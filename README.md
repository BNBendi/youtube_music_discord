# 🎵 YouTube Music Discord Rich Presence (Custom Script)

A lightweight, background Python script that interfaces with the Windows media subsystem to track **YouTube Music** playback within Brave or Chrome browsers. It pushes your real-time activity directly to your Discord profile, complete with the song title, artist, a custom logo, and a second-accurate, native playback progress bar.

Unlike bloated third-party applications, this solution relies entirely on a single, clean Python script using native Windows API components.

---

## 🧠 How It Works Behind the Scenes

Understanding how the script communicates with your system helps clarify how the data flows:

1. **Windows SMTC Layer:** Every time a song plays in Brave/Chrome, Windows registers it in its internal media manager (System Media Transport Controls). This is the exact same system that displays the media control popup next to your Windows volume slider.
2. **Python Extraction:** The script continuously checks the SMTC layer. It grabs the song title, artist name, total length of the song, and your current listening position.
3. **Time-Tick Conversion:** Windows tracks media durations in "Ticks" (hundred-nanosecond intervals). The script converts these massive numbers into clean, standard seconds.
4. **Discord API Push:** The script acts as a bridge, passing the processed data over a local socket to your active Discord desktop client using your unique Client ID. Discord then takes care of rendering the moving progress bar natively on your profile.

---

## ✨ Features

* **Native Playback Progress Bar (Timeline):** Dynamically calculates your current song position to match Discord's native media slider.
* **Fault-Tolerant (Ad/Stream Protection):** Automatically switches to a standard elapsed stopwatch if track duration becomes unavailable (e.g., during YouTube ads or continuous live streams) to prevent script crashes.
* **Auto-Reconnect Protection:** If Discord is closed and reopened, or if the network stumbles, the script silently re-establishes the connection in the background.
* **Resource Efficient:** Runs on a 3-second sleep loop, ensuring practically zero impact on your CPU or RAM.

---

## 🛠️ Step-by-Step Installation & Setup Guide

Follow these sequential phases to get your environment configured and the script running flawlessly.

### Phase 1: Folder Configuration
Make sure your Python script file is named **`youtube_music.py`** and is stored inside your dedicated project workspace directory (e.g., `C:\Users\...\Documents\folder_name\youtube_music_discord`).

### Phase 2: Create and Activate the Virtual Environment (`.venv`)
Using a virtual environment ensures that the required libraries remain locked inside this folder and don't conflict with other Python projects.

1. Open **Visual Studio Code**.
2. Open your project folder.
3. Open a new **PowerShell Terminal** inside VS Code (`Ctrl + ~`).
4. Execute the following commands to initialize and enter your virtual environment:

```bash
# 1. Initialize the internal virtual environment folder
python -m venv .venv

# 2. Grant temporary execution permissions to the terminal session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

# 3. Trigger the activation script to boot into your environment
.\.venv\Scripts\Activate.ps1
