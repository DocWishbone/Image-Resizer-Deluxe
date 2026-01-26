# =========================
# Dependency Check (MIT Nachfrage)
# =========================
import sys
import importlib
import subprocess
import os

REQUIRED = {
    "PIL": "Pillow",
    "tkinterdnd2": "tkinterdnd2",
}

def check_and_install():
    missing = []

    for module, package in REQUIRED.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)

    if not missing:
        return

    msg = (
        "Es fehlen folgende Python-Module:\n\n"
        + "\n".join(f"• {m}" for m in missing)
        + "\n\nSollen diese jetzt automatisch installiert werden?\n"
        + "(Internetverbindung erforderlich)"
    )

    try:
        from tkinter import Tk, messagebox
        root = Tk()
        root.withdraw()
        install = messagebox.askyesno("Fehlende Abhängigkeiten", msg)
    except Exception:
        print(msg)
        install = input("Installieren? [y/N]: ").strip().lower() == "y"

    if not install:
        sys.exit("Abbruch durch Benutzer.")

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", *missing]
    )

    try:
        messagebox.showinfo(
            "Fertig",
            "Abhängigkeiten wurden installiert.\nDas Programm wird neu gestartet."
        )
    except Exception:
        pass

    os.execl(sys.executable, sys.executable, *sys.argv)


check_and_install()

# =========================
# Imports
# =========================
from tkinter import (
    Frame, Label, Entry, Button, Listbox, Scrollbar,
    END, messagebox, filedialog, Toplevel
)
from PIL import Image
from tkinterdnd2 import TkinterDnD, DND_FILES

# =========================
# Preset-Farben
# =========================
PRESET_COLORS = [
    "#cfe9ff",
    "#a9d6ff",
    "#7fbfff",
    "#4da3ff",
]

# =========================
# Tooltip
# =========================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 15
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tip = tw = Toplevel(self.widget)
        tw.overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        Label(
            tw, text=self.text,
            background="#ffffe0",
            relief="solid", borderwidth=1,
            font=("Arial", 9),
            padx=6, pady=3
        ).pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# =========================
# App
# =========================
class ResizerApp:
    def __init__(self, root):
        self.root = root
        root.title("Bilder Resizer – Deluxe - m. ludwig 26.01.2026")
        root.minsize(380, 300)

        self.files = []

        # Eingaben
        top = Frame(root)
        top.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        Label(top, text="Max. Breite:").grid(row=0, column=0, sticky="w")
        self.width_entry = Entry(top, width=8)
        self.width_entry.insert(0, "1200")
        self.width_entry.grid(row=0, column=1, padx=(5, 20))

        Label(top, text="Max. Höhe:").grid(row=0, column=2, sticky="w")
        self.height_entry = Entry(top, width=8)
        self.height_entry.insert(0, "1200")
        self.height_entry.grid(row=0, column=3, padx=(5, 0))

        # Presets
        presets_frame = Frame(root)
        presets_frame.grid(row=1, column=0, padx=10, sticky="ew")

        presets = [
            ("Web", 1200, 1200, "Für Webseiten & CMS"),
            ("Mail", 800, 800, "Klein für E-Mail & Chat"),
            ("Social", 1080, 1080, "Instagram & Social Media"),
            ("Druck", 3000, 3000, "Hohe Auflösung für Print"),
        ]

        Label(presets_frame, text="Presets:").pack(side="left", padx=(0, 8))
        for (name, w, h, tip), color in zip(presets, PRESET_COLORS):
            b = Button(
                presets_frame,
                text=name,
                command=lambda w=w, h=h: self.set_preset(w, h),
                padx=10,
                background=color,
                activebackground=color,
                relief="raised",
                borderwidth=1,
            )
            b.pack(side="left", padx=3)
            b.bind("<Enter>", self.preset_hover_enter)
            b.bind("<Leave>", self.preset_hover_leave)
            ToolTip(b, tip)

        # Drag & Drop
        drop = Frame(root)
        drop.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.drop_label = Label(
            drop,
            text="📂 Dateien hier reinziehen (mehrere möglich)",
            relief="ridge", padx=10, pady=12
        )
        self.drop_label.pack(fill="x")

        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)

        # Dateiliste
        list_frame = Frame(root)
        list_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        root.rowconfigure(3, weight=1)

        self.listbox = Listbox(list_frame)
        sb = Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Buttons
        btns = Frame(root)
        btns.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        Button(btns, text="Bilder auswählen…", command=self.pick_files).pack(side="left")
        Button(btns, text="Liste leeren", command=self.clear_files).pack(side="left", padx=6)
        Button(btns, text="Verkleinern & speichern", command=self.resize).pack(side="right")

        self.status = Label(root, text="Bereit.", anchor="w")
        self.status.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")

    # -------- Helpers --------
    def preset_hover_enter(self, e):
        e.widget.config(relief="sunken")

    def preset_hover_leave(self, e):
        e.widget.config(relief="raised")

    def set_preset(self, w, h):
        self.width_entry.delete(0, END)
        self.height_entry.delete(0, END)
        self.width_entry.insert(0, str(w))
        self.height_entry.insert(0, str(h))
        self.status.config(text=f"Preset gesetzt: {w}×{h}")

    def normalize_drop(self, data):
        return [
            f for f in self.root.tk.splitlist(data)
            if os.path.isfile(f)
        ]

    def add_files(self, paths):
        added = 0
        for p in paths:
            p = os.path.abspath(p)
            if p not in self.files and p.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                self.files.append(p)
                self.listbox.insert(END, p)
                added += 1
        self.status.config(text=f"{added} hinzugefügt – Gesamt: {len(self.files)}")

    def on_drop(self, event):
        self.add_files(self.normalize_drop(event.data))

    def pick_files(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")]
        )
        self.add_files(paths)

    def clear_files(self):
        self.files.clear()
        self.listbox.delete(0, END)
        self.status.config(text="Liste geleert.")

    def resize(self):
        if not self.files:
            messagebox.showwarning("Hinweis", "Keine Dateien ausgewählt.")
            return

        try:
            w = int(self.width_entry.get())
            h = int(self.height_entry.get())
        except ValueError:
            messagebox.showerror("Fehler", "Ungültige Größe.")
            return

        out_dir = os.path.join(os.path.dirname(self.files[0]), "resized")
        os.makedirs(out_dir, exist_ok=True)

        ok = 0
        for f in self.files:
            try:
                with Image.open(f) as img:
                    img.thumbnail((w, h))
                    img.save(os.path.join(out_dir, os.path.basename(f)))
                ok += 1
                self.status.config(text=f"{ok}/{len(self.files)} verarbeitet…")
                self.root.update_idletasks()
            except Exception:
                pass

        messagebox.showinfo("Fertig", f"Gespeichert in:\n{out_dir}")
        self.status.config(text="Bereit.")

# =========================
# Start
# =========================
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ResizerApp(root)
    root.mainloop()
