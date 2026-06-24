# VolumeCommander

VolumeCommander is a Windows desktop utility that lets you control system and application audio with global hotkeys. It shows a small on-screen display (OSD) whenever the volume or mute state changes and exposes a system tray menu for reloading the configuration or exiting the app.

## Features

- Adjust the system volume
- Adjust the volume of the active foreground application
- Adjust the volume of specific apps by executable name
- Toggle mute for the system or an app
- Show the current level in a compact OSD
- Reload hotkeys from the tray menu without restarting

## Requirements

This project targets Windows and uses the following Python packages:

- keyboard
- pystray
- psutil
- pywin32
- comtypes
- Pillow
- pycaw

Install them with:

```powershell
pip install keyboard pystray psutil pywin32 comtypes Pillow pycaw
```

## Running the app

1. Copy the example config to a file named config.json if you do not already have one:

```powershell
copy config.example.json config.json
```

2. Start the app:

```powershell
python VolumeCommander.py
```

3. Use the tray icon to reload the configuration or exit the app.

## Configuration

The app reads hotkeys from config.json. Each hotkey entry is a JSON object with the following fields:

- key_combo: the key combination to listen for
- target: the audio target
  - system
  - active
  - a single executable name, such as chrome.exe
  - a list of executable names, such as ["discord.exe", "teams.exe"]
- action: the action to perform
  - up
  - down
  - toggle_mute
- amount: the step size used for volume changes, typically 0.01 to 0.05

## Example configuration

```json
{
  "hotkeys": [
    {
      "key_combo": -175,
      "target": "system",
      "action": "up",
      "amount": 0.02
    },
    {
      "key_combo": -174,
      "target": "system",
      "action": "down",
      "amount": 0.02
    },
    {
      "key_combo": -173,
      "target": "system",
      "action": "toggle_mute",
      "amount": 0.0
    },
    {
      "key_combo": "f13",
      "target": "active",
      "action": "up",
      "amount": 0.02
    },
    {
      "key_combo": "f14",
      "target": "active",
      "action": "down",
      "amount": 0.02
    },
    {
      "key_combo": "f15",
      "target": "active",
      "action": "toggle_mute",
      "amount": 0.0
    },
    {
      "key_combo": "alt+f23",
      "target": "chrome.exe",
      "action": "toggle_mute",
      "amount": 0.0
    },
    {
      "key_combo": "alt+f24",
      "target": ["discord.exe", "teams.exe"],
      "action": "toggle_mute",
      "amount": 0.0
    }
  ]
}
```

## Notes

- The app expects config.json to be present in the same folder as VolumeCommander.py when it starts.
- If the config file is missing or invalid, the app falls back to an empty hotkey list.
- The OSD shows either a percentage value or the word Muted when the target has been muted.
- The tray menu offers Reload Config and Exit actions.

## Building an executable

If you want a packaged Windows executable, use the provided build scripts:

```powershell
compile-release.bat
```

The output will be placed in the dist folder.
