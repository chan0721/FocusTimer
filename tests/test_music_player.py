"""
Tests for the MusicPlayer class.

Run:  python tests/test_music_player.py

Works everywhere:
  - On Windows (where pygame is installed) it tests against the real mixer.
  - Headless/CI (no pygame available) it uses a faithful mock of the
    pygame.mixer API to validate the player's logic (selection, stale
    events, pause/resume state machine, navigation).
"""

import os
import sys
import tempfile
import wave

# Dummy SDL drivers so real pygame works headless too
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pygame.mixer
    import pygame
    HAVE_REAL_PYGAME = True
except ImportError:
    HAVE_REAL_PYGAME = False

if not HAVE_REAL_PYGAME:
    # ── Minimal pygame.mixer mock ──────────────────────────────────────
    class _MockError(Exception):
        pass

    class _MockEvent:
        def __init__(self, type_):
            self.type = type_

    class _MockSound:
        def __init__(self, path):
            import numpy as np
            with wave.open(path, "rb") as wf:
                self._seconds = wf.getnframes() / float(wf.getframerate())

        def get_length(self):
            return self._seconds

        def set_volume(self, vol):
            pass

        def play(self):
            pass

    class _MockChannel:
        def __init__(self, _id):
            self._id = _id
            self._sound = None
            self._busy = False
            self._paused = False
            self._volume = 1.0

        def play(self, sound, loops=0):
            self._sound = sound
            self._busy = True
            self._paused = False

        def stop(self):
            self._busy = False
            self._paused = False
            self._sound = None

        def pause(self):
            if self._busy:
                self._paused = True

        def unpause(self):
            self._paused = False

        def get_busy(self):
            return self._busy

        def get_sound(self):
            return self._sound

        def set_volume(self, vol):
            self._volume = vol

        def set_endevent(self, evt_type):
            self._end_event = evt_type

    class _MockMixer:
        def __init__(self):
            self._channels = [_MockChannel(i) for i in range(8)]
            self._init = False

        def get_init(self):
            return self._init

        def init(self, **kwargs):
            self._init = True

        def quit(self):
            self._init = False

        def get_busy(self):
            return any(c.get_busy() for c in self._channels)

        def Sound(self, path):
            return _MockSound(path)

        def Channel(self, i):
            return self._channels[i]

    _mock_mixer = _MockMixer()
    pygame = type(sys)("pygame")  # dummy module object
    pygame.USEREVENT = 24
    pygame.error = _MockError
    pygame.mixer = _mock_mixer
    pygame.event = type(sys)("pygame.event")

    class _EventQueue:
        def __init__(self):
            self._events = []

        def post(self, evt):
            self._events.append(evt)

        def get(self):
            evts, self._events = self._events, []
            return evts

        def clear(self, evt_type=None):
            if evt_type is None:
                self._events = []
            else:
                self._events = [e for e in self._events if e.type != evt_type]

    _event_queue = _EventQueue()
    pygame.event.post = _event_queue.post
    pygame.event.get = _event_queue.get
    pygame.event.clear = _event_queue.clear

    # pygame.init/quit — the mock mixer tracks its own state
    def _mock_pygame_init():
        _mock_mixer.init()

    def _mock_pygame_quit():
        _mock_mixer.quit()

    pygame.init = _mock_pygame_init
    pygame.quit = _mock_pygame_quit

    # Register fake pygame + pygame.mixer as real modules so that
    # "import pygame.mixer" inside core.music_player succeeds.
    sys.modules["pygame"] = pygame
    sys.modules["pygame.mixer"] = _mock_mixer

SR = 22050


def _make_wav(path: str, seconds: float, freq: float = 440.0) -> None:
    """Create a distinct tone of given duration (used to identify tracks)."""
    import numpy as np

    n = int(SR * seconds)
    t = np.linspace(0, seconds, n, endpoint=False)
    samples = (0.3 * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(samples.tobytes())


from core.music_player import MusicPlayer, MUSIC_CHANNEL


def _playing_duration(player: MusicPlayer) -> float:
    """Length of the sound currently on the music channel (0.0 if none)."""
    ch = pygame.mixer.Channel(MUSIC_CHANNEL)
    snd = ch.get_sound()
    return snd.get_length() if snd else 0.0


class TestMusicPlayer:
    def setup(self):
        # Full init: pygame.event functions (post/clear/get) require the
        # video subsystem, not just the mixer.
        pygame.init()
        pygame.mixer.quit()
        pygame.mixer.init(frequency=SR, size=-16, channels=2, buffer=512)
        # Distinct durations identify each track: A=0.5s, B=1.0s, C=1.5s
        self.tmp = tempfile.mkdtemp()
        self.tracks = {
            "A": os.path.join(self.tmp, "A.wav"),
            "B": os.path.join(self.tmp, "B.wav"),
            "C": os.path.join(self.tmp, "C.wav"),
        }
        _make_wav(self.tracks["A"], 0.5, 440)
        _make_wav(self.tracks["B"], 1.0, 554)
        _make_wav(self.tracks["C"], 1.5, 659)
        self.paths = [self.tracks["A"], self.tracks["B"], self.tracks["C"]]
        self.player = MusicPlayer()
        self.player.load_playlist(self.paths)

    def teardown(self):
        self.player.shutdown()
        pygame.quit()

    # ── 1. Selecting a track plays THAT track ──────────────────────────
    def test_play_selected_track(self):
        self.player.play_music(0)
        assert _playing_duration(self.player) == 0.5, "expected track A"
        assert self.player.current_track_index == 0

        self.player.play_music(1)
        assert _playing_duration(self.player) == 1.0, "expected track B"
        assert self.player.current_track_index == 1

        self.player.play_music(2)
        assert _playing_duration(self.player) == 1.5, "expected track C"
        assert self.player.current_track_index == 2

    # ── 2. Selection is never skipped after a manual change ────────────
    def test_selection_not_skipped_after_manual_change(self):
        # Track A ends (channel not busy), but the user selects B before
        # the poller runs. The poll must NOT advance past the selection.
        self.player.play_music(0)
        pygame.mixer.Channel(MUSIC_CHANNEL).stop()  # simulate "A finished"
        self.player.play_music(1)                   # user picks B

        self.player.poll()  # poller runs next tick

        assert self.player.current_track_index == 1, "poll skipped selection!"
        assert _playing_duration(self.player) == 1.0, "wrong track playing"

    # ── 3. Pause → select another track → plays normally (not stuck) ───
    def test_pause_then_switch_track(self):
        self.player.play_music(0)
        assert self.player.is_music_playing

        self.player.pause_music()
        assert self.player.is_music_paused, "should be paused"
        # Note: get_busy() stays True while paused (sound still loaded)

        # Switch to another track while paused → must play normally
        self.player.play_music(2)
        assert not self.player.is_music_paused, "channel stuck paused!"
        assert self.player.is_music_playing, "channel stuck, not busy!"
        assert _playing_duration(self.player) == 1.5, "wrong track after switch"

    # ── 4. Pause → resume keeps the same track ─────────────────────────
    def test_pause_resume_same_track(self):
        self.player.play_music(1)
        self.player.pause_music()
        self.player.resume_music()
        assert self.player.is_music_playing
        assert not self.player.is_music_paused
        assert self.player.current_track_index == 1

    # ── 5. Play button cycle: play → pause → resume → pause ───────────
    def test_play_pause_cycle(self):
        self.player.play_music(0)
        self.player.pause_music()
        assert self.player.is_music_paused

        # play button → resume
        self.player.resume_music()
        assert self.player.is_music_playing
        assert not self.player.is_music_paused

        # play button → pause again
        self.player.pause_music()
        assert self.player.is_music_paused

    # ── 6. Next / previous navigation ──────────────────────────────────
    def test_next_prev(self):
        self.player.play_music(0)
        self.player.next_track()
        assert self.player.current_track_index == 1
        self.player.next_track()
        assert self.player.current_track_index == 2
        # wraps around
        self.player.next_track()
        assert self.player.current_track_index == 0
        self.player.prev_track()
        assert self.player.current_track_index == 2

    # ── 7. Repeat mode replays the same track ──────────────────────────
    def test_repeat_replays_same_track(self):
        self.player.play_music(0)
        self.player.repeat = True
        self.player.next_track()  # repeat → same index
        assert self.player.current_track_index == 0
        assert _playing_duration(self.player) == 0.5

    # ── 8. Stop clears playback ────────────────────────────────────────
    def test_stop_clears(self):
        self.player.play_music(1)
        assert self.player.is_music_playing
        self.player.stop_music()
        assert not self.player.is_music_playing
        assert not self.player.is_music_paused

    # ── 9. Poll detects natural track end and advances ─────────────────
    def test_poll_detects_track_end(self):
        self.player.play_music(0)
        # Simulate the track finishing: channel becomes not busy on its own
        pygame.mixer.Channel(MUSIC_CHANNEL).stop()
        self.player.poll()
        assert self.player.current_track_index == 1, "poll should advance"

    # ── 10. Poll does NOT advance while the track is playing ───────────
    def test_poll_no_advance_while_playing(self):
        self.player.play_music(0)
        self.player.poll()
        assert self.player.current_track_index == 0, "poll must not skip"

    # ── 11. Poll does NOT advance while paused ─────────────────────────
    def test_poll_no_advance_while_paused(self):
        self.player.play_music(0)
        self.player.pause_music()
        pygame.mixer.Channel(MUSIC_CHANNEL).stop()  # channel goes idle
        self.player.poll()
        assert self.player.current_track_index == 0, "paused track must not advance"

    # ── 12. Batch removal keeps playlist consistent ────────────────────
    def test_batch_remove(self):
        self.player.play_music(1)  # B currently playing (index 1)
        # Remove A(0) and C(2) in one call — B should stay and be current
        self.player.remove_from_playlist([0, 2])
        assert self.player.playlist == [self.tracks["B"]], "wrong playlist left"
        assert self.player.current_track_index == 0, "current index wrong"

    # ── 13. Removing the currently playing track stops playback ────────
    def test_remove_current_track_stops(self):
        self.player.play_music(2)  # C playing
        self.player.remove_from_playlist([2])
        assert self.player.current_track_index == -1, "index should reset"
        assert not self.player.is_music_playing, "playback should stop"


def main():
    t = TestMusicPlayer()
    methods = [m for m in dir(t) if m.startswith("test_")]
    passed = 0
    mode = "REAL pygame" if HAVE_REAL_PYGAME else "MOCK pygame"
    print(f"Running {len(methods)} tests against {mode}")
    for name in methods:
        try:
            t.setup()
            getattr(t, name)()
            passed += 1
            print(f"  PASS  {name}")
        except AssertionError as exc:
            print(f"  FAIL  {name}: {exc}")
        except Exception as exc:
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
        finally:
            try:
                t.teardown()
            except Exception:
                pass

    print(f"\n{passed}/{len(methods)} tests passed")
    return 0 if passed == len(methods) else 1


if __name__ == "__main__":
    sys.exit(main())
