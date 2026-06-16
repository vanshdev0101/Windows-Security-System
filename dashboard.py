"""
Laptop Guard — Glassmorphism Dashboard v2
Modern dark glass UI with photo grid, live log streaming, OTP ticker.
Run without Administrator privileges.
"""

import tkinter as tk
from tkinter import messagebox, font as tkfont
import os, glob, datetime, subprocess, threading, time, winreg
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageFont
import pyotp
from dotenv import load_dotenv

load_dotenv()
SAVE_FOLDER = os.getenv("SAVE_FOLDER", r"C:\IntruderPhotos")
TOTP_SECRET = os.getenv("TOTP_SECRET", "")
LOG_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guard.log")

# ── Palette ────────────────────────────────────────────────────────────────────
BG_DEEP   = "#080c14"   # near-black navy base
BG_GLASS  = "#0d1520"   # card base
BORDER    = "#1e3a5f"   # glass border blue
GLOW_B    = "#0ea5e9"   # sky-blue accent
GLOW_G    = "#10b981"   # emerald accent
GLOW_R    = "#ef4444"   # red alert
GLOW_Y    = "#f59e0b"   # amber warning
FG        = "#e2e8f0"
FG2       = "#64748b"
FG3       = "#94a3b8"
FONT_UI   = ("Segoe UI", 10)
FONT_B    = ("Segoe UI", 10, "bold")
FONT_H    = ("Segoe UI", 13, "bold")
FONT_MONO = ("Consolas",  9)
FONT_BIG  = ("Segoe UI", 30, "bold")
FONT_MED  = ("Segoe UI", 18, "bold")


def make_gradient_bg(w, h):
    """Generate a deep navy-to-black gradient image for the background."""
    img = Image.new("RGB", (w, h), BG_DEEP)
    draw = ImageDraw.Draw(img)
    # subtle radial glow top-left
    for r in range(300, 0, -1):
        alpha = int(18 * (1 - r / 300))
        col = (0, int(alpha * 0.6), int(alpha * 1.2))
        draw.ellipse((-r + 100, -r + 80, r + 100, r + 80), fill=col)
    # subtle glow bottom-right
    for r in range(250, 0, -1):
        alpha = int(12 * (1 - r / 250))
        col = (0, int(alpha * 0.8), int(alpha * 0.4))
        draw.ellipse((w - r - 50, h - r - 50, w + r - 50, h + r - 50), fill=col)
    return img


def glass_frame(parent, **kw):
    """A frame styled as a glass card."""
    f = tk.Frame(parent, bg=BG_GLASS,
                 highlightbackground=BORDER,
                 highlightthickness=1,
                 **kw)
    return f


class OTPRing(tk.Canvas):
    """Circular countdown ring for OTP."""
    def __init__(self, parent, size=110, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=BG_GLASS, highlightthickness=0, **kw)
        self.size = size
        self.otp_text  = "------"
        self.remaining = 30
        self._draw()

    def update_otp(self, otp, remaining):
        self.otp_text  = otp
        self.remaining = remaining
        self._draw()

    def _draw(self):
        self.delete("all")
        s, pad = self.size, 10
        # background ring
        self.create_oval(pad, pad, s - pad, s - pad,
                         outline=BORDER, width=6, fill=BG_GLASS)
        # progress arc
        frac  = self.remaining / 30
        color = GLOW_G if frac > 0.4 else (GLOW_Y if frac > 0.15 else GLOW_R)
        extent = frac * 359.9
        self.create_arc(pad, pad, s - pad, s - pad,
                        start=90, extent=-extent,
                        outline=color, width=6, style="arc")
        # OTP digits
        self.create_text(s // 2, s // 2 - 8, text=self.otp_text,
                         fill=FG, font=("Consolas", 14, "bold"), anchor="center")
        self.create_text(s // 2, s // 2 + 14, text=f"{self.remaining}s",
                         fill=FG2, font=("Segoe UI", 8), anchor="center")


class PhotoThumb(tk.Frame):
    """Single clickable photo thumbnail card."""
    def __init__(self, parent, path, on_click, **kw):
        super().__init__(parent, bg=BG_GLASS,
                         highlightbackground=BORDER,
                         highlightthickness=1,
                         cursor="hand2", **kw)
        self.path = path
        self._img_ref = None

        try:
            img = Image.open(path)
            img.thumbnail((140, 90))
            self._img_ref = ImageTk.PhotoImage(img)
            lbl = tk.Label(self, image=self._img_ref, bg=BG_GLASS)
        except Exception:
            lbl = tk.Label(self, text="⚠ Error", bg=BG_GLASS, fg=GLOW_R,
                           font=FONT_UI, width=14, height=5)
        lbl.pack(padx=4, pady=(4, 0))

        name   = os.path.basename(path)
        try:
            parts  = name.replace("intruder_", "").replace(".jpg", "")
            dt     = datetime.datetime.strptime(parts, "%Y%m%d_%H%M%S")
            label  = dt.strftime("%d %b\n%H:%M:%S")
        except Exception:
            label = name[:16]

        tk.Label(self, text=label, bg=BG_GLASS, fg=FG3,
                 font=("Segoe UI", 7), justify="center").pack(pady=(2, 4))

        for w in (self, lbl):
            w.bind("<Button-1>", lambda e: on_click(path))
            w.bind("<Enter>",    lambda e: self.config(highlightbackground=GLOW_B))
            w.bind("<Leave>",    lambda e: self.config(highlightbackground=BORDER))


class LaptopGuardDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Laptop Guard")
        self.geometry("1100x720")
        self.minsize(960, 640)
        self.configure(bg=BG_DEEP)

        self._bg_img    = None
        self._bg_label  = None
        self._thumb_refs = []

        self.status_var    = tk.StringVar(value="Checking...")
        self.total_var     = tk.StringVar(value="—")
        self.today_var     = tk.StringVar(value="—")
        self.selected_path = None
        self._log_pos      = "1.0"

        self._draw_bg()
        self._build_ui()
        self._refresh()
        self._tick_otp()
        self._check_service()
        self._stream_log()
        self.bind("<Configure>", self._on_resize)

    # ── Background ─────────────────────────────────────────────────────────────

    def _draw_bg(self):
        w, h = 1100, 720
        bg = make_gradient_bg(w, h)
        self._bg_img   = ImageTk.PhotoImage(bg)
        self._bg_label = tk.Label(self, image=self._bg_img, bd=0)
        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    def _on_resize(self, event):
        if event.widget is self:
            bg = make_gradient_bg(event.width, event.height)
            self._bg_img = ImageTk.PhotoImage(bg)
            self._bg_label.config(image=self._bg_img)

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── header ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_GLASS,
                       highlightbackground=BORDER, highlightthickness=1)
        hdr.place(relx=0, rely=0, relwidth=1, height=56)

        tk.Label(hdr, text="  🔒  LAPTOP GUARD",
                 font=("Segoe UI", 14, "bold"), bg=BG_GLASS, fg=FG).pack(side="left", padx=12)

        svc_frame = tk.Frame(hdr, bg=BG_GLASS)
        svc_frame.pack(side="right", padx=16)
        tk.Label(svc_frame, text="SERVICE", font=("Segoe UI", 7), bg=BG_GLASS, fg=FG2).pack()
        self.status_badge = tk.Label(svc_frame, textvariable=self.status_var,
                                     font=("Segoe UI", 9, "bold"), bg=BG_GLASS, fg=GLOW_Y)
        self.status_badge.pack()

        # ── stat bar ─────────────────────────────────────────────────────
        stat_y = 68
        self._stat_card("TOTAL ATTEMPTS", self.total_var,  GLOW_R,  0.01, stat_y, 0.16)
        self._stat_card("TODAY",          self.today_var,  GLOW_Y,  0.19, stat_y, 0.16)

        # OTP ring card
        otp_card = glass_frame(self)
        otp_card.place(relx=0.37, y=stat_y, relwidth=0.26, height=110)
        tk.Label(otp_card, text="LIVE OTP", font=("Segoe UI", 7),
                 bg=BG_GLASS, fg=FG2).pack(pady=(6, 0))
        self.otp_ring = OTPRing(otp_card, size=88)
        self.otp_ring.pack()

        self._stat_card("LAST SEEN",      tk.StringVar(value="—"),  FG3,   0.65, stat_y, 0.16)
        self._stat_card("PHOTOS SAVED",   self.total_var,  GLOW_B,  0.83, stat_y, 0.16)

        # ── left column: photo grid ───────────────────────────────────────
        left = glass_frame(self)
        left.place(relx=0.01, y=190, relwidth=0.44, relheight=0.71)

        hdr2 = tk.Frame(left, bg=BG_GLASS)
        hdr2.pack(fill="x", padx=12, pady=(10, 6))
        tk.Label(hdr2, text="📸  Intruder Photos", font=FONT_H,
                 bg=BG_GLASS, fg=FG).pack(side="left")
        self._btn_small(hdr2, "Refresh", self._refresh).pack(side="right")

        # scrollable grid canvas
        grid_outer = tk.Frame(left, bg=BG_GLASS)
        grid_outer.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        grid_outer.rowconfigure(0, weight=1)
        grid_outer.columnconfigure(0, weight=1)

        self.grid_canvas = tk.Canvas(grid_outer, bg=BG_GLASS,
                                     highlightthickness=0)
        vsb = tk.Scrollbar(grid_outer, orient="vertical",
                           command=self.grid_canvas.yview)
        self.grid_canvas.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        self.grid_canvas.grid(row=0, column=0, sticky="nsew")

        self.thumb_frame = tk.Frame(self.grid_canvas, bg=BG_GLASS)
        self.grid_canvas.create_window((0, 0), window=self.thumb_frame,
                                       anchor="nw", tags="inner")
        self.thumb_frame.bind("<Configure>",
            lambda e: self.grid_canvas.configure(
                scrollregion=self.grid_canvas.bbox("all")))
        self.grid_canvas.bind("<MouseWheel>",
            lambda e: self.grid_canvas.yview_scroll(-1*(e.delta//120), "units"))

        self.empty_lbl = tk.Label(self.thumb_frame,
                                  text="No intruder photos yet.\nLock your PC and enter a wrong password to test.",
                                  bg=BG_GLASS, fg=FG2, font=FONT_UI, justify="center")

        # ── right column: preview + log ───────────────────────────────────
        right = tk.Frame(self, bg=BG_DEEP)
        right.place(relx=0.47, y=190, relwidth=0.52, relheight=0.71)
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)
        right.columnconfigure(0, weight=1)

        # preview card
        prev_card = glass_frame(right)
        prev_card.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        prev_card.rowconfigure(1, weight=1)
        prev_card.columnconfigure(0, weight=1)
        tk.Label(prev_card, text="🖼  Preview", font=FONT_H,
                 bg=BG_GLASS, fg=FG).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))
        self.preview_lbl = tk.Label(prev_card, bg=BG_GLASS,
                                    text="← Select a photo from the grid",
                                    fg=FG2, font=FONT_UI)
        self.preview_lbl.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # log card
        log_card = glass_frame(right)
        log_card.grid(row=1, column=0, sticky="nsew")
        log_card.rowconfigure(1, weight=1)
        log_card.columnconfigure(0, weight=1)

        log_hdr = tk.Frame(log_card, bg=BG_GLASS)
        log_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        tk.Label(log_hdr, text="📋  Live Activity Log", font=FONT_H,
                 bg=BG_GLASS, fg=FG).pack(side="left")
        self.live_dot = tk.Label(log_hdr, text="● LIVE",
                                 font=("Segoe UI", 8, "bold"),
                                 bg=BG_GLASS, fg=GLOW_G)
        self.live_dot.pack(side="right")

        log_inner = tk.Frame(log_card, bg=BG_GLASS)
        log_inner.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        log_inner.rowconfigure(0, weight=1)
        log_inner.columnconfigure(0, weight=1)

        lsb = tk.Scrollbar(log_inner)
        lsb.grid(row=0, column=1, sticky="ns")
        self.log_box = tk.Text(log_inner, yscrollcommand=lsb.set,
                               bg="#0a1628", fg=FG3, font=FONT_MONO,
                               relief="flat", state="disabled",
                               insertbackground=FG, wrap="word")
        self.log_box.grid(row=0, column=0, sticky="nsew")
        lsb.config(command=self.log_box.yview)
        self.log_box.tag_config("alert", foreground=GLOW_R)
        self.log_box.tag_config("ok",    foreground=GLOW_G)
        self.log_box.tag_config("info",  foreground=GLOW_B)
        self.log_box.tag_config("dim",   foreground=FG2)

        # ── bottom action bar ─────────────────────────────────────────────
        bar = glass_frame(self)
        bar.place(relx=0, rely=1.0, relwidth=1, height=48, anchor="sw")

        self._btn(bar, "📁  Open Photo Folder", self._open_folder, GLOW_B).pack(side="left",  padx=(12, 4), pady=8)
        self._btn(bar, "▶  Start Service",      self._start_svc,   GLOW_G).pack(side="right", padx=4,       pady=8)
        self._btn(bar, "⏹  Stop Service",       self._stop_svc,    GLOW_R).pack(side="right", padx=4,       pady=8)

    def _stat_card(self, label, var, color, relx, y, relw):
        card = glass_frame(self)
        card.place(relx=relx, y=y, relwidth=relw, height=110)
        tk.Label(card, text=label, font=("Segoe UI", 7),
                 bg=BG_GLASS, fg=FG2).pack(pady=(12, 2))
        tk.Label(card, textvariable=var,
                 font=FONT_BIG, bg=BG_GLASS, fg=color).pack()

    def _btn(self, parent, text, cmd, color=GLOW_B):
        return tk.Button(parent, text=text, command=cmd,
                         bg=BG_GLASS, fg=color, font=FONT_B,
                         relief="flat", padx=14, pady=6,
                         activebackground=BORDER, activeforeground=color,
                         cursor="hand2", bd=0)

    def _btn_small(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd,
                         bg=BORDER, fg=FG3, font=("Segoe UI", 8),
                         relief="flat", padx=8, pady=3,
                         activebackground=BG_GLASS, cursor="hand2", bd=0)

    # ── Logic ──────────────────────────────────────────────────────────────────

    def _refresh(self):
        photos = sorted(glob.glob(os.path.join(SAVE_FOLDER, "intruder_*.jpg")),
                        reverse=True)
        today  = datetime.date.today().strftime("%Y%m%d")

        self.total_var.set(str(len(photos)))
        self.today_var.set(str(sum(1 for p in photos if today in os.path.basename(p))))

        # rebuild grid
        for w in self.thumb_frame.winfo_children():
            w.destroy()
        self._thumb_refs.clear()

        if not photos:
            self.empty_lbl = tk.Label(
                self.thumb_frame,
                text="No intruder photos yet.\nLock your PC and enter a wrong password to test.",
                bg=BG_GLASS, fg=FG2, font=FONT_UI, justify="center")
            self.empty_lbl.grid(row=0, column=0, padx=20, pady=40)
            return

        cols = 3
        for i, path in enumerate(photos):
            thumb = PhotoThumb(self.thumb_frame, path, self._show_photo)
            thumb.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")
            self._thumb_refs.append(thumb)

        self._log_from_photos(photos)

    def _show_photo(self, path):
        self.selected_path = path
        try:
            # get current preview area size
            self.preview_lbl.update_idletasks()
            pw = max(self.preview_lbl.winfo_width()  - 16, 300)
            ph = max(self.preview_lbl.winfo_height() - 16, 200)
            img = Image.open(path)
            img.thumbnail((pw, ph))
            self._preview_ref = ImageTk.PhotoImage(img)
            self.preview_lbl.config(image=self._preview_ref, text="")
        except Exception as e:
            self.preview_lbl.config(text=f"Error: {e}", image="")

    def _log_from_photos(self, photos):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.insert("end", "─── Intrusion History ───\n", "dim")
        for p in photos[:30]:
            name = os.path.basename(p)
            try:
                parts = name.replace("intruder_", "").replace(".jpg", "")
                dt    = datetime.datetime.strptime(parts, "%Y%m%d_%H%M%S")
                ts    = dt.strftime("%d %b %Y  %H:%M:%S")
            except Exception:
                ts = name
            self.log_box.insert("end", f"⚠  Failed login at {ts}\n", "alert")
        self.log_box.config(state="disabled")
        self.log_box.see("end")

    def _stream_log(self):
        """Tail guard.log in real time if it exists."""
        if not os.path.exists(LOG_FILE):
            self.after(5000, self._stream_log)
            return

        def tail():
            try:
                with open(LOG_FILE, "r", errors="replace") as f:
                    f.seek(0, 2)  # jump to end
                    while True:
                        line = f.readline()
                        if line:
                            self._append_log(line.rstrip())
                        else:
                            time.sleep(1)
            except Exception:
                pass

        threading.Thread(target=tail, daemon=True).start()

    def _append_log(self, line):
        def _do():
            self.log_box.config(state="normal")
            tag = "alert" if "failed" in line.lower() or "⚠" in line else \
                  "ok"    if "[+]" in line else \
                  "info"  if "[*]" in line else "dim"
            self.log_box.insert("end", line + "\n", tag)
            self.log_box.config(state="disabled")
            self.log_box.see("end")
            # pulse live dot
            self.live_dot.config(fg=GLOW_Y)
            self.after(600, lambda: self.live_dot.config(fg=GLOW_G))
        self.after(0, _do)

    def _tick_otp(self):
        if TOTP_SECRET:
            try:
                totp      = pyotp.TOTP(TOTP_SECRET)
                otp       = totp.now()
                remaining = 30 - (datetime.datetime.now().second % 30)
                self.otp_ring.update_otp(otp, remaining)
            except Exception:
                self.otp_ring.update_otp("ERR", 0)
        else:
            self.otp_ring.update_otp("NO KEY", 0)
        self.after(1000, self._tick_otp)

    def _check_service(self):
        def check():
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                     r"SYSTEM\CurrentControlSet\Services\LaptopGuard")
                val, _ = winreg.QueryValueEx(key, "Start")
                winreg.CloseKey(key)
                # Check running state via tasklist instead of sc
                r = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq python.exe"],
                    capture_output=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if "python.exe" in r.stdout:
                    self.status_var.set("● RUNNING")
                    self.status_badge.config(fg=GLOW_G)
                else:
                    self.status_var.set("● STOPPED")
                    self.status_badge.config(fg=GLOW_R)
            except FileNotFoundError:
                self.status_var.set("● NOT INSTALLED")
                self.status_badge.config(fg=GLOW_Y)
            except Exception:
                self.status_var.set("● UNKNOWN")
                self.status_badge.config(fg=FG2)
        threading.Thread(target=check, daemon=True).start()
        self.after(15000, self._check_service)

    def _start_svc(self):
        subprocess.run(["sc", "start", "LaptopGuard"], capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        self.after(2000, self._check_service)

    def _stop_svc(self):
        subprocess.run(["sc", "stop", "LaptopGuard"], capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)

    def _start_svc(self):
        subprocess.run(["sc", "start", "LaptopGuard"], capture_output=True)
        self.after(2000, self._check_service)

    def _stop_svc(self):
        subprocess.run(["sc", "stop", "LaptopGuard"], capture_output=True)
        self.after(2000, self._check_service)

    def _open_folder(self):
        os.makedirs(SAVE_FOLDER, exist_ok=True)
        os.startfile(SAVE_FOLDER)


if __name__ == "__main__":
    app = LaptopGuardDashboard()
    app.mainloop()