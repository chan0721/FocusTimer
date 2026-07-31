"""
Default application settings and constants.
Settings are overridden by values stored in the SQLite database at runtime.
"""

# ── Application metadata ──────────────────────────────────────────────
APP_NAME = "FocusTimer"
APP_VERSION = "1.0.0"
APP_AUTHOR = "FocusTimer"

# ── Timer defaults ────────────────────────────────────────────────────
DEFAULT_FOCUS_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5
DEFAULT_POMODORO_CYCLES = 4
FOCUS_PRESETS = [25, 50, 90]  # minutes

# ── Daily goal default ────────────────────────────────────────────────
DEFAULT_DAILY_GOAL_MINUTES = 240  # 4 hours

# ── Audio defaults ────────────────────────────────────────────────────
DEFAULT_MUSIC_VOLUME = 40
DEFAULT_AMBIENT_VOLUME = 30

# Folder scanned for .mp3/.wav/.ogg/.flac/.m4a ambient sound files.
# Place your own files here; names appear as checkboxes in the Music tab.
AMBIENT_SOUNDS_DIR = "assets/sounds"
AMBIENT_AUDIO_EXTS = (".mp3", ".wav", ".ogg", ".flac", ".m4a")

# ── Quote defaults ────────────────────────────────────────────────────
QUOTE_CHANGE_FREQUENCY = "per_session"  # per_session | per_break | daily

# Built-in inspirational quotes (science & learning themed)
BUILTIN_QUOTES = [
    ("The important thing is not to stop questioning. "
     "Curiosity has its own reason for existing.",
     "Albert Einstein"),
    ("The journey of a thousand miles begins with one step.",
     "Lao Tzu"),
    ("Success is not final, failure is not fatal: "
     "it is the courage to continue that counts.",
     "Winston Churchill"),
    ("It does not matter how slowly you go as long as you do not stop.",
     "Confucius"),
    ("The only way to do great work is to love what you do.",
     "Steve Jobs"),
    ("Education is the most powerful weapon which you can use "
     "to change the world.",
     "Nelson Mandela"),
    ("Live as if you were to die tomorrow. "
     "Learn as if you were to live forever.",
     "Mahatma Gandhi"),
    ("The beautiful thing about learning is that nobody can "
     "take it away from you.",
     "B.B. King"),
    ("Tell me and I forget. Teach me and I remember. "
     "Involve me and I learn.",
     "Benjamin Franklin"),
    ("An investment in knowledge pays the best interest.",
     "Benjamin Franklin"),
    ("The mind is not a vessel to be filled, but a fire to be kindled.",
     "Plutarch"),
    ("Wisdom is not a product of schooling but of the lifelong "
     "attempt to acquire it.",
     "Albert Einstein"),
    ("Study hard what interests you the most in the most "
     "undisciplined, irreverent and original manner possible.",
     "Richard Feynman"),
    ("What we know is a drop, what we don't know is an ocean.",
     "Isaac Newton"),
    ("The only true wisdom is in knowing you know nothing.",
     "Socrates"),
    ("Imagination is more important than knowledge.",
     "Albert Einstein"),
    ("I have not failed. I've just found 10,000 ways that won't work.",
     "Thomas Edison"),
    ("Whether you think you can or you think you can't, you're right.",
     "Henry Ford"),
    ("It is during our darkest moments that we must focus to see the light.",
     "Aristotle"),
    ("The future belongs to those who believe in the beauty of their dreams.",
     "Eleanor Roosevelt"),
]

# ── UI ─────────────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 680
WINDOW_DEFAULT_WIDTH = 1100
WINDOW_DEFAULT_HEIGHT = 750
SIDEBAR_WIDTH = 180

# ── Theme ─────────────────────────────────────────────────────────────
DEFAULT_THEME = "light"
