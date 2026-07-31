"""
Music & Ambient Sound page — music player, playlist management, ambient mixer.
Ambient sounds are user-provided .mp3/.wav files placed in assets/sounds/.
"""

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QSlider, QCheckBox, QGroupBox, QGridLayout,
    QFileDialog, QMessageBox, QLineEdit, QScrollArea,
)
from PyQt6.QtCore import Qt

from config.settings import AMBIENT_SOUNDS_DIR
from core.music_player import MusicPlayer
from database.database import Database
from sounds.generator import scan_ambient_sounds


class MusicWidget(QWidget):
    """Music player and ambient sound mixer page."""

    def __init__(self, music_player: MusicPlayer, db: Database, parent=None):
        super().__init__(parent)
        self._player = music_player
        self._db = db
        self._playlist_id: int | None = None

        # Ambient state: key -> (display_name, file_path)
        # key is the filename stem (unique identifier)
        self._ambient_checks: dict[str, QCheckBox] = {}
        self._ambient_sliders: dict[str, QSlider] = {}
        self._ambient_labels: dict[str, QLabel] = {}
        self._ambient_paths: dict[str, str] = {}

        self._init_ui()
        self._load_saved_state()
        self._refresh_ambient_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # ── LEFT: Music Player ────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(12)

        title = QLabel("Music Player")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        left.addWidget(title)

        # Now playing
        self._now_playing = QLabel("No track playing")
        self._now_playing.setStyleSheet("color: #6c757d; font-size: 13px;")
        left.addWidget(self._now_playing)

        # Playlist
        left.addWidget(QLabel("Playlist:"))
        self._playlist_widget = QListWidget()
        self._playlist_widget.setMaximumHeight(200)
        self._playlist_widget.doubleClicked.connect(self._on_playlist_double_click)
        left.addWidget(self._playlist_widget)

        # Music controls
        ctrl_row = QHBoxLayout()
        self._prev_btn = QPushButton("\u23ee")  # ⏮
        self._prev_btn.setToolTip("Previous")
        self._prev_btn.clicked.connect(self._player.prev_track)
        ctrl_row.addWidget(self._prev_btn)

        self._play_btn = QPushButton("\u25b6")  # ▶
        self._play_btn.setToolTip("Play")
        self._play_btn.clicked.connect(self._on_play_clicked)
        ctrl_row.addWidget(self._play_btn)

        self._pause_btn = QPushButton("\u23f8")  # ⏸
        self._pause_btn.setToolTip("Pause")
        self._pause_btn.clicked.connect(self._player.pause_music)
        ctrl_row.addWidget(self._pause_btn)

        self._stop_btn = QPushButton("\u23f9")  # ⏹
        self._stop_btn.setToolTip("Stop")
        self._stop_btn.clicked.connect(self._player.stop_music)
        ctrl_row.addWidget(self._stop_btn)

        self._next_btn = QPushButton("\u23ed")  # ⏭
        self._next_btn.setToolTip("Next")
        self._next_btn.clicked.connect(self._player.next_track)
        ctrl_row.addWidget(self._next_btn)
        left.addLayout(ctrl_row)

        # Shuffle / Repeat
        opt_row = QHBoxLayout()
        self._shuffle_cb = QCheckBox("Shuffle")
        self._shuffle_cb.toggled.connect(self._on_shuffle_toggled)
        opt_row.addWidget(self._shuffle_cb)

        self._repeat_cb = QCheckBox("Repeat")
        self._repeat_cb.toggled.connect(self._on_repeat_toggled)
        opt_row.addWidget(self._repeat_cb)
        opt_row.addStretch()
        left.addLayout(opt_row)

        # Music volume
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Music Vol:"))
        self._music_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._music_vol_slider.setRange(0, 100)
        self._music_vol_slider.setValue(
            int(self._player.music_volume * 100)
        )
        self._music_vol_slider.valueChanged.connect(self._on_music_vol_changed)
        vol_row.addWidget(self._music_vol_slider)
        self._music_vol_label = QLabel(f"{int(self._player.music_volume * 100)}%")
        vol_row.addWidget(self._music_vol_label)
        left.addLayout(vol_row)

        # Folder / Playlist management
        mgmt_row = QHBoxLayout()
        add_folder_btn = QPushButton("Add Folder...")
        add_folder_btn.clicked.connect(self._add_folder)
        mgmt_row.addWidget(add_folder_btn)

        add_files_btn = QPushButton("Add Files...")
        add_files_btn.clicked.connect(self._add_files)
        mgmt_row.addWidget(add_files_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected)
        mgmt_row.addWidget(remove_btn)
        left.addLayout(mgmt_row)

        layout.addLayout(left, 2)

        # ── RIGHT: Ambient Sounds (dynamic) ───────────────────────────
        right = QVBoxLayout()
        right.setSpacing(8)

        # Header row
        amb_header = QHBoxLayout()
        amb_title = QLabel("Ambient Sounds")
        amb_title.setStyleSheet("font-size: 22px; font-weight: 600;")
        amb_header.addWidget(amb_title)
        amb_header.addStretch()

        self._refresh_amb_btn = QPushButton("Refresh")
        self._refresh_amb_btn.setToolTip(
            "Re-scan assets/sounds/ for new or removed files"
        )
        self._refresh_amb_btn.clicked.connect(self._refresh_ambient_ui)
        amb_header.addWidget(self._refresh_amb_btn)
        right.addLayout(amb_header)

        hint = QLabel(
            f"Place .mp3 / .wav / .ogg files in\n"
            f"'{AMBIENT_SOUNDS_DIR}/' and click Refresh."
        )
        hint.setStyleSheet("color: #868e96; font-size: 11px; padding-bottom: 4px;")
        right.addWidget(hint)

        # Scrollable area for ambient controls (handles many files)
        self._ambient_scroll = QScrollArea()
        self._ambient_scroll.setWidgetResizable(True)
        self._ambient_scroll.setStyleSheet("QScrollArea { border: none; }")
        self._ambient_container = QWidget()
        self._ambient_layout = QVBoxLayout(self._ambient_container)
        self._ambient_layout.setContentsMargins(0, 0, 0, 0)
        self._ambient_layout.setSpacing(4)
        self._ambient_layout.addStretch()
        self._ambient_scroll.setWidget(self._ambient_container)
        right.addWidget(self._ambient_scroll, 1)

        layout.addLayout(right, 1)

    # ── Ambient UI builder ────────────────────────────────────────────

    def _refresh_ambient_ui(self) -> None:
        """Clear and rebuild ambient controls from folder scan."""
        # Remove old widgets
        while self._ambient_layout.count() > 1:  # keep the stretch
            item = self._ambient_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        self._ambient_checks.clear()
        self._ambient_sliders.clear()
        self._ambient_labels.clear()
        self._ambient_paths.clear()

        sounds = scan_ambient_sounds()
        if not sounds:
            empty = QLabel("  (no audio files found)")
            empty.setStyleSheet("color: #868e96; font-size: 13px; padding: 12px;")
            self._ambient_layout.insertWidget(0, empty)
            return

        for display_name, file_path in sounds:
            key = display_name.lower().replace(" ", "_")
            self._ambient_paths[key] = file_path

            row = QHBoxLayout()
            row.setSpacing(6)

            cb = QCheckBox(display_name)
            cb.toggled.connect(
                lambda checked, k=key: self._on_ambient_toggled(k, checked)
            )
            self._ambient_checks[key] = cb
            row.addWidget(cb, 1)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(30)
            slider.valueChanged.connect(
                lambda val, k=key: self._on_ambient_vol_changed(k, val)
            )
            self._ambient_sliders[key] = slider
            row.addWidget(slider)

            label = QLabel("30%")
            label.setFixedWidth(36)
            self._ambient_labels[key] = label
            row.addWidget(label)

            # Insert before the stretch
            self._ambient_layout.insertLayout(
                self._ambient_layout.count() - 1, row
            )

    def _clear_layout(self, layout) -> None:
        """Recursively remove all items from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    # ── Music controls ────────────────────────────────────────────────

    def _on_play_clicked(self) -> None:
        if self._player.is_music_playing:
            self._player.pause_music()
            return
        if self._player.current_track_index < 0:
            self._player.play_music(0)
        else:
            self._player.resume_music()

    def _on_playlist_double_click(self, index) -> None:
        self._player.play_music(index.row())
        self._update_now_playing()

    def _on_shuffle_toggled(self, checked: bool) -> None:
        self._player.shuffle = checked

    def _on_repeat_toggled(self, checked: bool) -> None:
        self._player.repeat = checked

    def _on_music_vol_changed(self, value: int) -> None:
        self._player.music_volume = value / 100.0
        self._music_vol_label.setText(f"{value}%")
        self._db.set_setting("music_volume", str(value))

    def _update_now_playing(self) -> None:
        name = self._player.current_track_name
        self._now_playing.setText(name if name else "No track playing")

    def _refresh_playlist_ui(self) -> None:
        self._playlist_widget.clear()
        for path in self._player.playlist:
            name = os.path.splitext(os.path.basename(path))[0]
            self._playlist_widget.addItem(name)

    # ── File/folder management ────────────────────────────────────────

    AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma")

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return

        found = []
        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(self.AUDIO_EXTS):
                    found.append(os.path.join(root, f))

        if found:
            self._player.add_to_playlist(found)
            self._refresh_playlist_ui()
            self._ensure_playlist()
            if self._playlist_id:
                for path in found:
                    self._db.add_track(self._playlist_id, path)
        else:
            QMessageBox.information(
                self, "No Audio Found",
                "No supported audio files found in the selected folder."
            )

    def _add_files(self) -> None:
        filter_str = "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg *.aac *.wma);;All Files (*)"
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "", filter_str
        )
        if files:
            self._player.add_to_playlist(files)
            self._refresh_playlist_ui()
            self._ensure_playlist()
            if self._playlist_id:
                for path in files:
                    self._db.add_track(self._playlist_id, path)

    def _remove_selected(self) -> None:
        row = self._playlist_widget.currentRow()
        if row >= 0:
            self._player.remove_from_playlist(row)
            self._refresh_playlist_ui()

    def _ensure_playlist(self) -> None:
        if self._playlist_id is not None:
            return
        playlists = self._db.get_playlists()
        if playlists:
            self._playlist_id = playlists[0]["id"]
        else:
            self._playlist_id = self._db.create_playlist("Main")

    def _load_saved_state(self) -> None:
        """Restore playlist and settings from DB on startup."""
        saved_vol = int(self._db.get_setting("music_volume", "40"))
        self._music_vol_slider.setValue(saved_vol)

        playlists = self._db.get_playlists()
        if playlists:
            self._playlist_id = playlists[0]["id"]
            tracks = self._db.get_tracks(self._playlist_id)
            paths = [t["file_path"] for t in tracks]
            valid = [p for p in paths if os.path.isfile(p)]
            if valid:
                self._player.load_playlist(valid)
                self._refresh_playlist_ui()

        # Restore ambient volume global
        saved_amb = int(self._db.get_setting("ambient_volume", "30"))
        for slider in self._ambient_sliders.values():
            slider.setValue(saved_amb)

    # ── Ambient sound controls ────────────────────────────────────────

    def _on_ambient_toggled(self, key: str, checked: bool) -> None:
        path = self._ambient_paths.get(key)
        if not path or not os.path.isfile(path):
            return
        if checked:
            vol = self._ambient_sliders[key].value() / 100.0
            self._player.play_ambient(key, path, vol)
        else:
            self._player.stop_ambient(key)

    def _on_ambient_vol_changed(self, key: str, value: int) -> None:
        if key in self._ambient_labels:
            self._ambient_labels[key].setText(f"{value}%")
        self._player.set_ambient_volume(key, value / 100.0)
        self._db.set_setting("ambient_volume", str(value))

    def refresh_on_navigate(self) -> None:
        self._update_now_playing()
