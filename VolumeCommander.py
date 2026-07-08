import json
import threading
import queue
import tkinter as tk
import keyboard
import pystray
import psutil
import win32gui
import win32process
import comtypes
import os
import sys
from PIL import Image, ImageDraw
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume

CONFIG_FILE = 'config.json'

# Thread-safe queue to pass volume updates to the UI
osd_queue = queue.Queue()

# --- 1. Load Configuration ---
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"hotkeys": []}


def format_osd_text(name, volume, muted=False):
    if muted:
        return f"{name}: Muted"
    return f"{name}: {int(volume * 100)}%"

# --- Utility: Get Active Window Process Name ---
def get_active_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().lower()
    except Exception:
        return None

# --- 2. Audio Adjustment Logic ---
def adjust_volume(target, action, amount):
    comtypes.CoInitialize()  # Required for background threads
    try:
        delta = amount if action == "up" else -amount if action == "down" else 0.0
        new_vol = None
        display_name = "Volume"
        muted = None

        # Handle System Volume
        if target == "system":
            device = AudioUtilities.GetSpeakers()
            volume = getattr(device, "EndpointVolume", None)
            if volume is None:
                return

            if action == "toggle_mute":
                if hasattr(volume, "GetMute") and hasattr(volume, "SetMute"):
                    is_muted = volume.GetMute()
                    volume.SetMute(not is_muted, None)
                    muted = not is_muted
                else:
                    muted = True
                current_vol = volume.GetMasterVolumeLevelScalar()
                new_vol = current_vol
            else:
                current_vol = volume.GetMasterVolumeLevelScalar()
                new_vol = max(0.0, min(1.0, current_vol + delta))
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                muted = False
            display_name = "System"

        # Handle Specific/Active Apps
        else:
            if target == "active":
                target_apps = [get_active_process_name()]
            elif isinstance(target, list):
                target_apps = [t.lower() for t in target]
            else:
                target_apps = [target.lower()]

            if not target_apps or target_apps == [None]:
                return

            display_name = target_apps[0].replace('.exe', '') if target_apps[0] else "App"

            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.name().lower() in target_apps:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    if action == "toggle_mute":
                        current_muted = volume.GetMute()
                        volume.SetMute(not current_muted, None)
                        muted = not current_muted
                        new_vol = volume.GetMasterVolume()
                    else:
                        current_vol = volume.GetMasterVolume()
                        new_vol = max(0.0, min(1.0, current_vol + delta))
                        volume.SetMasterVolume(new_vol, None)
                        muted = False

        # Send the update to the UI queue
        if new_vol is not None or muted is not None:
            osd_queue.put({
                "name": display_name.capitalize(),
                "volume": new_vol if new_vol is not None else 0.0,
                "muted": muted if muted is not None else False,
            })

    finally:
        comtypes.CoUninitialize()

# --- 3. Global Hotkey Interception ---
def setup_hotkeys(config):
    keyboard.unhook_all()
    for item in config.get("hotkeys", []):
        key_combo = item["key_combo"]
        target = item["target"]
        action = item["action"]
        amount = item.get("amount", 0.05)
        
        keyboard.add_hotkey(
            key_combo, 
            adjust_volume, 
            args=(target, action, amount),
            suppress=False
        )

# --- 4. System Tray Implementation ---
def get_icon_path():
    """
    Helps the app find the icon file whether it is running as a standard 
    Python script or as a bundled PyInstaller .exe
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller extracts bundled files to a temporary folder (_MEIPASS)
        return os.path.join(sys._MEIPASS, 'icon.ico')
    
    # Standard script execution
    return 'icon.ico'

def create_image():
    # Load the custom image file instead of drawing one
    return Image.open(get_icon_path())

def reload_app(icon, item):
    config = load_config()
    setup_hotkeys(config)

def exit_app(icon, item):
    keyboard.unhook_all()
    icon.stop()
    osd_queue.put("EXIT") # Signal the GUI to close

# --- 5. On-Screen Display (OSD) UI ---
class VolumeOSD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True) # Removes window borders
        self.root.attributes('-topmost', True) # Always on top
        self.root.attributes('-alpha', 0.90) # Slight transparency
        self.root.configure(bg='#1e1e1e')
        self.root.withdraw() # Hide initially

        # Position at the bottom center of the screen
        window_width, window_height = 300, 65
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = screen_height - 180
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')

        # App Name & Volume Text
        self.label = tk.Label(self.root, text="", fg="white", bg="#1e1e1e", font=("Segoe UI", 12, "bold"))
        self.label.pack(pady=(8, 2))

        # Visual Progress Bar (using a Canvas)
        self.canvas = tk.Canvas(self.root, width=260, height=8, bg="#444444", highlightthickness=0)
        self.canvas.pack(pady=2)
        self.bar = self.canvas.create_rectangle(0, 0, 0, 8, fill="#0096FF")

        self.hide_timer = None
        self.check_queue()

    def check_queue(self):
        try:
            while True:
                msg = osd_queue.get_nowait()
                if msg == "EXIT":
                    self.root.destroy()
                    return
                self.show_osd(msg['name'], msg.get('volume', 0.0), msg.get('muted', False))
        except queue.Empty:
            pass
        
        # Check the queue again in 50 milliseconds
        self.root.after(50, self.check_queue)

    def show_osd(self, name, volume, muted=False):
        # Update text and bar width
        self.label.config(text=format_osd_text(name, volume, muted))
        bar_width = 0 if muted else max(0.0, min(1.0, volume))
        self.canvas.coords(self.bar, 0, 0, int(260 * bar_width), 8)
        
        self.root.deiconify() # Reveal the window
        
        # Reset the auto-hide timer
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
        self.hide_timer = self.root.after(2000, self.root.withdraw) # Hide after 2 seconds

    def run(self):
        self.root.mainloop()

# --- 6. Main Execution ---
def main():
    config = load_config()
    setup_hotkeys(config)

    # Setup and run the System Tray in a background thread
    menu = pystray.Menu(
        pystray.MenuItem('Reload Config', reload_app),
        pystray.MenuItem('Exit', exit_app)
    )
    icon = pystray.Icon("VolumeCommander", create_image(), "Volume Hotkey Manager", menu)
    threading.Thread(target=icon.run, daemon=True).start()
    
    # Run the OSD UI on the main thread
    osd = VolumeOSD()
    osd.run()

if __name__ == '__main__':
    main()