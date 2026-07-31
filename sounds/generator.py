"""
Minimal sound helpers — only the completion chime is generated.
Ambient sounds are user-provided .mp3/.wav files placed in assets/sounds/.
"""

import os
import wave
import numpy as np

from config.settings import AMBIENT_SOUNDS_DIR

# Project root-relative assets directory
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(_PROJECT_ROOT, AMBIENT_SOUNDS_DIR)


def _ensure_dir() -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)


def _normalize(samples: np.ndarray, ceiling: float = 0.95) -> np.ndarray:
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples / peak * ceiling
    return samples.astype(np.float32)


def _write_wav(filepath: str, samples: np.ndarray, sample_rate: int = 44100) -> None:
    samples = _normalize(samples)
    int_samples = (samples * 32767).astype(np.int16)
    _ensure_dir()
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())


def get_sound_path(sound_name: str) -> str:
    """Return the full path for a named asset (e.g. the completion chime)."""
    return os.path.join(ASSETS_DIR, f"{sound_name}.wav")


def generate_completion_chime(filepath: str) -> None:
    """Pleasant three-tone completion chime with gentle decay (~1 sec)."""
    sr = 44100
    n = sr
    t = np.linspace(0, 1, n, endpoint=False)
    f1, f2, f3 = 523.25, 659.25, 783.99  # C5, E5, G5
    tone1 = np.sin(2 * np.pi * f1 * t) * np.exp(-t * 4)
    tone2 = np.sin(2 * np.pi * f2 * t) * np.exp(-(t - 0.15) * 4)
    tone2[:int(0.15 * sr)] = 0
    tone3 = np.sin(2 * np.pi * f3 * t) * np.exp(-(t - 0.3) * 3)
    tone3[:int(0.3 * sr)] = 0
    samples = (tone1 * 0.35 + tone2 * 0.35 + tone3 * 0.3).astype(np.float32)
    _write_wav(filepath, samples, sr)


def scan_ambient_sounds() -> list[tuple[str, str]]:
    """
    Scan the ambient sounds directory for audio files.
    Returns a sorted list of (display_name, full_path) tuples.
    """
    from config.settings import AMBIENT_AUDIO_EXTS
    _ensure_dir()
    results = []
    try:
        for fname in sorted(os.listdir(ASSETS_DIR)):
            if fname.lower().endswith(AMBIENT_AUDIO_EXTS):
                full = os.path.join(ASSETS_DIR, fname)
                # Display name: filename without extension, underscores → spaces
                stem = os.path.splitext(fname)[0]
                display = stem.replace("_", " ").replace("-", " ").title()
                results.append((display, full))
    except FileNotFoundError:
        pass
    return results
