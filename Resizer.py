import sys
import importlib
import subprocess

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
        return  # alles ok

    msg = (
        "Es fehlen folgende Python-Module:\n\n"
        + "\n".join(f"• {m}" for m in missing)
        + "\n\nSollen diese jetzt automatisch installiert werden?\n\n"
        + "(Internetverbindung erforderlich)"
    )

    # GUI-Dialog versuchen
    try:
        from tkinter import Tk, messagebox
        root = Tk()
        root.withdraw()
        install = messagebox.askyesno("Fehlende Abhängigkeiten", msg)
    except Exception:
        # Fallback Terminal
        print(msg)
        install = input("Installieren? [y/N]: ").strip().lower() == "y"

    if not install:
        sys.exit("Abbruch durch Benutzer.")

    # Installation
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", *missing]
        )
    except subprocess.CalledProcessError:
        try:
            messagebox.showerror(
                "Fehler",
                "Installation fehlgeschlagen.\nBitte manuell installieren."
            )
        except Exception:
            pass
        sys.exit(1)

    # Erfolg → Neustart
    try:
        messagebox.showinfo(
            "Fertig",
            "Abhängigkeiten wurden installiert.\nDas Programm wird neu gestartet."
        )
    except Exception:
        pass

    os.execl(sys.executable, sys.executable, *sys.argv)

# ---- HIER aufrufen ----
if __name__ == "__main__":
    import os
    check_and_install()


import os
from tkinter import (
    Tk, Frame, Label, Entry, Button, Listbox, Scrollbar, END, messagebox, Toplevel
)
from tkinter import filedialog
from PIL import Image

from tkinterdnd2 import TkinterDnD, DND_FILES


# ---------- Tooltip ----------
class ToolTip:
    def __init__(self, widget, text: str):
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
            tw,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9),
            padx=6,
            pady=3,
        ).pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

PRESET_COLORS = [
    "#cfe9ff",  # sehr hellblau
    "#a9d6ff",  # hellblau
    "#7fbfff",  # mittelblau
    "#4da3ff",  # dunkler
]

# ---------- App ----------
class ResizerApp:
    def __init__(self, root):
        self.root = root
        root.title("Bilder verkleinern (Deluxe) - mlu 26.01.2026")
        root.minsize(560, 420)

        self.files = []

        # Top inputs
        top = Frame(root)
        top.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)

        Label(top, text="Max. Breite:").grid(row=0, column=0, sticky="w")
        self.width_entry = Entry(top, width=10)
        self.width_entry.insert(0, "1200")
        self.width_entry.grid(row=0, column=1, sticky="w", padx=(6, 20))

        Label(top, text="Max. Höhe:").grid(row=0, column=2, sticky="w")
        self.height_entry = Entry(top, width=10)
        self.height_entry.insert(0, "1200")
        self.height_entry.grid(row=0, column=3, sticky="w", padx=(6, 0))

        # Presets
        presets_frame = Frame(root)
        presets_frame.grid(row=1, column=0, padx=10, sticky="ew")

        presets = [
            ("Web", 1200, 1200, "Für Webseiten & CMS (gut genug, nicht zu groß)"),
            ("Mail", 800, 800, "Klein für E-Mail/Chat (schnell, wenig MB)"),
            ("Social", 1080, 1080, "Instagram & Social Media (typische Kantenlänge)"),
            ("Druck", 3000, 3000, "Hohe Auflösung (eher für Print/Archiv)"),
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

            # Hover
            b.bind("<Enter>", self.preset_hover_enter)
            b.bind("<Leave>", self.preset_hover_leave)

            ToolTip(b, tip)

        # Drop area
        drop = Frame(root)
        drop.grid(row=2, column=0, padx=10, pady=(10, 6), sticky="ew")
        drop.columnconfigure(0, weight=1)

        self.drop_label = Label(
            drop,
            text="📂 Dateien hier reinziehen (mehrere gleichzeitig möglich)\n"
                 "Tipp: Shift/Ctrl markieren und zusammen droppen",
            relief="ridge",
            padx=10,
            pady=12
        )
        self.drop_label.grid(row=0, column=0, sticky="ew")

        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)

        # File list + scrollbar
        list_frame = Frame(root)
        list_frame.grid(row=3, column=0, padx=10, pady=6, sticky="nsew")
        root.rowconfigure(3, weight=1)
        root.columnconfigure(0, weight=1)

        self.listbox = Listbox(list_frame, height=10)
        sb = Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)

        self.listbox.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        # Buttons
        btns = Frame(root)
        btns.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        btns.columnconfigure(0, weight=1)

        Button(btns, text="Bilder auswählen…", command=self.pick_files).pack(side="left")
        Button(btns, text="Liste leeren", command=self.clear_files).pack(side="left", padx=8)
        Button(btns, text="Verkleinern & speichern", command=self.resize_and_save).pack(side="right")

        # Status
        self.status = Label(root, text="Bereit.", anchor="w")
        self.status.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")

    def set_status(self, text: str):
        self.status.config(text=text)
        self.root.update_idletasks()

    def set_preset(self, w: int, h: int):
        self.width_entry.delete(0, END)
        self.height_entry.delete(0, END)
        self.width_entry.insert(0, str(w))
        self.height_entry.insert(0, str(h))
        self.set_status(f"Preset gesetzt: {w}×{h}")
        
    def preset_hover_enter(self, event):
        event.widget.config(relief="sunken")

    def preset_hover_leave(self, event):
        event.widget.config(relief="raised")

    def normalize_dnd_files(self, data: str):
        """
        tkinterdnd2 liefert je nach OS z.B.:
          - "C:/a.jpg C:/b.jpg"
          - "{C:/my file.jpg} {C:/other.png}"
        splitlist kann das i.d.R. sauber.
        """
        files = self.root.tk.splitlist(data)
        # Optional: Ordner rausfiltern / erlauben? -> hier nur Dateien
        out = []
        for f in files:
            f = f.strip()
            if os.path.isfile(f):
                out.append(f)
        return out

    def add_files(self, paths):
        added = 0
        for p in paths:
            p = os.path.abspath(p)
            if p not in self.files:
                # einfache Filterung auf Bildendungen
                ext = os.path.splitext(p)[1].lower()
                if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    self.files.append(p)
                    self.listbox.insert(END, p)
                    added += 1
        self.set_status(f"{added} Datei(en) hinzugefügt. Gesamt: {len(self.files)}")

    def on_drop(self, event):
        paths = self.normalize_dnd_files(event.data)
        if not paths:
            self.set_status("Drop erkannt, aber keine gültigen Dateien gefunden.")
            return
        self.add_files(paths)

    def pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Bilder auswählen",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")]
        )
        if paths:
            self.add_files(paths)

    def clear_files(self):
        self.files.clear()
        self.listbox.delete(0, END)
        self.set_status("Liste geleert.")

    def resize_and_save(self):
        if not self.files:
            messagebox.showwarning("Hinweis", "Keine Dateien ausgewählt.")
            return

        try:
            max_w = int(self.width_entry.get())
            max_h = int(self.height_entry.get())
            if max_w <= 0 or max_h <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige positive Zahlen für Breite/Höhe eingeben.")
            return

        out_dir = os.path.join(os.path.dirname(self.files[0]), "resized")
        os.makedirs(out_dir, exist_ok=True)

        ok, fail = 0, 0
        for f in self.files:
            try:
                with Image.open(f) as img:
                    img.thumbnail((max_w, max_h))
                    out_path = os.path.join(out_dir, os.path.basename(f))
                    img.save(out_path)
                ok += 1
                self.set_status(f"Verarbeitet: {ok}/{len(self.files)}")
            except Exception:
                fail += 1

        messagebox.showinfo(
            "Fertig",
            f"Gespeichert in:\n{out_dir}\n\nOK: {ok}\nFehler: {fail}"
        )
        self.set_status("Bereit.")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ResizerApp(root)
    root.mainloop()
