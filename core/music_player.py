"""
Audio playback engine wrapping pygame.mixer.
Handles music (MP3/FLAC/WAV/etc.) and ambient sound loops with independent volume.
"""

import os
import random
from typing import Optional

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

        # Track which ambient sound is playing on each channel: channel → sound_name
        self._ambient_active: dict[int, str] = {}
        # Per-sound volume levels (0.0 - 1.0)
        self._ambient_volumes: dict[str, float] = {}

        # Set up channel end-of-track callback
        pygame.mixer.Channel(MUSIC_CHANNEL).set_endevent(
            pygame.USEREVENT + 1
        )

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

    def remove_from_playlist(self, index: int) -> None:
        if 0 <= index < len(self._playlist):
            was_current = index == self._playlist_index
            self._playlist.pop(index)
            if was_current:
                self.stop_music()
            elif index < self._playlist_index:
                self._playlist_index -= 1

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
        """Start playing from the given playlist index, or resume current."""
        music_ch = pygame.mixer.Channel(MUSIC_CHANNEL)

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
            return

        try:
            sound = pygame.mixer.Sound(self._playlist[self._playlist_index])
            music_ch.play(sound, loops=0)
            music_ch.set_volume(self._music_volume)
        except pygame.error as exc:
            print(f"MusicPlayer: cannot play {self._playlist[self._playlist_index]}: {exc}")
            self._advance_track()

    def pause_music(self) -> None:
        pygame.mixer.Channel(MUSIC_CHANNEL).pause()

    def resume_music(self) -> None:
        music_ch = pygame.mixer.Channel(MUSIC_CHANNEL)
        if not music_ch.get_busy():
            # If nothing is loaded, start from the current track
            if self._playlist_index >= 0:
                self.play_music()
        else:
            music_ch.unpause()

    def stop_music(self) -> None:
        pygame.mixer.Channel(MUSIC_CHANNEL).stop()

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
            return
        if self._repeat:
            # Replay the same track
            self.play_music()
            return
        if self._shuffle:
            self._playlist_index = random.randint(0, len(self._playlist) - 1)
        else:
            self._playlist_index = (self._playlist_index + 1) % len(self._playlist)
        self.play_music()

    @property
    def is_music_playing(self) -> bool:
        return pygame.mixer.Channel(MUSIC_CHANNEL).get_busy()

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

    # ── Check for track-end events (call from main event loop) ────────

    def process_events(self, event) -> bool:
        """Handle pygame music-end events. Returns True if event was consumed."""
        if event.type == pygame.USEREVENT + 1:
            self._advance_track()
            return True
        return False

    # ── Cleanup ────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        self.stop_music()
        self.stop_all_ambient()
