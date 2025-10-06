import sys
import platform
import shutil
import subprocess
import configparser
import re
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QComboBox, QCheckBox,
    QProgressBar, QMessageBox, QTextEdit, QTabWidget
)

APP_TITLE = "GAMDL — Apple Music Downloader"

# When frozen by PyInstaller, sys._MEIPASS points to the temp bundle dir
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys._MEIPASS)
else:
    APP_DIR = Path(__file__).parent

# Put user config/wizard marker in the home directory (always writable)
CONFIG_DIR = Path.home() / ".gamdl_gui"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = CONFIG_DIR / "settings.ini"
FIRSTWIZARD_PATH = CONFIG_DIR / "firstwizard.done"

# Icon can still be loaded from the app directory
ICON_PATH = APP_DIR / "icon.png"

# Default output/temp folders remain in the user’s Music folder
DEFAULT_OUTPUT = str(Path.home() / "Apple Music")
DEFAULT_TEMP = str(Path.home() / "Apple Music" / "temp")


# Worker thread for running gamdl
class ProcessWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished_ok = pyqtSignal()
    finished_err = pyqtSignal(str)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        creationflags = 0
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=creationflags
            )
        except Exception as e:
            self.finished_err.emit(f"Failed to start process:\n{e}")
            return

        progress_re = re.compile(r"(\d{1,3}(?:\.\d+)?)%")

        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            line = line.rstrip()
            self.log.emit(line)

            match = progress_re.search(line)
            if match:
                try:
                    pct = float(match.group(1))
                    self.progress.emit(int(min(max(pct, 0), 100)))
                except Exception:
                    pass

        ret = proc.wait()
        if ret == 0:
            self.progress.emit(100)
            self.finished_ok.emit()
        else:
            self.finished_err.emit(f"Process exited with code {ret}")

class GamdlGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1200, 860)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        # State
        self.output_dir = DEFAULT_OUTPUT
        self.temp_dir = DEFAULT_TEMP
        self.cookies_path = ""
        self.ffmpeg_path = shutil.which("ffmpeg") or ""
        self.mp4decrypt_path = shutil.which("mp4decrypt") or ""
        self.mp4box_path = shutil.which("MP4Box") or ""
        self.nm3u8dl_path = shutil.which("N_m3u8DL-RE") or ""
        self.worker = None
        self._recent_logs = []

        root = QVBoxLayout(self)

        # Tabs
        tabs = QTabWidget()
        root.addWidget(tabs)

        # Download tab
        tab_download = QWidget()
        tabs.addTab(tab_download, "Download")
        dl_layout = QGridLayout(tab_download)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paste Apple Music URL")
        dl_layout.addWidget(QLabel("URL"), 0, 0)
        dl_layout.addWidget(self.url_edit, 0, 1, 1, 3)

        self.output_label = QLabel(DEFAULT_OUTPUT)
        self.output_btn = QPushButton("Choose output")
        self.output_btn.clicked.connect(self.choose_output)
        dl_layout.addWidget(QLabel("Output"), 1, 0)
        dl_layout.addWidget(self.output_label, 1, 1, 1, 2)
        dl_layout.addWidget(self.output_btn, 1, 3)

        self.temp_label = QLabel(DEFAULT_TEMP)
        self.temp_btn = QPushButton("Choose temp")
        self.temp_btn.clicked.connect(self.choose_temp)
        dl_layout.addWidget(QLabel("Temp"), 2, 0)
        dl_layout.addWidget(self.temp_label, 2, 1, 1, 2)
        dl_layout.addWidget(self.temp_btn, 2, 3)

        self.cookies_label = QLabel("No cookies.txt selected")
        self.cookies_btn = QPushButton("Select cookies.txt")
        self.cookies_btn.clicked.connect(self.choose_cookies)
        dl_layout.addWidget(QLabel("Cookies"), 3, 0)
        dl_layout.addWidget(self.cookies_label, 3, 1, 1, 2)
        dl_layout.addWidget(self.cookies_btn, 3, 3)

        # Advanced tab
        tab_advanced = QWidget()
        tabs.addTab(tab_advanced, "Advanced")
        adv_layout = QGridLayout(tab_advanced)

        self.cb_lyrics = QCheckBox("Download synced lyrics")
        self.cb_lyrics.setChecked(True)
        self.lyrics_fmt = QComboBox()
        self.lyrics_fmt.addItems(["lrc", "srt", "ttml"])
        adv_layout.addWidget(self.cb_lyrics, 0, 0)
        adv_layout.addWidget(QLabel("Lyrics format"), 0, 1)
        adv_layout.addWidget(self.lyrics_fmt, 0, 2)

        self.resolution = QComboBox()
        self.resolution.addItems(["240p","360p","480p","540p","720p","1080p","1440p","2160p"])
        adv_layout.addWidget(QLabel("Video resolution"), 1, 0)
        adv_layout.addWidget(self.resolution, 1, 1)

        self.codec_mv = QComboBox()
        self.codec_mv.addItems(["h264","h265","ask"])
        adv_layout.addWidget(QLabel("Music video codec"), 1, 2)
        adv_layout.addWidget(self.codec_mv, 1, 3)

        self.codec_song = QComboBox()
        self.codec_song.addItems([
            "aac-legacy","aac-he-legacy",
            "aac","aac-he","aac-binaural","aac-downmix",
            "aac-he-binaural","aac-he-downmix",
            "atmos","ac3","alac","ask"
        ])
        adv_layout.addWidget(QLabel("Song codec"), 2, 0)
        adv_layout.addWidget(self.codec_song, 2, 1)

        self.remux_fmt = QComboBox()
        self.remux_fmt.addItems(["m4v","mp4"])
        adv_layout.addWidget(QLabel("Remux format (MV)"), 2, 2)
        adv_layout.addWidget(self.remux_fmt, 2, 3)

        self.download_mode = QComboBox()
        self.download_mode.addItems(["ytdlp","nm3u8dlre"])
        adv_layout.addWidget(QLabel("Download mode"), 3, 0)
        adv_layout.addWidget(self.download_mode, 3, 1)

        self.lang_edit = QLineEdit("en-US")
        adv_layout.addWidget(QLabel("Metadata language"), 3, 2)
        adv_layout.addWidget(self.lang_edit, 3, 3)

        self.cb_save_cover = QCheckBox("Save cover")
        self.cb_save_playlist = QCheckBox("Save playlist M3U8")
        self.cb_overwrite = QCheckBox("Overwrite existing")
        self.cb_disable_mv_skip = QCheckBox("Don't skip MVs in albums/playlists")
        adv_layout.addWidget(self.cb_save_cover, 4, 0)
        adv_layout.addWidget(self.cb_save_playlist, 4, 1)
        adv_layout.addWidget(self.cb_overwrite, 4, 2)
        adv_layout.addWidget(self.cb_disable_mv_skip, 4, 3)

        # Presets
        presets_box = QGroupBox("Presets")
        presets_layout = QHBoxLayout()
        btn_audio = QPushButton("Audio‑only")
        btn_video = QPushButton("Music videos")
        btn_lossless = QPushButton("Lossless")
        btn_audio.clicked.connect(self.apply_preset_audio)
        btn_video.clicked.connect(self.apply_preset_video)
        btn_lossless.clicked.connect(self.apply_preset_lossless)
        for b in (btn_audio, btn_video, btn_lossless):
            b.setObjectName("pillButton")
        presets_layout.addWidget(btn_audio)
        presets_layout.addWidget(btn_video)
        presets_layout.addWidget(btn_lossless)
        presets_box.setLayout(presets_layout)
        adv_layout.addWidget(presets_box, 5, 0, 1, 4)

        # Tools tab
        tab_tools = QWidget()
        tabs.addTab(tab_tools, "Tools")
        tools_layout = QGridLayout(tab_tools)

        # Existing tools paths + installers
        self.ffmpeg_edit = QLineEdit(self.ffmpeg_path)
        btn_ffmpeg = QPushButton("Install FFmpeg")
        btn_ffmpeg.clicked.connect(lambda: self.install_tool("ffmpeg"))
        tools_layout.addWidget(QLabel("FFmpeg path"), 0, 0)
        tools_layout.addWidget(self.ffmpeg_edit, 0, 1, 1, 2)
        tools_layout.addWidget(btn_ffmpeg, 0, 3)

        self.mp4decrypt_edit = QLineEdit(self.mp4decrypt_path)
        btn_mp4decrypt = QPushButton("Install mp4decrypt")
        btn_mp4decrypt.clicked.connect(lambda: self.install_tool("mp4decrypt"))
        tools_layout.addWidget(QLabel("mp4decrypt path"), 1, 0)
        tools_layout.addWidget(self.mp4decrypt_edit, 1, 1, 1, 2)
        tools_layout.addWidget(btn_mp4decrypt, 1, 3)

        self.mp4box_edit = QLineEdit(self.mp4box_path)
        btn_mp4box = QPushButton("Install MP4Box")
        btn_mp4box.clicked.connect(lambda: self.install_tool("mp4box"))
        tools_layout.addWidget(QLabel("MP4Box path"), 2, 0)
        tools_layout.addWidget(self.mp4box_edit, 2, 1, 1, 2)
        tools_layout.addWidget(btn_mp4box, 2, 3)

        self.nm3u8dl_edit = QLineEdit(self.nm3u8dl_path)
        btn_nm3u8dl = QPushButton("Install N_m3u8DL-RE")
        btn_nm3u8dl.clicked.connect(lambda: self.install_tool("nm3u8dlre"))
        tools_layout.addWidget(QLabel("N_m3u8DL-RE path"), 3, 0)
        tools_layout.addWidget(self.nm3u8dl_edit, 3, 1, 1, 2)
        tools_layout.addWidget(btn_nm3u8dl, 3, 3)

        # New: Python/GAMDL/FFmpeg status and install/upgrade buttons
        self.python_status = QLabel()
        btn_python = QPushButton("Install Python")
        btn_python.clicked.connect(self.install_python)
        tools_layout.addWidget(QLabel("Python"), 4, 0)
        tools_layout.addWidget(self.python_status, 4, 1, 1, 2)
        tools_layout.addWidget(btn_python, 4, 3)

        self.gamdl_status = QLabel()
        btn_gamdl = QPushButton("Install GAMDL")
        btn_gamdl.clicked.connect(self.install_gamdl)
        btn_gamdl_upgrade = QPushButton("Upgrade GAMDL")
        btn_gamdl_upgrade.clicked.connect(self.upgrade_gamdl)
        tools_layout.addWidget(QLabel("GAMDL"), 5, 0)
        tools_layout.addWidget(self.gamdl_status, 5, 1)
        tools_layout.addWidget(btn_gamdl, 5, 2)
        tools_layout.addWidget(btn_gamdl_upgrade, 5, 3)

        self.ffmpeg_status = QLabel()
        tools_layout.addWidget(QLabel("FFmpeg status"), 6, 0)
        tools_layout.addWidget(self.ffmpeg_status, 6, 1, 1, 2)

        # Logs tab
        tab_logs = QWidget()
        tabs.addTab(tab_logs, "Logs")
        logs_layout = QVBoxLayout(tab_logs)
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_font = QFont("Consolas")
        log_font.setPointSize(11)
        self.log_view.setFont(log_font)
        logs_layout.addWidget(self.progress)
        logs_layout.addWidget(self.log_view)

        # Footer
        footer = QHBoxLayout()
        self.btn_download = QPushButton("Download")
        self.btn_download.clicked.connect(self.start_download)
        footer.addStretch(1)
        footer.addWidget(self.btn_download)
        root.addLayout(footer)

        # Theme
        self.apply_theme()

        # Load config + first-run wizard
        self.load_config()
        self.run_first_wizard()

        # Check tools status
        self.check_tools()

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI'; font-size: 13pt; color: #EAEAEA; background-color: #121212; }
            QLineEdit, QTextEdit, QComboBox {
                background: #1E1E1E; border: 1px solid #333; border-radius: 8px; padding: 8px;
            }
            QPushButton { background: #1DB954; color: #000; border-radius: 20px; padding: 8px 18px; font-weight: bold; }
            QPushButton:hover { background: #1ED760; }
            QPushButton#pillButton { border-radius: 22px; padding: 8px 18px; }
            QProgressBar { border: 1px solid #333; border-radius: 8px; text-align: center; font-weight: bold; }
            QProgressBar::chunk { background-color: #1DB954; border-radius: 8px; }
        """)

    # Config persistence
    def load_config(self):
        cfg = configparser.ConfigParser()
        if CONFIG_PATH.exists():
            cfg.read(CONFIG_PATH)
            self.output_dir = cfg.get("paths", "output", fallback=self.output_dir)
            self.temp_dir = cfg.get("paths", "temp", fallback=self.temp_dir)
            self.cookies_path = cfg.get("paths", "cookies", fallback=self.cookies_path)
            self.output_label.setText(self.output_dir)
            self.temp_label.setText(self.temp_dir)
            if self.cookies_path:
                self.cookies_label.setText(self.cookies_path)

            # Advanced
            self.cb_lyrics.setChecked(cfg.getboolean("advanced","synced_lyrics",fallback=True))
            self.lyrics_fmt.setCurrentText(cfg.get("advanced","lyrics_fmt",fallback="lrc"))
            self.resolution.setCurrentText(cfg.get("advanced","resolution",fallback="1080p"))
            self.codec_mv.setCurrentText(cfg.get("advanced","codec_mv",fallback="h264"))
            self.codec_song.setCurrentText(cfg.get("advanced","codec_song",fallback="aac"))
            self.remux_fmt.setCurrentText(cfg.get("advanced","remux_fmt",fallback="mp4"))
            self.download_mode.setCurrentText(cfg.get("advanced","download_mode",fallback="ytdlp"))
            self.lang_edit.setText(cfg.get("advanced","language",fallback="en-US"))
            self.cb_save_cover.setChecked(cfg.getboolean("advanced","save_cover",fallback=False))
            self.cb_save_playlist.setChecked(cfg.getboolean("advanced","save_playlist",fallback=False))
            self.cb_overwrite.setChecked(cfg.getboolean("advanced","overwrite",fallback=False))
            self.cb_disable_mv_skip.setChecked(cfg.getboolean("advanced","disable_mv_skip",fallback=False))

            # Tools
            self.ffmpeg_edit.setText(cfg.get("tools","ffmpeg_path",fallback=self.ffmpeg_edit.text()))
            self.mp4decrypt_edit.setText(cfg.get("tools","mp4decrypt_path",fallback=self.mp4decrypt_edit.text()))
            self.mp4box_edit.setText(cfg.get("tools","mp4box_path",fallback=self.mp4box_edit.text()))
            self.nm3u8dl_edit.setText(cfg.get("tools","nm3u8dlre_path",fallback=self.nm3u8dl_edit.text()))

    def save_config(self):
        cfg = configparser.ConfigParser()
        cfg["paths"] = {
            "output": self.output_dir,
            "temp": self.temp_dir,
            "cookies": self.cookies_path
        }
        cfg["advanced"] = {
            "synced_lyrics": str(self.cb_lyrics.isChecked()),
            "lyrics_fmt": self.lyrics_fmt.currentText(),
            "resolution": self.resolution.currentText(),
            "codec_mv": self.codec_mv.currentText(),
            "codec_song": self.codec_song.currentText(),
            "remux_fmt": self.remux_fmt.currentText(),
            "download_mode": self.download_mode.currentText(),
            "language": self.lang_edit.text().strip() or "en-US",
            "save_cover": str(self.cb_save_cover.isChecked()),
            "save_playlist": str(self.cb_save_playlist.isChecked()),
            "overwrite": str(self.cb_overwrite.isChecked()),
            "disable_mv_skip": str(self.cb_disable_mv_skip.isChecked()),
        }
        cfg["tools"] = {
            "ffmpeg_path": self.ffmpeg_edit.text().strip(),
            "mp4decrypt_path": self.mp4decrypt_edit.text().strip(),
            "mp4box_path": self.mp4box_edit.text().strip(),
            "nm3u8dlre_path": self.nm3u8dl_edit.text().strip(),
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            cfg.write(f)

    def run_first_wizard(self):
        if FIRSTWIZARD_PATH.exists():
            return
        default_cookies = Path.cwd() / "cookies.txt"
        if default_cookies.exists():
            self.cookies_path = str(default_cookies)
            self.cookies_label.setText(str(default_cookies))
        else:
            QMessageBox.information(self, "First‑time setup",
                "cookies.txt is required to authenticate with Apple Music.\n"
                "Export cookies (Netscape format) using a browser extension, then select the file.")
            self.choose_cookies()
        FIRSTWIZARD_PATH.write_text("done")
        self.save_config()

    def choose_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select output folder", self.output_dir)
        if d:
            self.output_dir = d
            self.output_label.setText(d)
            self.save_config()

    def choose_temp(self):
        d = QFileDialog.getExistingDirectory(self, "Select temp folder", self.temp_dir)
        if d:
            self.temp_dir = d
            self.temp_label.setText(d)
            self.save_config()

    def choose_cookies(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select cookies.txt", str(Path.cwd()), "Text files (*.txt);;All files (*.*)")
        if f:
            self.cookies_path = f
            self.cookies_label.setText(f)
            self.save_config()

    # Presets
    def apply_preset_audio(self):
        self.codec_song.setCurrentText("aac")
        self.cb_lyrics.setChecked(True)
        self.resolution.setCurrentText("720p")
        self.download_mode.setCurrentText("ytdlp")
        self.cb_disable_mv_skip.setChecked(True)
        self.save_config()

    def apply_preset_video(self):
        self.codec_mv.setCurrentText("h264")
        self.resolution.setCurrentText("1080p")
        self.cb_lyrics.setChecked(False)
        self.download_mode.setCurrentText("ytdlp")
        self.cb_disable_mv_skip.setChecked(False)
        self.save_config()

    def apply_preset_lossless(self):
        self.codec_song.setCurrentText("alac")
        self.resolution.setCurrentText("2160p")
        self.codec_mv.setCurrentText("h265")
        self.cb_lyrics.setChecked(True)
        self.download_mode.setCurrentText("ytdlp")
        self.save_config()

    def build_cmd(self):
        url = self.url_edit.text().strip()
        if not url:
            raise ValueError("Please enter a valid Apple Music URL.")
        if not self.cookies_path or not Path(self.cookies_path).exists():
            raise ValueError("cookies.txt is required.")

        # Run GAMDL via python -m to avoid PATH issues
        py = sys.executable or (shutil.which("python") or "python")
        cmd = [py, "-m", "gamdl", url]

        # Paths
        if self.output_dir:
            cmd.extend(["--output-path", self.output_dir])
        if self.temp_dir:
            cmd.extend(["--temp-path", self.temp_dir])
        if self.cookies_path:
            cmd.extend(["--cookies-path", self.cookies_path])

        # Advanced mappings
        lang = self.lang_edit.text().strip()
        if lang:
            cmd.extend(["--language", lang])

        if not self.cb_lyrics.isChecked():
            cmd.append("--no-synced-lyrics")
        else:
            cmd.extend(["--synced-lyrics-format", self.lyrics_fmt.currentText()])

        cmd.extend(["--resolution", self.resolution.currentText()])
        cmd.extend(["--codec-music-video", self.codec_mv.currentText()])
        cmd.extend(["--codec-song", self.codec_song.currentText()])
        cmd.extend(["--remux-format-music-video", self.remux_fmt.currentText()])
        cmd.extend(["--download-mode", self.download_mode.currentText()])

        if self.cb_save_cover.isChecked():
            cmd.append("--save-cover")
        if self.cb_save_playlist.isChecked():
            cmd.append("--save-playlist")
        if self.cb_overwrite.isChecked():
            cmd.append("--overwrite")
        if self.cb_disable_mv_skip.isChecked():
            cmd.append("--disable-music-video-skip")

        # Tool path overrides
        if self.ffmpeg_edit.text().strip():
            cmd.extend(["--ffmpeg-path", self.ffmpeg_edit.text().strip()])
        if self.mp4decrypt_edit.text().strip():
            cmd.extend(["--mp4decrypt-path", self.mp4decrypt_edit.text().strip()])
        if self.mp4box_edit.text().strip():
            cmd.extend(["--mp4box-path", self.mp4box_edit.text().strip()])
        if self.nm3u8dl_edit.text().strip():
            cmd.extend(["--nm3u8dlre-path", self.nm3u8dl_edit.text().strip()])

        return cmd

    def start_download(self):
        try:
            cmd = self.build_cmd()
        except Exception as e:
            QMessageBox.warning(self, "Validation error", str(e))
            return

        self.progress.setMaximum(0)
        self.progress.setValue(0)
        self.log_view.clear()
        self._recent_logs.clear()
        self.btn_download.setEnabled(False)

        self.worker = ProcessWorker(cmd)
        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.append_log)
        self.worker.finished_ok.connect(self.on_done)
        self.worker.finished_err.connect(self.on_err)
        self.worker.start()

    def on_progress(self, value):
        if self.progress.maximum() == 0:
            self.progress.setMaximum(100)
        self.progress.setValue(value)

    def append_log(self, text):
        self.log_view.append(text)
        self._recent_logs.append(text)
        if len(self._recent_logs) > 30:
            self._recent_logs.pop(0)

    def on_done(self):
        self.btn_download.setEnabled(True)
        self.progress.setMaximum(100)
        self.progress.setValue(100)
        QMessageBox.information(self, "Done", "Download finished successfully.")

    def on_err(self, msg):
        self.btn_download.setEnabled(True)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        # Show last log lines for easier debugging
        tail = "\n".join(self._recent_logs[-10:]) if self._recent_logs else "(no output)"
        QMessageBox.critical(self, "Error", f"{msg}\n\nLast output:\n{tail}")

    # Tool checks and installers
    def check_tools(self):
        # Python
        py = shutil.which("python") or shutil.which("py")
        if py:
            try:
                out = subprocess.check_output([py, "--version"], text=True).strip()
                self.python_status.setText(f"✅ {out}")
            except Exception:
                self.python_status.setText("✅ Python found")
        else:
            self.python_status.setText("❌ Not installed")

        # GAMDL
        try:
            out = subprocess.check_output([sys.executable, "-m", "gamdl", "--version"], text=True).strip()
            self.gamdl_status.setText(f"✅ {out}")
        except Exception:
            self.gamdl_status.setText("❌ Not installed")

        # FFmpeg
        ff = shutil.which("ffmpeg") or (self.ffmpeg_edit.text().strip() or "")
        if ff and Path(ff).exists() or shutil.which("ffmpeg"):
            try:
                ver = subprocess.check_output([ff if Path(ff).exists() else "ffmpeg", "-version"], text=True).splitlines()[0]
                self.ffmpeg_status.setText(f"✅ {ver}")
            except Exception:
                self.ffmpeg_status.setText("✅ FFmpeg found")
        else:
            self.ffmpeg_status.setText("❌ Not installed")

    def install_python(self):
        import webbrowser
        if platform.system() == "Windows" and shutil.which("winget"):
            subprocess.run(["winget", "install", "-e", "--id", "Python.Python.3.12"])
        else:
            webbrowser.open("https://www.python.org/downloads/")
        self.check_tools()

    def install_gamdl(self):
        subprocess.run([sys.executable, "-m", "pip", "install", "gamdl"])
        self.check_tools()

    def upgrade_gamdl(self):
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "gamdl"])
        self.check_tools()

    def install_tool(self, tool):
        import webbrowser
        system = platform.system()
        if tool == "ffmpeg":
            if system == "Windows" and shutil.which("winget"):
                subprocess.run(["winget", "install", "-e", "--id", "Gyan.FFmpeg"])
            else:
                webbrowser.open("https://ffmpeg.org/download.html")
        elif tool == "mp4decrypt":
            webbrowser.open("https://www.bento4.com/downloads/")
        elif tool == "mp4box":
            webbrowser.open("https://gpac.io/downloads/gpac-nightly-builds/")
        elif tool == "nm3u8dlre":
            webbrowser.open("https://github.com/nilaoda/N_m3u8DL-RE/releases/latest")

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    base_font = QFont("Segoe UI")
    base_font.setPointSize(12)
    app.setFont(base_font)
    w = GamdlGUI()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
