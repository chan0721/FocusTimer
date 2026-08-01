"""
Audio playback engine wrapping pygame.mixer.

Design notes (important for reliability):
  * Track end is detected by POLLING the channel state (Channel.get_busy)
    instead of pygame events. Pygame end-of-track events were unreliable:
    stale events could advance past the user's selection, and multiple
    queued events caused tracks to be skipped.
  * The currently playing Sound is kept in a strong reference
    (self._current_sound) so pygame never drops the audio mid-play.
  * The paused state is tracked internally (pygame has no
    Channel.get_paused()).
"""

import os
import random

import pygame.mixer

from config.settings import DEFAULT_MUSIC_VOLUME, DEFAULT_AMBIENT_VOLUME


# Reserve channels: 0 = music, 1-7 = ambient sounds
MUSIC_CHANNEL = 0
AMBIENT_CHANNELS = list(range(1, 8))
MAX_AMBIENT_SOUNDS = len(AMBIENT_CHANNELS)


class MusicPlayer:
    """Wraps pygame.mixer for music playback and ambient sound mixing."""

    def __init__(self):
        # pygame.mixer is initialised once in main.py; ensure it's ready
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        self._music_volume = DEFAULT_MUSIC_VOLUME / 100.0
        self._ambient_volume = DEFAULT_AMBIENT_VOLUME / 100.0

        self._playlist: list[str] = []       # list of file paths
        self._playlist_index = -1
        self._repeat = False
        self._shuffle = False

        self._music_paused = False   # our own pause-state tracking
        self._expect_playing = False # True between play() and natural end
        self._current_sound = None   # strong reference to the playing Sound

        # Track which ambient sound is playing on each channel: channel → sound_name
        self._ambient_active: dict[int, str] = {}
        # Per-sound volume levels (0.0 - 1.0)
        self._ambient_volumes: dict[str, float] = {}

    # ── Music playback ────────────────────────────────────────────────

    def load_playlist(self, file_paths: list[str]) -> None:
        """Replace the current playlist with a list of audio file paths."""
        self.stop_music()
        self._playlist = [p for p in file_paths if os.path.isfile(p)]
        self._playlist_index = -1

    def add_to_playlist(self, file_paths: list[str]) -> None:
        """Append tracks to the existing playlist."""
        for p in file_paths:
            if os.path.isfile(p) and p not in self._playlist:
                self._playlist.append(p)

    def remove_from_playlist(self, indexes: list[int]) -> None:
        """
        Remove tracks by a (possibly unsorted) list of playlist indexes.
        Handles the currently playing track and adjusts the index correctly.
        """
        if not indexes:
            return
        indexes = sorted(set(indexes), reverse=True)
        current = self._playlist_index
        removed_current = False

        for idx in indexes:
            if not (0 <= idx < len(self._playlist)):
                continue
            if idx == current:
                removed_current = True
            elif idx < current:
                current -= 1
            self._playlist.pop(idx)

        if removed_current:
            self.stop_music()
            self._playlist_index = -1
        else:
            self._playlist_index = current

    @property
    def playlist(self) -> list[str]:
        return list(self._playlist)

    @property
    def current_track_index(self) -> int:
        return self._playlist_index

    @property
    def current_track_name(self) -> str:
        if 0 <= self._playlist_index < len(self._playlist):
            return os.path.splitext(
                os.path.basename(self._playlist[self._playlist_index])
            )[0]
        return ""

    def play_music(self, index: int | None = None) -> None:
        """
        Start playing the track at `index` (or the current track if None).
        Corrupt/unplayable files are skipped automatically.
        """
        if index is not None:
            if 0 <= index < len(self._playlist):
                self._playlist_index = index
            else:
                return

        if self._playlist_index < 0 and self._playlist:
            if self._shuffle:
                self._playlist_index = random.randint(0, len(self._playlist) - 1)
            else:
                self._playlist_index = 0

        if self._playlist_index < 0 or self._playlist_index >= len(self._playlist):
            self._expect_playing = False
            return

        self._try_play_current(allow_skip=True)

    def _try_play_current(self, allow_skip: bool = False, depth: int = 0) -> None:
        """Load and play the track at _playlist_index; skip broken files."""
        if depth > len(self._playlist):  # playlist fully unplayable — give up
            self._expect_playing = False
            self._current_sound = None
            return

        ch = pygame.mixer.Channel(MUSIC_CHANNEL)
        try:
            sound = pygame.mixer.Sound(self._playlist[self._playlist_index])
        except pygame.error as exc:
            print(f"MusicPlayer: cannot load "
                  f"{self._playlist[self._playlist_index]}: {exc}")
            if allow_skip:
                self._playlist_index = (
                    self._playlist_index + 1) % len(self._playlist)
                self._try_play_current(allow_skip=True, depth=depth + 1)
            else:
                self._expect_playing = False
            return

        # Keep a strong reference so pygame does not drop the sound mid-play
        self._current_sound = sound
        # stop() fully resets the channel (clears paused state),
        # then play; unpause() as a safety net.
        ch.stop()
        ch.play(sound, loops=0)
        ch.unpause()
        ch.set_volume(self._music_volume)
        self._music_paused = False
        self._expect_playing = True

    def pause_music(self) -> None:
        pygame.mixer.Channel(MUSIC_CHANNEL).pause()
        self._music_paused = True

    def resume_music(self) -> None:
        if self._music_paused:
            pygame.mixer.Channel(MUSIC_CHANNEL).unpause()
            self._music_paused = False
            return
        # Not paused but stopped — start the current track over
        if not pygame.mixer.Channel(MUSIC_CHANNEL).get_busy():
            if self._playlist_index >= 0:
                self.play_music()

    def stop_music(self) -> None:
        pygame.mixer.Channel(MUSIC_CHANNEL).stop()
        self._music_paused = False
        self._expect_playing = False
        self._current_sound = None

    def next_track(self) -> None:
        self._advance_track()

    def prev_track(self) -> None:
        if not self._playlist:
            return
        if self._shuffle:
            self._playlist_index = random.randint(0, len(self._playlist) - 1)
        else:
            self._playlist_index = (self._playlist_index - 1) % len(self._playlist)
        self.play_music()

    def _advance_track(self) -> None:
        """Move to the next track based on repeat/shuffle settings."""
        if not self._playlist:
            self._expect_playing = False
            return
        if self._repeat:
            self.play_music()  # replay the same track
            return
        if self._shuffle:
            self._playlist_index = random.randint(0, len(self._playlist) - 1)
        else:
            self._playlist_index = (self._playlist_index + 1) % len(self._playlist)
        self.play_music()

    def poll(self) -> None:
        """
        Call periodically from the UI event loop (e.g. every 200 ms).
        Detects when the current track has ended naturally and advances.
        Replaces the old (unreliable) pygame end-of-track event mechanism.
        """
        if self._music_paused or not self._expect_playing:
            return
        if not pygame.mixer.Channel(MUSIC_CHANNEL).get_busy():
            self._expect_playing = False
            self._advance_track()

    @property
    def is_music_playing(self) -> bool:
        """True if a track is loaded on the channel and audible."""
        return pygame.mixer.Channel(MUSIC_CHANNEL).get_busy() and not self._music_paused

    @property
    def is_music_paused(self) -> bool:
        """True if a track is loaded but paused."""
        return self._music_paused

    @property
    def repeat(self) -> bool:
        return self._repeat

    @repeat.setter
    def repeat(self, value: bool) -> None:
        self._repeat = value

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    @shuffle.setter
    def shuffle(self, value: bool) -> None:
        self._shuffle = value

    @property
    def music_volume(self) -> float:
        return self._music_volume

    @music_volume.setter
    def music_volume(self, value: float) -> None:
        """Set volume as 0.0–1.0."""
        self._music_volume = max(0.0, min(1.0, value))
        ch = pygame.mixer.Channel(MUSIC_CHANNEL)
        if ch.get_busy():
            ch.set_volume(self._music_volume)

    # ── Ambient sounds ────────────────────────────────────────────────

    def play_ambient(self, sound_name: str, filepath: str, volume: float | None = None) -> None:
        """Start looping an ambient sound on a free channel."""
        if not os.path.isfile(filepath):
            return
        # Find a free channel
        free_channel = None
        for ch_idx in AMBIENT_CHANNELS:
            if not pygame.mixer.Channel(ch_idx).get_busy():
                free_channel = ch_idx
                break
        if free_channel is None:
            return  # all channels busy

        try:
            sound = pygame.mixer.Sound(filepath)
            ch = pygame.mixer.Channel(free_channel)
            ch.play(sound, loops=-1)  # loop indefinitely
            vol = volume if volume is not None else self._ambient_volume
            ch.set_volume(vol)
            self._ambient_active[free_channel] = sound_name
            self._ambient_volumes[sound_name] = vol
        except pygame.error as exc:
            print(f"MusicPlayer: cannot play ambient '{sound_name}': {exc}")

    def stop_ambient(self, sound_name: str) -> None:
        """Stop a specific ambient sound."""
        for ch_idx, name in list(self._ambient_active.items()):
            if name == sound_name:
                pygame.mixer.Channel(ch_idx).stop()
                del self._ambient_active[ch_idx]
                self._ambient_volumes.pop(sound_name, None)
                break

    def stop_all_ambient(self) -> None:
        for ch_idx in list(self._ambient_active.keys()):
            pygame.mixer.Channel(ch_idx).stop()
        self._ambient_active.clear()
        self._ambient_volumes.clear()

    def set_ambient_volume(self, sound_name: str, volume: float) -> None:
        """Set volume for a specific ambient sound (0.0–1.0)."""
        vol = max(0.0, min(1.0, volume))
        self._ambient_volumes[sound_name] = vol
        for ch_idx, name in self._ambient_active.items():
            if name == sound_name:
                pygame.mixer.Channel(ch_idx).set_volume(vol)

    def set_ambient_volume_global(self, volume: float) -> None:
        """Set all ambient channels to the same volume."""
        self._ambient_volume = max(0.0, min(1.0, volume))
        for ch_idx in self._ambient_active:
            pygame.mixer.Channel(ch_idx).set_volume(self._ambient_volume)
            name = self._ambient_active[ch_idx]
            self._ambient_volumes[name] = self._ambient_volume

    @property
    def ambient_volume(self) -> float:
        return self._ambient_volume

    @property
    def active_ambient_sounds(self) -> list[str]:
        return list(self._ambient_active.values())

    def is_ambient_playing(self, sound_name: str) -> bool:
        return sound_name in self._ambient_active.values()

    # ── Cleanup ────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        self.stop_music()
        self.stop_all_ambient()
