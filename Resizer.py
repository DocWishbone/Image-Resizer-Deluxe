import sys
import importlib
import subprocess
import json
import os
from tkinter import (
    Tk, Frame, Label, Entry, Button, Listbox, Scrollbar, END, messagebox, Toplevel, StringVar, OptionMenu
)
from tkinter import filedialog
from PIL import Image
from tkinterdnd2 import TkinterDnD, DND_FILES

try:
    from .version import __version__
    from .version import __author__
except (ImportError, ValueError):
    from version import __version__
    from version import __author__

# ---------- Abhängigkeiten prüfen ----------
REQUIRED = {
    "PIL": "Pillow",
    "tkinterdnd2": "tkinterdnd2",
}

APP_VERSION = __version__
APP_AUTHOR = __author__

def check_and_install():
    missing = []
    for module, package in REQUIRED.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
    if not missing:
        return

    msg = "Es fehlen folgende Python-Module:\n\n" + "\n".join(f"• {m}" for m in missing) + \
          "\n\nSollen diese jetzt automatisch installiert werden?\n(Internetverbindung erforderlich)"
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

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    except subprocess.CalledProcessError:
        try:
            messagebox.showerror("Fehler", "Installation fehlgeschlagen.\nBitte manuell installieren.")
        except Exception:
            pass
        sys.exit(1)

    try:
        messagebox.showinfo("Fertig", "Abhängigkeiten wurden installiert.\nDas Programm wird neu gestartet.")
    except Exception:
        pass

    os.execl(sys.executable, sys.executable, *sys.argv)

check_and_install()

# ---------- Strings ----------
STRINGS = {
    "de": {
        "title": f"Bilder verkleinern – Deluxe v{APP_VERSION} - {APP_AUTHOR}",
        "presets": "Presets:",
        "preset_names": ["Web", "Mail", "Social", "Druck"],
        "max_width": "Max. Breite:",
        "max_height": "Max. Höhe:",
        "drop_text": "📂 Dateien hier reinziehen (mehrere möglich)",
        "btn_pick": "Bilder auswählen…",
        "btn_clear": "Liste leeren",
        "btn_resize": "Verkleinern & speichern",
        "status_ready": "Bereit.",
        "preset_set": "Preset gesetzt: {w}×{h}",
        "tips": [
            "Für Webseiten & CMS (gut genug, nicht zu groß)",
            "Klein für E-Mail/Chat (schnell, wenig MB)",
            "Instagram & Social Media (typische Kantenlänge)",
            "Hohe Auflösung (eher für Print/Archiv)"
        ]
    },
    "en": {
        "title": f"Image Resizer – Deluxe v{APP_VERSION} - v{APP_AUTHOR}",
        "presets": "Presets:",
        "preset_names": ["Web", "Mail", "Social", "Print"],
        "max_width": "Max width:",
        "max_height": "Max height:",
        "drop_text": "📂 Drop files here (multiple allowed)",
        "btn_pick": "Select images…",
        "btn_clear": "Clear list",
        "btn_resize": "Resize & save",
        "status_ready": "Ready.",
        "preset_set": "Preset set: {w}×{h}",
        "tips": [
            "For websites & CMS",
            "Small for Email/Chat",
            "Instagram & Social Media",
            "High resolution (Print/Archive)"
        ]
    },
    "ru": {
        "title": f"Изменение размера изображений – Deluxe v{APP_VERSION} - {APP_AUTHOR}",
        "presets": "Пресеты:",
        "preset_names": ["Веб", "Почта", "Соцсети", "Печать"],
        "max_width": "Макс. ширина:",
        "max_height": "Макс. высота:",
        "drop_text": "📂 Перетащите файлы сюда (можно несколько)",
        "btn_pick": "Выбрать изображения…",
        "btn_clear": "Очистить список",
        "btn_resize": "Уменьшить и сохранить",
        "status_ready": "Готово.",
        "preset_set": "Пресет установлен: {w}×{h}",
        "tips": [
            "Для веб-сайтов и CMS",
            "Маленький для почты/чата",
            "Instagram и соцсети",
            "Высокое разрешение (печать)"
        ]
    }
}

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# ---------- Tooltip ----------
class ToolTip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def update_text(self, new_text):
        self.text = new_text

    def show(self, _=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 15
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tip = tw = Toplevel(self.widget)
        tw.overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        Label(tw, text=self.text, background="#ffffe0", relief="solid", borderwidth=1,
              font=("Arial", 9), padx=6, pady=3).pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# ---------- Preset Farben ----------
PRESET_COLORS = [
    "#cfe9ff",
    "#a9d6ff",
    "#7fbfff",
    "#4da3ff",
]

# ---------- Sprachoptionen ----------
LANG_OPTIONS = {
    "DE": "de",
    "EN": "en",
    "RU": "ru",
}

# ---------- App ----------
class ResizerApp:
    def __init__(self, root):
        cfg = load_config()
        self.lang = StringVar(value=cfg.get("language", "de"))
        self.root = root
        root.minsize(560, 420)
        self.files = []
        self.tooltips =[]

        # Top Inputs
        top = Frame(root)
        top.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)

        # Breite / Höhe Labels + Entry
        self.lbl_width = Label(top)
        self.lbl_width.grid(row=0, column=0, sticky="w")
        self.width_entry = Entry(top, width=10)
        self.width_entry.insert(0, "1200")
        self.width_entry.grid(row=0, column=1, sticky="w", padx=(6,20))

        self.lbl_height = Label(top)
        self.lbl_height.grid(row=0, column=2, sticky="w")
        self.height_entry = Entry(top, width=10)
        self.height_entry.insert(0, "1200")
        self.height_entry.grid(row=0, column=3, sticky="w", padx=(6,0))

        # --- Sprache Dropdown (nur Text) ---
        current_flag = next(flag for flag, code in LANG_OPTIONS.items() if code == self.lang.get())
        self.flag_var = StringVar(value=current_flag)

        lang_menu = OptionMenu(top, self.flag_var, *LANG_OPTIONS.keys(), command=self.change_language)
        lang_menu.grid(row=0, column=4, padx=(15,0))
        lang_menu.config(font=("Arial", 10, "bold"))  # große Schrift für Text-Flags

        self.preset_buttons = []

        # ---------- Presets ----------
        presets_frame = Frame(root)
        presets_frame.grid(row=1, column=0, padx=10, sticky="ew")

        self.lbl_presets = Label(presets_frame)
        self.lbl_presets.pack(side="left", padx=(0,8))

        # Preset-Werte: Breite, Höhe, Tooltip
        preset_values = [
            (1200, 1200),
            (800, 800),
            (1080, 1080),
            (3000, 3000),
        ]

        # Preset-Buttons erzeugen
        self.preset_buttons = []
        for i, ((w, h), color) in enumerate(zip(preset_values, PRESET_COLORS)):
            b = Button(
                presets_frame,
                text="", # durch apply-language
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
                   
            tip_obj = ToolTip(b, "") 
            self.tooltips.append(tip_obj)
            self.preset_buttons.append(b)

        # Drop Area
        drop = Frame(root)
        drop.grid(row=2, column=0, padx=10, pady=(10,6), sticky="ew")
        drop.columnconfigure(0, weight=1)
        self.drop_label = Label(drop, relief="ridge", padx=10, pady=12)
        self.drop_label.grid(row=0, column=0, sticky="ew")
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)

        # File List + Scrollbar
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
        self.btn_pick = Button(btns, command=self.pick_files)
        self.btn_pick.pack(side="left")
        self.btn_clear = Button(btns, command=self.clear_files)
        self.btn_clear.pack(side="left", padx=8)
        self.btn_resize = Button(btns, command=self.resize_and_save)
        self.btn_resize.pack(side="right")

        # Status
        self.status = Label(root, anchor="w")
        self.status.grid(row=5, column=0, padx=10, pady=(0,10), sticky="ew")

        # Sprache anwenden
        self.apply_language()
        save_config({"language": self.lang.get()})

    # --- Methoden ---
    def change_language(self, selected_flag):
        code = LANG_OPTIONS[selected_flag]
        self.lang.set(code)
        self.apply_language()
        save_config({"language": code})

    def apply_language(self):
        t = STRINGS[self.lang.get()]
        self.root.title(t["title"])
        self.lbl_width.config(text=t["max_width"])
        self.lbl_height.config(text=t["max_height"])
        self.lbl_presets.config(text=t["presets"])
        self.drop_label.config(text=t["drop_text"])
        self.btn_pick.config(text=t["btn_pick"])
        self.btn_clear.config(text=t["btn_clear"])
        self.btn_resize.config(text=t["btn_resize"])
        self.status.config(text=t["status_ready"])
        
        # Namen der Buttons aktualisieren
        for b, name in zip(self.preset_buttons, t["preset_names"]):
            b.config(text=name)

        # Tooltips aktualisieren
        if hasattr(self, 'tooltips'):
            for tip_obj, new_text in zip(self.tooltips, t["tips"]):
                tip_obj.update_text(new_text)

    def set_status(self, text: str):
        self.status.config(text=text)
        self.root.update_idletasks()

    def set_preset(self, w: int, h: int):
        self.width_entry.delete(0, END)
        self.height_entry.delete(0, END)
        self.width_entry.insert(0, str(w))
        self.height_entry.insert(0, str(h))
        t = STRINGS[self.lang.get()]
        self.set_status(t["preset_set"].format(w=w, h=h))

    def preset_hover_enter(self, event):
        event.widget.config(relief="sunken")

    def preset_hover_leave(self, event):
        event.widget.config(relief="raised")

    def normalize_dnd_files(self, data: str):
        files = self.root.tk.splitlist(data)
        return [f.strip() for f in files if os.path.isfile(f.strip())]

    def add_files(self, paths):
        added = 0
        for p in paths:
            p = os.path.abspath(p)
            if p not in self.files:
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
        paths = filedialog.askopenfilenames(title="Bilder auswählen", filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
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
                    img.save(os.path.join(out_dir, os.path.basename(f)))
                ok += 1
                self.set_status(f"Verarbeitet: {ok}/{len(self.files)}")
            except Exception:
                fail += 1
        messagebox.showinfo("Fertig", f"Gespeichert in:\n{out_dir}\n\nOK: {ok}\nFehler: {fail}")
        self.set_status("Bereit.")

# ---------- Main ----------
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ResizerApp(root)
    root.mainloop()
