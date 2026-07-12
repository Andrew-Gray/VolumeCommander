"""Small companion utility for discovering VolumeCommander hotkey values."""

import json
import queue
import tkinter as tk
from tkinter import ttk

import keyboard


MODIFIER_ORDER = ("ctrl", "shift", "alt", "windows")
MODIFIER_NAMES = {
    "ctrl": "ctrl",
    "left ctrl": "ctrl",
    "right ctrl": "ctrl",
    "shift": "shift",
    "left shift": "shift",
    "right shift": "shift",
    "alt": "alt",
    "left alt": "alt",
    "right alt": "alt",
    "alt gr": "alt gr",
    "windows": "windows",
    "left windows": "windows",
    "right windows": "windows",
}


def normalized_key_name(name):
    """Return the spelling expected by keyboard's hotkey parser."""
    if not name:
        return None
    name = name.lower().strip()
    return MODIFIER_NAMES.get(name, name)


def format_combo(events):
    """Convert concurrently pressed keyboard events into a config value."""
    names = []
    scan_codes = []
    for event in events:
        name = normalized_key_name(event.name)
        if name and name not in names:
            names.append(name)
        scan_codes.append(event.scan_code)

    if not names:
        return scan_codes[0] if len(scan_codes) == 1 else None

    modifiers = [name for name in MODIFIER_ORDER if name in names]
    other_names = [name for name in names if name not in MODIFIER_ORDER]
    ordered = modifiers + other_names
    return "+".join(ordered) if ordered else None


class KeyComboFinder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VolumeCommander Key Combo Finder")
        self.root.geometry("560x330")
        self.root.minsize(480, 300)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.events = queue.Queue()
        self.pressed = {}
        self.combo_events = {}
        self.hook = None

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Press a key or key combination",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            frame,
            text="Release the keys when finished. Nothing typed here is suppressed.",
        ).pack(anchor="w", pady=(2, 18))

        ttk.Label(frame, text="Config key_combo value:").pack(anchor="w")
        result_row = ttk.Frame(frame)
        result_row.pack(fill="x", pady=(4, 14))
        self.result = tk.StringVar(value="Waiting for input...")
        ttk.Entry(
            result_row,
            textvariable=self.result,
            font=("Consolas", 13),
            state="readonly",
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(result_row, text="Copy", command=self.copy_result).pack(
            side="left", padx=(8, 0)
        )

        self.current = tk.StringVar(value="Currently pressed: none")
        ttk.Label(frame, textvariable=self.current).pack(anchor="w", pady=(0, 10))

        ttk.Label(frame, text="Raw event details:").pack(anchor="w")
        self.details = tk.Text(frame, height=6, wrap="none", font=("Consolas", 10))
        self.details.pack(fill="both", expand=True, pady=(4, 0))
        self.details.insert("1.0", "Key names and scan codes will appear here.")
        self.details.configure(state="disabled")

        self.hook = keyboard.hook(self.on_keyboard_event, suppress=False)
        self.root.after(30, self.process_events)

    def on_keyboard_event(self, event):
        # keyboard invokes hooks on its own thread; Tk must stay on the main thread.
        self.events.put(event)

    def process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event.event_type == keyboard.KEY_DOWN:
                    if event.scan_code not in self.pressed:
                        # If a previous trigger was released while a modifier is
                        # still held, start a fresh combo for the next trigger.
                        if not set(self.combo_events).issubset(self.pressed):
                            self.combo_events = dict(self.pressed)
                        self.pressed[event.scan_code] = event
                        self.combo_events[event.scan_code] = event
                    self.show_current()
                elif event.event_type == keyboard.KEY_UP:
                    if self.combo_events:
                        self.show_completed_combo(list(self.combo_events.values()))
                    self.pressed.pop(event.scan_code, None)
                    if not self.pressed:
                        self.combo_events.clear()
                    self.show_current()
        except queue.Empty:
            pass
        self.root.after(30, self.process_events)

    def show_current(self):
        names = [
            normalized_key_name(event.name) or str(event.scan_code)
            for event in self.pressed.values()
        ]
        self.current.set("Currently pressed: " + (" + ".join(names) if names else "none"))

    def show_completed_combo(self, events):
        value = format_combo(events)
        if value is not None:
            self.result.set(json.dumps(value))

        lines = [
            f"name={event.name!r:<20} scan_code={event.scan_code:<8} "
            f"type={event.event_type}"
            for event in events
        ]
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")

    def copy_result(self):
        value = self.result.get()
        if value and value != "Waiting for input...":
            self.root.clipboard_clear()
            self.root.clipboard_append(value)
            self.root.update_idletasks()

    def close(self):
        if self.hook is not None:
            keyboard.unhook(self.hook)
            self.hook = None
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = KeyComboFinder()
    app.run()


if __name__ == "__main__":
    main()
