import sys
import importlib
import subprocess
import json
import os

def get_version():
    try:
        # Falls es als EXE läuft, nehmen wir den Dateinamen (z.B. Image_Resizer_v1.4.0.exe)
        exe_name = os.path.basename(sys.executable)
        if "v" in exe_name:
            # Extrahiert alles nach dem 'v'
            return exe_name.split("_v")[-1].replace(".exe", "")
    except:
        pass
    return "DEVELOPER-EDITION" # Fallback, falls man das Skript direkt in Python startet

APP_VERSION = get_version()
APP_AUTHOR = "m. ludwig"

REQUIRED = {
    "PIL": "Pillow",
    "tkinterdnd2": "tkinterdnd2",
}

def check_and_install():
    if getattr(sys, 'frozen', False):
        return

    missing = []
    for module, package in REQUIRED.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
            
    if not missing:
        return

    try:
        from tkinter import Tk, messagebox, Label, Toplevel
        root = Tk()
        root.withdraw()
        
        msg = ("Es fehlen folgende Module:\n\n" + 
               "\n".join(f"• {m}" for m in missing) + 
               "\n\nSollen diese jetzt automatisch installiert werden?")
        
        if not messagebox.askyesno("Installation erforderlich", msg):
            sys.exit()

        # Lade-Fenster
        loading = Toplevel(root)
        loading.title("Bitte warten...")
        loading.geometry("300x100")
        # Zentrieren
        x = (root.winfo_screenwidth() // 2) - 150
        y = (root.winfo_screenheight() // 2) - 50
        loading.geometry(f"+{x}+{y}")
        
        Label(loading, text="\nInstalliere Abhängigkeiten...", font=("Arial", 10, "bold")).pack()
        Label(loading, text="Dies kann einen Moment dauern...").pack()
        loading.update()

        # Installation via Pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        
        loading.destroy()
        root.destroy()

        # Neustart FIX: Wir nutzen spawnl statt execl, um Pfadprobleme mit Leerzeichen zu umgehen
        os.spawnl(os.P_WAIT, sys.executable, f'"{sys.executable}"', *sys.argv)
        sys.exit()
        
    except Exception as e:
        print(f"Fehler: {e}")
        sys.exit(1)

check_and_install()

from tkinter import (
    Tk, Frame, Label, Entry, Button, Listbox, Scrollbar, END, 
    messagebox, Toplevel, StringVar, OptionMenu, Radiobutton # Radiobutton hinzugefügt
)
from tkinter import filedialog
from PIL import Image
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk, ImageOps

# ---------- Strings ----------
STRINGS = {
    "de": {
        "title": f"Bilder verkleinern – Deluxe v{APP_VERSION} - {APP_AUTHOR}",
        "presets": "Presets:",
        "preset_names": ["Mail", "Social", "Web", "Druck"],
        "max_width": "Max. Breite:",
        "max_height": "Max. Höhe:",
        "mode_resize": "Bilder verkleinern",
        "mode_ico": "ICO erstellen (Multi-Size)",
        "drop_text": "📂 Dateien hier reinziehen (mehrere möglich)",
        "btn_pick": "Bilder auswählen…",
        "btn_clear": "Liste leeren",
        "btn_resize": "Verkleinern & speichern",
        "btn_ico": "Icons erstellen",
        "status_ready": "Bereit.",
        "preset_set": "Preset gesetzt: {w}×{h}",
        "tips": [
            "Klein für E-Mail/Chat (schnell, wenig MB)",
            "Instagram & Social Media (typische Kantenlänge)",
            "Für Webseiten & CMS (gut genug, nicht zu groß)",
            "Hohe Auflösung (eher für Print/Archiv)"
        ]
    },
    "en": {
        "title": f"Image Resizer – Deluxe v{APP_VERSION} - {APP_AUTHOR}",
        "presets": "Presets:",
        "preset_names": ["Mail", "Social", "Web", "Print"],
        "max_width": "Max width:",
        "max_height": "Max height:",
        "mode_resize": "Resize images",
        "mode_ico": "Create ICO (Multi-Size)",
        "drop_text": "📂 Drop files here (multiple allowed)",
        "btn_pick": "Select images…",
        "btn_clear": "Clear list",
        "btn_resize": "Resize & save",
        "btn_ico": "Create Icons",
        "status_ready": "Ready.",
        "preset_set": "Preset set: {w}×{h}",
        "tips": [
            "Small for Email/Chat",
            "Instagram & Social Media",
            "For websites & CMS",
            "High resolution (Print/Archive)"
        ]
    },
    "ru": {
        "title": f"Изменение размера изображений – Deluxe v{APP_VERSION} - {APP_AUTHOR}",
        "presets": "Пресеты:",
        "preset_names": ["Почта", "Соцсети", "Веб", "Печать"],
        "max_width": "Макс. ширина:",
        "max_height": "Макс. высота:",
        "mode_resize": "Изменить размер",
        "mode_ico": "Создать ICO",
        "drop_text": "📂 Перетащите файлы сюда",
        "btn_pick": "Выбрать изображения…",
        "btn_clear": "Очистить список",
        "btn_resize": "Изменить и сохранить",
        "btn_ico": "Создать иконки",
        "status_ready": "Готово.",
        "preset_set": "Пресет установлен: {w}×{h}",
        "tips": [
            "Маленький для почты",
            "Соцсети (Instagram и др.)",
            "Для веб-сайтов",
            "Высокое качество (печать)"
        ]
    },
    "es": {
        "title": f"Redimensionar imágenes – Deluxe v{APP_VERSION} - {APP_AUTHOR}",
        "presets": "Ajustes:",
        "preset_names": ["Correo", "Social", "Web", "Imprimir"],
        "max_width": "Ancho máx:",
        "max_height": "Alto máx:",
        "mode_resize": "Redimensionar",
        "mode_ico": "Crear ICO",
        "drop_text": "📂 Suelte los archivos aquí",
        "btn_pick": "Seleccionar imágenes…",
        "btn_clear": "Limpiar lista",
        "btn_resize": "Redimensionar y guardar",
        "btn_ico": "Crear iconos",
        "status_ready": "Listo.",
        "preset_set": "Ajuste establecido: {w}×{h}",
        "tips": [
            "Pequeño para correo",
            "Redes sociales",
            "Sitios web",
            "Alta resolución"
        ]
    },
    "fr": {
        "title": f"Redimensionner les images – Deluxe v{APP_VERSION} - {APP_AUTHOR}",
        "presets": "Préréglages :",
        "preset_names": ["E-mail", "Social", "Web", "Imprimer"],
        "max_width": "Largeur max :",
        "max_height": "Hauteur max :",
        "mode_resize": "Redimensionner",
        "mode_ico": "Créer ICO",
        "drop_text": "📂 Déposez les fichiers ici",
        "btn_pick": "Sélectionner des images…",
        "btn_clear": "Effacer la liste",
        "btn_resize": "Redimensionner et sauver",
        "btn_ico": "Créer des icônes",
        "status_ready": "Prêt.",
        "preset_set": "Préréglage défini : {w}×{h}",
        "tips": [
            "Petit pour email",
            "Réseaux sociaux",
            "Sites web",
            "Haute résolution"
        ]
    },
    "it": {
        "title": f"Ridimensiona immagini – Deluxe v{APP_VERSION} - {APP_AUTHOR}",
        "presets": "Predefiniti:",
        "preset_names": ["Email", "Social", "Web", "Stampa"],
        "max_width": "Larghezza max:",
        "max_height": "Altezza max:",
        "mode_resize": "Ridimensiona",
        "mode_ico": "Crea ICO",
        "drop_text": "📂 Trascina i file qui",
        "btn_pick": "Seleziona immagini…",
        "btn_clear": "Svuota lista",
        "btn_resize": "Ridimensiona e salva",
        "btn_ico": "Crea icone",
        "status_ready": "Pronto.",
        "preset_set": "Predefinito impostato: {w}×{h}",
        "tips": [
            "Piccolo per email",
            "Social media",
            "Siti web",
            "Alta risoluzione"
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
    "ES": "es",
    "FR": "fr",
    "IT": "it",
}
        
# ---------- App ----------
class ResizerApp:
    def __init__(self, root):
        cfg = load_config()
        self.lang = StringVar(value=cfg.get("language", "de"))
        self.root = root
        root.geometry("500x500") # Breite angepasst
        root.minsize(600, 450)
        self.files = []
        self.tooltips = []
        self.mode = StringVar(value="resize") # Modus-Variable

        # --- Modus Umschalter ---
        mode_frame = Frame(self.root)
        mode_frame.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")
        
        # In der __init__
        self.rb_resize = Radiobutton(mode_frame, text="", variable=self.mode, 
                                    value="resize", font=("Arial", 10), 
                                    command=self.update_button_text) # Command hinzugefügt
        self.rb_resize.pack(side="left", padx=10)

        self.rb_ico = Radiobutton(mode_frame, text="", variable=self.mode, 
                                 value="ico", font=("Arial", 10), 
                                 command=self.update_button_text) # Command hinzugefügt
        self.rb_ico.pack(side="left", padx=10)

        # Top Inputs
        top = Frame(root)
        top.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
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

        # --- Sprache Dropdown ---
        current_flag = next(flag for flag, code in LANG_OPTIONS.items() if code == self.lang.get())
        self.flag_var = StringVar(value=current_flag)

        lang_menu = OptionMenu(top, self.flag_var, *LANG_OPTIONS.keys(), command=self.change_language)
        lang_menu.grid(row=0, column=4, padx=(15,0))
        lang_menu.config(font=("Arial", 10, "bold"))

        self.preset_buttons = []

        # ---------- Presets ----------
        self.presets_frame = Frame(root)
        self.presets_frame.grid(row=2, column=0, padx=10, sticky="ew")

        self.lbl_presets = Label(self.presets_frame)
        self.lbl_presets.pack(side="left", padx=(0,8))

        preset_values = [(800, 800), (1080, 1080), (1200, 1200), (3000, 3000)]

        self.preset_buttons = []
        for i, ((w, h), color) in enumerate(zip(preset_values, PRESET_COLORS)):
            b = Button(
                self.presets_frame,
                text="", 
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
        drop.grid(row=3, column=0, padx=10, pady=(10,6), sticky="ew")
        drop.columnconfigure(0, weight=1)
        self.drop_label = Label(drop, relief="ridge", padx=10, pady=12)
        self.drop_label.grid(row=0, column=0, sticky="ew")
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)

        # File List + Scrollbar
        list_frame = Frame(root)
        list_frame.grid(row=4, column=0, padx=10, pady=6, sticky="nsew")
        root.rowconfigure(4, weight=1)
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
        btns.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        btns.columnconfigure(0, weight=1)
        self.btn_pick = Button(btns, command=self.pick_files)
        self.btn_pick.pack(side="left")
        self.btn_clear = Button(btns, command=self.clear_files)
        self.btn_clear.pack(side="left", padx=8)
        self.btn_resize = Button(
            btns, 
            command=self.start_process, 
            bg="#28a745",    # Ein schönes "Erfolgs-Grün"
            fg="white",      # Weiße Schrift für besseren Kontrast
            font=("Arial", 10, "bold") # Etwas dicker, damit er auffällt
        )
        self.btn_resize.pack(side="right")

        # Status
        self.status = Label(root, anchor="w")
        self.status.grid(row=6, column=0, padx=10, pady=(0,10), sticky="ew")

        # Sprache anwenden
        self.apply_language()
        save_config({"language": self.lang.get()})

    # --- Methoden ---
    def start_process(self): # NEU: Weiche für Button-Klick
        if self.mode.get() == "resize":
            self.resize_and_save()
        else:
            self.convert_to_ico(self.files)

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
        self.status.config(text=t["status_ready"])
        
        # Radiobuttons übersetzen
        self.rb_resize.config(text=t["mode_resize"])
        self.rb_ico.config(text=t["mode_ico"])
        
        # Button-Text je nach Modus setzen
        self.update_button_text() 
        
        for b, name in zip(self.preset_buttons, t["preset_names"]):
            b.config(text=name)

        if hasattr(self, 'tooltips'):
            for tip_obj, new_text in zip(self.tooltips, t["tips"]):
                tip_obj.update_text(new_text)

    def update_button_text(self):
        t = STRINGS[self.lang.get()]
        if self.mode.get() == "resize":
            self.btn_resize.config(text=t["btn_resize"])
            # Presets und Eingabefelder aktivieren
            self.presets_frame.grid() 
            self.width_entry.config(state="normal")
            self.height_entry.config(state="normal")
        else:
            self.btn_resize.config(text=t["btn_ico"])
            # Presets verstecken und Eingabefelder ausgrauen
            self.presets_frame.grid_remove() 
            self.width_entry.config(state="disabled")
            self.height_entry.config(state="disabled")

    def convert_to_ico(self, file_paths): # NEU: ICO Logik
        if not file_paths:
            messagebox.showwarning("Hinweis", "Keine Dateien ausgewählt.")
            return
        out_dir = os.path.join(os.path.dirname(file_paths[0]), "converted_icons")
        os.makedirs(out_dir, exist_ok=True)
        ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        ok, fail = 0, 0
        for path in file_paths:
            try:
                with Image.open(path) as img:
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    base_name = os.path.splitext(os.path.basename(path))[0]
                    output_path = os.path.join(out_dir, f"{base_name}.ico")
                    img.save(output_path, format='ICO', sizes=ico_sizes)
                    ok += 1
            except: fail += 1
        messagebox.showinfo("Fertig", f"Icons erstellt: {ok}\nFehler: {fail}")
        os.startfile(out_dir)

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
        return [f.strip('{}') for f in files] # {} Fix für Pfade mit Leerzeichen

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
        
        if self.mode.get() == "ico": # Direkt-Modus für ICO bei Drop
            self.convert_to_ico(paths)
        else:
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
                img = Image.open(f)
                img = ImageOps.exif_transpose(img)
                img.thumbnail((max_w, max_h))
                output_path = os.path.join(out_dir, os.path.basename(f))
                img.save(output_path, quality=95, subsampling=0, optimize=True)
                img.close()
                ok += 1
                self.set_status(f"Verarbeitet: {ok}/{len(self.files)}")
            except Exception as e:
                fail += 1
        messagebox.showinfo("Fertig", f"Gespeichert in:\n{out_dir}\n\nOK: {ok}\nFehler: {fail}")
        os.startfile(out_dir)
        self.set_status("Bereit.")

# ---------- Main ----------
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ResizerApp(root)
    root.mainloop()