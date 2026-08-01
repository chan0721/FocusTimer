"""
Central path resolution.

When running from source, all persistent files live in the project root.
When packaged with PyInstaller (--onefile), `__file__` points into a
temporary extraction folder that is DELETED on exit. Writing persistent
data there (database, user sounds) would be lost — so we resolve
persistent paths against the executable's own directory instead.

The packaged .exe is fully self-contained: on first run it seeds the
default ambient sounds from the bundle into <exe>/assets/sounds/ so the
user can see, replace, or delete them.
"""

import os
import shutil
import sys

# Ambient file extensions used when seeding the bundled sounds
_AUDIO_EXTS = (".mp3", ".wav", ".ogg", ".flac", ".m4a")


def is_frozen() -> bool:
    """True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def get_app_base_dir() -> str:
    """
    Persistent base directory:
      - directory of the .exe when packaged
      - project root when running from source
    """
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_db_path() -> str:
    """Path of the SQLite database file (persistent)."""
    return os.path.join(get_app_base_dir(), "focustimer.db")


def get_icon_path() -> str:
    """Path of the application icon (persistent)."""
    return os.path.join(get_app_base_dir(), "assets", "icon.ico")


def get_sounds_dir() -> str:
    """
    User-editable ambient sounds directory (<exe>/assets/sounds).

    When packaged, on first run this copies the bundled default sounds
    (brown noise, rain, etc.) into the persistent folder, so the .exe
    works standalone and the sounds remain visible/editable by the user.
    """
    user_dir = os.path.join(get_app_base_dir(), "assets", "sounds")

    # Already has user-visible ambient files → use it directly
    if _has_ambient_files(user_dir):
        return user_dir

    # Frozen: seed the user dir from the bundled copy
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        bundled = os.path.join(sys._MEIPASS, "assets", "sounds")
        if os.path.isdir(bundled):
            _seed_sounds(bundled, user_dir)

    return user_dir


def _has_ambient_files(directory: str) -> bool:
    """True if the directory contains any non-internal audio file."""
    try:
        for fname in os.listdir(directory):
            if not fname.startswith("__") and fname.lower().endswith(_AUDIO_EXTS):
                return True
    except FileNotFoundError:
        return False
    return False


def _seed_sounds(src_dir: str, dst_dir: str) -> None:
    """Copy bundled ambient audio files into the persistent sounds folder."""
    try:
        os.makedirs(dst_dir, exist_ok=True)
        for fname in os.listdir(src_dir):
            if fname.lower().endswith(_AUDIO_EXTS):
                src = os.path.join(src_dir, fname)
                dst = os.path.join(dst_dir, fname)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
    except OSError:
        pass  # folder may be read-only (e.g. Program Files) — app still works
