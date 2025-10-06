# GAMDL GUI — Apple Music Downloader

A modern **PyQt6 desktop application** for downloading Apple Music songs, albums, playlists, music videos, and post videos.  
This GUI wraps the [GAMDL](https://github.com/glomatico/gamdl) command‑line tool into a user‑friendly interface with presets, progress bars, and configuration persistence.

**Join Glomatico's Discord Server:** <https://discord.gg/aBjMEZ9tnq>

---

## ✨ Features

- **High‑Quality Songs**: Download tracks in AAC, ALAC, Atmos, and other codecs.
- **High‑Quality Music Videos**: Download music videos up to 4K resolution.
- **Synced Lyrics**: Save synced lyrics in LRC, SRT, or TTML formats.
- **Artist Support**: Fetch all albums or music videos from an artist link.
- **Presets**: One‑click profiles for *Audio‑only*, *Music Videos*, and *Lossless* workflows.
- **Customizable**: Advanced tab for resolution, codec, remux format, language, and more.
- **Progress & Logs**: Built‑in progress bar and live log viewer.
- **First‑Run Wizard**: Guides you to select your `cookies.txt` file.
- **Tools Tab**: Check installation status of Python, GAMDL, and FFmpeg. Install or upgrade with one click.
- **Config Persistence**: Remembers your settings in `settings.ini`.

---

## 🖥️ Prerequisites

- **Python 3.10 or higher** installed on your system.
- **GAMDL** installed (`pip install gamdl`).
- **cookies.txt** file exported from your Apple Music browser session (Netscape format).  
  Use one of these extensions while logged in with an active subscription:
  - **Firefox**: [Export Cookies](https://addons.mozilla.org/addon/export-cookies-txt)
  - **Chromium‑based Browsers**: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- **FFmpeg** available on your system PATH or configured in the Tools tab.  
  Recommended builds:
  - **Windows**: [AnimMouse's FFmpeg Builds](https://github.com/AnimMouse/ffmpeg-stable-autobuild/releases)
  - **Linux**: [John Van Sickle's FFmpeg Builds](https://johnvansickle.com/ffmpeg/)

### Optional dependencies

- [mp4decrypt](https://www.bento4.com/downloads/) — required for `mp4box` remux mode, music video downloads, and experimental codecs.
- [MP4Box](https://gpac.io/downloads/gpac-nightly-builds/) — required for `mp4box` remux mode.
- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE/releases/latest) — required for `nm3u8dlre` download mode.

---

## 🚀 Installation

1. Download the app in the releases page or download this repository and run python app.py
2. Install dependencies: pip install PyQt6 gamdl

---

## 🕹️ Usage

- Launch the app
- On first run, select your `cookies.txt` file when prompted or directly paste it inside the same follder
- Paste an Apple Music URL (song, album, playlist, artist, music video, or post video).
- Choose output and temp folders if desired.
- Adjust advanced options or use a preset.
- Click **Download**. Progress and logs will appear in the **Logs** tab.

---

## 📂 Supported URL Types

- Song
- Album (public or library)
- Playlist (public or library)
- Music video
- Artist
- Post video

---

## ⚙️ Configuration

- Settings are saved automatically in `settings.ini` (in the same folder as the app).
- Includes paths, advanced options, and tool overrides.
- You can also override tool paths (FFmpeg, mp4decrypt, MP4Box, N_m3u8DL‑RE) in the **Tools** tab.

---

## 🧩 Presets

- **Audio‑only**: AAC codec, synced lyrics, skip music videos.
- **Music videos**: H.264 codec, 1080p resolution, no lyrics.
- **Lossless**: ALAC codec, 2160p resolution, H.265 video.

---

## 🔧 Tools Tab

- **Python**: Check version, install if missing.
- **GAMDL**: Check version, install or upgrade with one click.
- **FFmpeg**: Check version, install via winget (Windows) or open download page.
- **mp4decrypt / MP4Box / N_m3u8DL‑RE**: Configure paths or open download pages.

---

## 📜 License

This project is provided as a community GUI wrapper for [GAMDL](https://github.com/glomatico/gamdl).

