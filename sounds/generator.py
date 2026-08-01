"""
Minimal sound helpers — only the completion chime is generated.
Ambient sounds are .mp3/.wav files scanned from assets/sounds/.
Paths are resolved via config.paths so data persists next to the .exe.
"""

import os
import wave
import numpy as np

from config.paths import get_app_base_dir, get_sounds_dir


def _get_write_dir() -> str:
    """Persistent directory for generated assets (never the bundled temp copy)."""
    return os.path.join(get_app_base_dir(), "assets", "sounds")


def _ensure_dir() -> None:
    os.makedirs(_get_write_dir(), exist_ok=True)


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
    """Persistent path for a generated asset (e.g. the completion chime)."""
    return os.path.join(_get_write_dir(), f"{sound_name}.wav")


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
    Files starting with '__' (internal assets, e.g. the completion chime)
    are excluded. Uses config.paths.get_sounds_dir(), which handles the
    bundled-to-persistent seeding for packaged builds.
    """
    from config.settings import AMBIENT_AUDIO_EXTS

    results = []
    scan_dir = get_sounds_dir()
    try:
        for fname in sorted(os.listdir(scan_dir)):
            if fname.startswith("__"):
                continue  # internal file
            if fname.lower().endswith(AMBIENT_AUDIO_EXTS):
                full = os.path.join(scan_dir, fname)
                stem = os.path.splitext(fname)[0]
                display = stem.replace("_", " ").replace("-", " ").title()
                results.append((display, full))
    except FileNotFoundError:
        pass
    return results
