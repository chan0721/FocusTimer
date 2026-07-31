# FocusTimer

A minimalist Windows desktop focus timer for deep work and daily study habits — Pomodoro cycles, statistics dashboard, session history, inspirational quotes, music player, and ambient sound mixer. Fully offline.

<p align="center">
  <em>Clean. Calm. Distraction-free.</em>
</p>

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Installation (from source)](#installation-from-source)
- [How to Use](#how-to-use)
  - [Timer Page](#timer-page)
  - [Statistics Page](#statistics-page)
  - [History Page](#history-page)
  - [Quotes Page](#quotes-page)
  - [Music & Ambient Page](#music--ambient-page)
  - [Settings Page](#settings-page)
- [Adding Your Own Ambient Sounds](#adding-your-own-ambient-sounds)
- [Packaging as a Windows .exe](#packaging-as-a-windows-exe)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [AI Usage Disclosure](#ai-usage-disclosure)
- [License](#license)

---

## Features

| Feature | Description |
|---|---|
| **Focus Timer** | Preset durations (25 / 50 / 90 / 120 / 180 min) plus a custom spinbox (1–600 min). Start, pause, resume, reset. |
| **Pomodoro Mode** | Toggleable. Configurable focus duration, break duration, and number of cycles. Auto-transitions between phases. |
| **Daily Goal** | Set a daily focus target (30 min – 12 h). A progress bar on the timer page tracks today's progress. |
| **Statistics** | Bar chart of daily focus time, weekly average, session count, and a GitHub-style calendar heatmap. |
| **Session History** | Every completed session is logged with date, time, duration, and task description. Filter by date range and search by keyword. |
| **Quotes** | 20 built-in inspirational quotes. Add, edit, and delete your own. Displayed on the timer page during sessions. |
| **Music Player** | Play local `.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg` files. Browse folders, build playlists, shuffle, repeat, volume control. |
| **Ambient Sound Mixer** | Place your own ambient audio files in `assets/sounds/` — they appear as checkboxes with independent volume sliders. Mix multiple sounds simultaneously (up to 7). |
| **Light & Dark Themes** | Switch in Settings (restart required). |
| **Fully Offline** | No internet connection needed. No accounts, no telemetry. |

---

## Screenshots

```
 ┌─────────────────────────────────────────────────────────┐
 │  ⏱  Timer          │                                    │
 │  📊  Statistics     │           ┌──────────────┐         │
 │  📋  History        │           │   01:23:45   │         │
 │  💬  Quotes         │           └──────────────┘         │
 │  🎵  Music          │                                    │
 │  ⚙  Settings        │  "The journey of a thousand       │
 │                     │   miles begins with one step."    │
 │                     │               — Lao Tzu           │
 │                     │                                    │
 │                     │  ████████░░░░  2.5 / 4 hours      │
 │                     │                                    │
 │                     │  Current task: [______________]    │
 │                     │  Focus time:   [90 min ▼] [90 min] │
 │                     │                                    │
 │                     │  ┌ Pomodoro Mode ─────────────┐   │
 │                     │  │ ☑ Enable Pomodoro          │   │
 │                     │  │ Focus: [25 min] Cycles: [4]│   │
 │                     │  │ Break: [ 5 min]            │   │
 │                     │  └────────────────────────────┘   │
 │                     │                                    │
 │                     │         ┌──────────────┐          │
 │                     │         │  START FOCUS  │          │
 │                     │         └──────────────┘          │
 └─────────────────────────────────────────────────────────┘
```

---

## Installation (from source)

### Prerequisites

- **Python 3.10 or later**
- **Windows** (primary target; also runs on Linux/macOS)
- Git (optional, for cloning)

### Step-by-step

```powershell
# 1. Clone the repository
git clone https://github.com/chan0721/FocusTimer.git
cd FocusTimer

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

On first launch the app creates:

- `focustimer.db` — SQLite database (session history, settings, quotes, playlists)
- `assets/sounds/__completion_chime.wav` — notification sound played when a session ends

---

## How to Use

### Timer Page

The main screen. This is where you start focus sessions.

1. **Choose a duration** — use the dropdown for a preset (25 / 50 / 90 / 120 / 180 min) or type a custom value in the spinbox.
2. **Enter a task description** (optional) — helps you remember what you worked on when reviewing history later.
3. **Enable Pomodoro** (optional) — check the box and configure focus/break durations and the number of cycles.
4. **Click "START FOCUS"** — the countdown begins. While running you can pause or reset.
5. **When the timer ends** — a chime plays and the session is saved to history automatically. If Pomodoro is enabled, it auto-transitions to the break phase.

The **progress bar** at the top shows today's completed time vs. your daily goal (set in Settings).

An **inspirational quote** is displayed during each session. Quotes change per session by default (configurable in Settings).

### Statistics Page

Shows your focus data over time:

- **Summary cards** — today's focus time, session count, goal completion %, and weekly daily average.
- **Bar chart** — daily focus hours for the selected period (7 / 30 / 90 days).
- **Calendar heatmap** — a GitHub-contribution-style grid showing the last ~4 months, color-coded by daily focus time.

### History Page

A log of every completed (or abandoned) focus session:

- **Date range filter** — pick start and end dates, then click "Filter".
- **Text search** — type in the search bar to filter by task description.
- **Delete** — select rows and click "Delete Selected" to remove them.

### Quotes Page

Manage inspirational quotes that appear on the timer page:

- **20 built-in quotes** — shown with a "Built-in" tag. These cannot be edited or deleted.
- **Add your own** — click "+ Add Quote", enter text and author, then save.
- **Edit / Delete** — select a user-created quote and use the buttons at the bottom.

### Music & Ambient Page

**Left side — Music Player:**

- **Add music** — click "Add Folder..." to scan a directory, or "Add Files..." to pick individual tracks.
- **Playlist** — double-click a track to play. Use the transport buttons (previous, play, pause, stop, next).
- **Shuffle / Repeat** — toggle checkboxes.
- **Volume** — slider from 0% to 100%.

**Right side — Ambient Sounds:**

- Place `.mp3` / `.wav` / `.ogg` files in `assets/sounds/` (see [Adding Your Own Ambient Sounds](#adding-your-own-ambient-sounds)).
- Click **Refresh** to scan the folder for new or removed files.
- Check the box next to a sound to start playing it. Uncheck to stop.
- Each sound has its own **volume slider**.
- You can mix up to 7 ambient sounds simultaneously (e.g., rain + fireplace + coffee shop).

### Settings Page

Configure defaults that apply to new sessions:

| Section | Options |
|---|---|
| **Timer Defaults** | Default focus duration, default break duration, Pomodoro cycle count, daily goal |
| **Appearance** | Light or Dark theme (requires restart) |
| **Quotes** | Quote change frequency: per session, per break, or daily |
| **Audio Defaults** | Default music volume, default ambient volume |
| **Startup** | Which page to show when the app launches |

Click **Save Settings** to persist changes.

---

## Adding Your Own Ambient Sounds

1. Download ambient audio files from any source (`.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`).
2. Place them in:

   ```
   FocusTimer/assets/sounds/
   ```

3. In the app, go to the **Music** tab and click **Refresh**.

The filename (without extension) becomes the display name. Underscores and dashes are converted to spaces:

```
rain.mp3          →  Rain
ocean_waves.wav   →  Ocean Waves
coffee-shop.ogg   →  Coffee Shop
```

To remove a sound, delete the file from the folder and click Refresh.

---

## Packaging as a Windows .exe

A PyInstaller spec file is included (`FocusTimer.spec`).

### 1. Install PyInstaller

```powershell
pip install pyinstaller
```

### 2. Generate the icon (if missing)

```powershell
python build_icon.py
```

### 3. Build

```powershell
pyinstaller FocusTimer.spec
```

The output is at `dist/FocusTimer.exe` (~150 MB due to bundled Qt libraries).

### What the spec does

- `--onefile` — single executable
- `--windowed` — no console window
- `--icon assets/icon.ico` — custom application icon
- Embeds all Python modules, Qt binaries, and `assets/` directory

---

## Project Structure

```
FocusTimer/
├── main.py                     # Entry point — initializes pygame, launches the Qt app
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── FocusTimer.spec             # PyInstaller spec for building .exe
├── build_icon.py               # Script to generate assets/icon.ico
│
├── config/
│   └── settings.py             # App constants, defaults, built-in quotes
│
├── database/
│   └── database.py             # SQLite layer — sessions, goals, quotes, settings, playlists
│
├── core/
│   ├── timer.py                # Countdown engine with Pomodoro state machine
│   └── music_player.py         # pygame.mixer wrapper — music + multi-channel ambient
│
├── sounds/
│   └── generator.py            # Completion chime generator + ambient folder scanner
│
├── ui/
│   ├── main_window.py          # Main window — sidebar navigation + stacked pages
│   ├── timer_widget.py         # Timer page — countdown, Pomodoro, quotes, progress
│   ├── statistics_widget.py    # Statistics page — bar chart + calendar heatmap
│   ├── history_widget.py       # History page — session table with search/filter
│   ├── quotes_widget.py        # Quotes page — add/edit/delete quotes
│   ├── music_widget.py         # Music page — player + ambient mixer
│   ├── settings_widget.py      # Settings page — all user preferences
│   └── styles.py               # Light & dark QSS stylesheets
│
├── assets/
│   ├── icon.ico                # Application icon (16/32/48/256 px)
│   └── sounds/                 # Place your ambient .mp3/.wav files here
│       └── README.txt          # Instructions for the sounds folder
│
└── music/
    └── default_sounds/         # Reserved for future built-in sounds
```

---

## Technology Stack

| Component | Technology |
|---|---|
| GUI framework | PyQt6 |
| Audio playback | pygame (mixer) |
| Charts & heatmap | matplotlib (embedded via FigureCanvasQTAgg) |
| Database | SQLite (Python stdlib `sqlite3`) |
| Sound generation | numpy |
| Packaging | PyInstaller |

---

## AI Usage Disclosure

This project was developed with assistance from **DeepSeek** (deepseek-v4-pro), an AI language model, acting as an interactive coding assistant. The AI contributed to:

- Generating the initial project structure and all source files based on a detailed requirements document
- Implementing the core timer logic, database schema, and UI components
- Writing the procedural ambient sound generator (later replaced with user-provided file support)
- Iterative debugging and refinement through conversation (Pomodoro timing fix, settings layout alignment, pygame initialization, etc.)

All design decisions, feature specifications, and final review were directed by the human user. The AI served as a pair-programming tool — writing code, explaining choices, and applying feedback — but did not autonomously determine the project's goals or scope.

---

## License

This project is provided for personal use. The built-in inspirational quotes are sourced from public domain and commonly attributed works. The completion chime and icon are procedurally generated.
