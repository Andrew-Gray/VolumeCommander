# VolumeCommander

VolumeCommander is a Windows system-tray application that controls the system volume, the active application's volume, or the volume of selected applications through global hotkeys. It also displays a small on-screen volume indicator.

## Requirements

- Windows
- Python 3
- The project dependencies:

```powershell
py -m pip install pyinstaller keyboard pystray psutil pywin32 comtypes pillow pycaw
```

## Build

Run all build commands from the project directory.

### Using the batch files

For a release build without a console window:

```powershell
.\compile-release.bat
```

For a debug build with a console window, which is useful for viewing errors and diagnostic output:

```powershell
.\compile-debug.bat
```

The executable is created at `dist\VolumeCommander.exe`.

### Key Combo Finder utility

`KeyComboFinder.py` is a small companion app that shows the exact JSON value to
use for `key_combo`. It uses the same `keyboard` package as VolumeCommander, so
the names it reports match the names accepted by the main app. It also displays
the raw scan code, which is useful for unusual media or macro keys.

Run it from source:

```powershell
py KeyComboFinder.py
```

Or build `dist\KeyComboFinder.exe`:

```powershell
.\compile-key-finder.bat
```

Press and release a key or combination, then use **Copy** and paste the result
directly after `"key_combo":` in `config.json`. The finder observes keys
globally but does not suppress them, and it stops observing when its window is
closed.

### Using the command line

The release build command is:

```powershell
pyinstaller --noconsole --onefile --icon=icon.ico --add-data "icon.ico;." VolumeCommander.py
```

The debug build command is:

```powershell
pyinstaller --onefile --icon=icon.ico --add-data "icon.ico;." VolumeCommander.py
```

PyInstaller may reuse generated files from a previous build. To force a clean build, add `--clean` to either command.

## Configure

Copy `config.example.json` to `config.json`:

```powershell
Copy-Item config.example.json config.json
```

Do not merely rename the example if you want to keep it as a reference. Place `config.json` in the directory from which you start `VolumeCommander.exe` (normally beside the executable), because the application reads it from its current working directory.

The file contains a `hotkeys` array. Each item defines one hotkey:

```json
{
  "hotkeys": [
    {
      "key_combo": "ctrl+f23",
      "target": "chrome.exe",
      "action": "up",
      "amount": 0.02,
      "suppress": false
    }
  ]
}
```

### Configuration values

| Field | Required | Supported values |
| --- | --- | --- |
| `key_combo` | Yes | A key or combination accepted by the Python `keyboard` package, such as `f13`, `ctrl+f23`, `shift+f24`, or `alt+f24`. Integer scan codes such as `-175` may also be used for special media keys. |
| `target` | Yes | `"system"` for the Windows master volume; `"active"` for the foreground application; an executable name such as `"chrome.exe"`; or an array such as `["discord.exe", "teams.exe"]` to affect all matching audio sessions. Executable matching is case-insensitive. |
| `action` | Yes | `"up"`, `"down"`, or `"toggle_mute"`. |
| `amount` | No | A decimal volume step between `0.0` and `1.0`. For example, `0.02` changes volume by 2 percentage points. The default is `0.05`. It is ignored by `toggle_mute`. |
| `suppress` | No | JSON boolean `true` prevents the matched hotkey from reaching other applications; `false` allows it through. The default is `false`. Only the boolean value `true` enables suppression (not the string `"true"`). |

Volume changes are clamped to the valid 0-100% range. For application targets, the application must have an active Windows audio session for its volume to be changed.

After editing `config.json`, right-click the VolumeCommander tray icon and select **Reload Config**. Select **Exit** to close the application.

## Run without building

You can also run the Python source directly after installing the dependencies:

```powershell
py VolumeCommander.py
```
