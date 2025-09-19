
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# ---------------------------
# CONFIG: change these paths
# ---------------------------
ASSETS = {
    "background": "C:\\Users\\muska\\Downloads\\background.png",  # placeholder background image
    "logo": "C:\\Users\\muska\\Downloads\\logo.png",              # placeholder logo (top-left)
    "drug": "C:\\Users\\muska\\Downloads\\drug_inventory_image.png",              # image for Drug Inventory tile
    "sales": "C:\\Users\\muska\\Downloads\\Sales_image.png",            # image for Sales tile
    "stock": "C:\\Users\\muska\\Downloads\\Stock_image.png",            # image for Stock tile
    "patient": "C:\\Users\\muska\\Downloads\\Patient_image.png",        # image for Patient Data tile
}

SCRIPTS = {
    "Drug Inventory": "C:\\Users\\muska\\OneDrive\\Desktop\\Main_App_Drug_Inventory\\Drug_Inventory_UI_4.py",
    "Sales UI": "C:\\Users\\muska\\OneDrive\\Desktop\\Main_App_Drug_Inventory\\Sales_ui_4.py",
    "Stock UI": "C:\\Users\\muska\\OneDrive\\Desktop\\Main_App_Drug_Inventory\\Stock_ui_2.py",
    "Patient Data": "C:\\Users\\muska\\OneDrive\\Desktop\\Main_App_Drug_Inventory\\PAtient_Data_2.py",
}

# Aesthetic constants
TILE_BG = "#0f1724"       # dark tile background
TILE_HOVER = "#0b1220"    # hover background
TILE_TEXT = "#E6EEF3"     # tile text color
APP_BG = "#081225"        # fallback app bg if no image
LOGO_SIZE = (110, 110)    # desired logo nominal size


# ---------------------------
# Utility functions
# ---------------------------
def resource_path(path):
    """Return a path safe for PyInstaller or regular run."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, path)


def open_script(script_name):
    """
    Launch the given python script in a new process so each UI remains independent.
    Uses the same Python executable.
    """
    script_path = resource_path(script_name)
    if not os.path.exists(script_path):
        tk.messagebox.showerror("Script not found", f"Could not find: {script_path}")
        return
    try:
        # Use a non-blocking detached process
        subprocess.Popen([sys.executable, script_path], close_fds=True)
    except Exception as e:
        tk.messagebox.showerror("Launch failed", f"Failed to launch {script_name}:\n{e}")


# ---------------------------
# Tile widget
# ---------------------------
class Tile(ttk.Frame):
    def __init__(self, master, title, image_path, script, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title = title
        self.script = script
        self.image_path = resource_path(image_path)
        self.configure(style="Tile.TFrame")
        # keep references
        self._img_orig = self._load_image_or_placeholder(self.image_path)
        self._photo = None

        # create inner widgets
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, relief="flat")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=(14, 6))
        self.text_label = ttk.Label(self, text=title, style="TileLabel.TLabel", anchor="center", wraplength=220)
        self.text_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 18))

        # clickable area: bind all relevant widgets
        for w in (self, self.canvas, self.text_label):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        # layout expand
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def _load_image_or_placeholder(self, path):
        """Load image if exists else create a simple placeholder image."""
        try:
            img = Image.open(path).convert("RGBA")
        except Exception:
            # placeholder: colored rounded rectangle
            img = Image.new("RGBA", (400, 280), (45, 55, 72, 255))
        return img

    def resize_and_draw(self, width, height):
        """Resize internal image to fit width x height minus some padding and draw on canvas."""
        if width <= 10 or height <= 10:
            return
        # determine target size leaving space for text
        target_w = width - 24
        target_h = int(height * 0.65)
        if target_w <= 0 or target_h <= 0:
            return
        img = self._img_orig.copy()
        img_ratio = img.width / img.height
        tgt_ratio = target_w / target_h
        if img_ratio > tgt_ratio:
            # fit by width
            new_w = target_w
            new_h = max(1, int(target_w / img_ratio))
        else:
            new_h = target_h
            new_w = max(1, int(target_h * img_ratio))
        img = img.resize((new_w, new_h), Image.LANCZOS)
        # create rounded corners mask (optional)
        self._photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        # center it
        x = (width // 2)
        y = (target_h // 2) + 8
        self.canvas.create_image(x, y, image=self._photo)

    def _on_click(self, _ev=None):
        open_script(self.script)

    def _on_enter(self, _ev=None):
        self.configure(style="TileHover.TFrame")

    def _on_leave(self, _ev=None):
        self.configure(style="Tile.TFrame")


# ---------------------------
# Main App
# ---------------------------
class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Major: Tools Launcher")
        self.minsize(840, 520)

        # load background and logo
        self.bg_path = resource_path(ASSETS.get("background", ""))
        self.logo_path = resource_path(ASSETS.get("logo", ""))

        # main container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # background canvas (scales with window)
        self.bg_canvas = tk.Canvas(self, highlightthickness=0)
        self.bg_canvas.grid(row=0, column=0, sticky="nsew")
        self.bg_img_orig = self._load_bg_image(self.bg_path)
        self.bg_photo = None

        # a semi-transparent overlay frame to hold content (so text readable)
        self.content_frame = ttk.Frame(self.bg_canvas, style="Content.TFrame")
        self.content_window = self.bg_canvas.create_window(
            0, 0, anchor="nw", window=self.content_frame
        )

        # top bar: logo + app title + optional small description
        self._build_topbar(self.content_frame)

        # tile area
        self.tile_container = ttk.Frame(self.content_frame, style="Content.TFrame")
        self.tile_container.grid(row=1, column=0, sticky="nsew", padx=28, pady=(12, 28))
        self.tile_container.grid_rowconfigure(0, weight=1)
        self.tile_container.grid_columnconfigure(0, weight=1)
        self.tile_container.grid_columnconfigure(1, weight=1)

        # create tiles
        self.tiles = []
        # Order them in a 2x2 grid
        items = list(SCRIPTS.items())  # (title, script)
        keys = list(SCRIPTS.keys())
        images_map = {
            "Drug Inventory": ASSETS.get("drug"),
            "Sales UI": ASSETS.get("sales"),
            "Stock UI": ASSETS.get("stock"),
            "Patient Data": ASSETS.get("patient"),
        }
        idx = 0
        for r in range(2):
            for c in range(2):
                if idx >= len(items):
                    break
                title = items[idx][0]
                script = items[idx][1]
                img_path = images_map.get(title, "")
                tile = Tile(self.tile_container, title, img_path, script, style="Tile.TFrame")
                tile.grid(row=r, column=c, sticky="nsew", padx=12, pady=12)
                self.tile_container.grid_rowconfigure(r, weight=1)
                self.tile_container.grid_columnconfigure(c, weight=1)
                self.tiles.append(tile)
                idx += 1

        # footer / small instruction
        footer = ttk.Label(self.content_frame, text="Click a card to open the corresponding UI (each opens separately).",
                           style="Footer.TLabel")
        footer.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 18))

        # content_frame expand config
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # bind resize
        self.bind("<Configure>", self._on_configure)

        # apply styles
        self._setup_styles()

        # initial layout pass
        self.update_idletasks()
        self._on_configure()

    def _build_topbar(self, parent):
        top = ttk.Frame(parent, style="Topbar.TFrame")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=18)
        top.grid_columnconfigure(2, weight=1)
        # logo
        logo_img = self._load_logo_image(self.logo_path)
        self.logo_photo = ImageTk.PhotoImage(logo_img)
        logo_lbl = ttk.Label(top, image=self.logo_photo, background="")
        logo_lbl.grid(row=0, column=0, sticky="w", padx=(0, 12))
        # title and subtitle
        title = ttk.Label(top, text="Major Control Panel", style="Title.TLabel")
        title.grid(row=0, column=1, sticky="w")
        subtitle = ttk.Label(top, text="Unified launcher for your GUIs — responsive & elegant", style="Subtitle.TLabel")
        subtitle.grid(row=0, column=2, sticky="w", padx=(10, 0))

    def _load_logo_image(self, path):
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail(LOGO_SIZE, Image.LANCZOS)
        except Exception:
            # fallback: create a simple circle-like placeholder
            img = Image.new("RGBA", LOGO_SIZE, (0, 0, 0, 0))
            # draw a simple filled rectangle
            placeholder = Image.new("RGBA", LOGO_SIZE, (14, 165, 233, 255))
            img.paste(placeholder)
        return img

    def _load_bg_image(self, path):
        try:
            img = Image.open(path).convert("RGBA")
        except Exception:
            img = None
        return img

    def _setup_styles(self):
        style = ttk.Style(self)
        # Basic theme tweak
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Tile.TFrame", background=TILE_BG, relief="flat")
        style.configure("TileHover.TFrame", background=TILE_HOVER, relief="flat")
        style.configure("TileLabel.TLabel", background=TILE_BG, foreground=TILE_TEXT, font=("Segoe UI", 13, "bold"))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#FFFFFF", background="")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#D8E6F3", background="")
        style.configure("Footer.TLabel", font=("Segoe UI", 9), foreground="#B8C9D8", background="")
        style.configure("Content.TFrame", background="", relief="flat")
        style.configure("Topbar.TFrame", background="", relief="flat")

        # give canvas a default background if no bg image
        self.bg_canvas.configure(background=APP_BG)

    def _on_configure(self, event=None):
        # adjust background to window size
        w = self.winfo_width()
        h = self.winfo_height()
        if self.bg_img_orig:
            # produce a scaled bg image that fills the window (cover)
            img = self.bg_img_orig.copy()
            img_ratio = img.width / img.height
            win_ratio = max(0.001, w / max(1, h))
            if img_ratio > win_ratio:
                # bg is wider than window -> fit by height
                new_h = h
                new_w = int(img_ratio * new_h)
            else:
                new_w = w
                new_h = int(new_w / img_ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            # crop center
            left = max(0, (new_w - w) // 2)
            top = max(0, (new_h - h) // 2)
            img = img.crop((left, top, left + w, top + h))
            self.bg_photo = ImageTk.PhotoImage(img)
            self.bg_canvas.delete("bg_image")
            self.bg_canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="bg_image")
        else:
            # fallback color already set
            pass

        # reposition content window and size it to leave margins
        margin_x = max(20, int(w * 0.03))
        margin_y = max(16, int(h * 0.03))
        content_w = max(600, w - 2 * margin_x)
        content_h = max(380, h - 2 * margin_y)
        self.bg_canvas.coords(self.content_window, margin_x, margin_y)
        self.bg_canvas.itemconfig(self.content_window, width=content_w, height=content_h)

        # cascade resize to tiles so they update their internal images
        # compute each tile size as roughly half available content area
        # find each tile widget's actual size and call resize_and_draw
        self.update_idletasks()
        for tile in self.tiles:
            tw = tile.winfo_width() or (content_w // 2 - 40)
            th = tile.winfo_height() or (content_h // 2 - 40)
            tile.resize_and_draw(tw, th)


# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
