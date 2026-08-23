import customtkinter as ctk
import minecraft_launcher_lib
import subprocess, os, threading, json, shutil, psutil, sys, platform, zipfile, tempfile, re
import requests, base64, webbrowser, uuid
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox, filedialog
import ssl
import certifi
import time
from pypresence import Presence

# Forces Python to use the certifi certificate bundle
os.environ['SSL_CERT_FILE'] = certifi.where()

# ─── OS Detection ───────────────────────────────────────────────────────────
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

def open_folder(path):
    if IS_WINDOWS:
        os.startfile(path)
    elif IS_LINUX:
        subprocess.Popen(["xdg-open", path])
    else:
        os.startfile(path)

def get_java_name():
    return "javaw.exe" if IS_WINDOWS else "java"

def parse_mc_version(version_str):
    try:
        parts = version_str.split('.')
        if len(parts) >= 2:
            major = int(parts[0])
            minor = int(parts[1])
            return major, minor
        return int(parts[0]), 0
    except:
        return 0, 0

def supports_forge(version_str):
    major, minor = parse_mc_version(version_str)
    if major >= 2:
        return True
    return major == 1 and minor >= 8

def supports_fabric(version_str):
    major, minor = parse_mc_version(version_str)
    if major >= 2:
        return True
    return major == 1 and minor >= 14

def supports_neoforge(version_str):
    try:
        parts = version_str.split('.')
        major, minor = int(parts[0]), int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 else 0
        if major >= 2:
            return True
        if major == 1 and minor > 20:
            return True
        if major == 1 and minor == 20 and patch >= 2:
            return True
        return False
    except:
        return False

# OR: Temporary bypass (If the above doesn't work)


# Theme Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG_DARK = "#0a0a14"
BG_CARD = "#14142a"
BG_SIDEBAR = "#0c0c1e"
ACCENT = "#7c5cbf"
ACCENT_HOVER = "#6a4dab"
GREEN = "#2ecc71"
RED = "#e74c3c"
ORANGE = "#f39c12"
TEXT_MUTED = "#8888bb"
TEXT_WHITE = "#ffffff"
BORDER = "#2a2a50"
FONT = "Segoe UI"

LIGHT_BG_DARK = "#f0f0f5"
LIGHT_BG_CARD = "#ffffff"
LIGHT_BG_SIDEBAR = "#e8e8f0"
LIGHT_TEXT_MUTED = "#666680"
LIGHT_TEXT_WHITE = "#1a1a2e"
LIGHT_BORDER = "#d0d0e0"

class SozipLauncher(ctk.CTk):
    VERSION = "2.0"
    UPDATE_URL = "https://raw.githubusercontent.com/sozipp/LAUNCHER-UPDATER/main/UPDATE.json"

    def __init__(self):
        super().__init__()
        self.title("SOZIP LAUNCHER PRO")
        self.minsize(900, 700)
        self.resizable(True, True)
        self.withdraw()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        main_w = min(1150, sw - 60)
        main_h = min(850, sh - 100)
        self.geometry(f"{main_w}x{main_h}+{sw//2-main_w//2}+{sh//2-main_h//2}")
        self.configure(fg_color=BG_DARK)

        splash_w = min(600, sw - 80)
        splash_h = min(500, sh - 80)
        self.splash = ctk.CTkToplevel()
        self.splash.overrideredirect(True)
        self.splash.attributes("-topmost", True)
        self.splash.configure(fg_color=BG_DARK)
        self.splash.geometry(f"{splash_w}x{splash_h}+{sw//2-splash_w//2}+{sh//2-splash_h//2}")

        self.splash_title = ctk.CTkLabel(self.splash, text="SOZIP", font=(FONT, 80, "bold"), text_color=ACCENT)
        self.splash_title.pack(expand=True, pady=(60, 0))
        ctk.CTkLabel(self.splash, text="LAUNCHER", font=(FONT, 24, "normal"), text_color=TEXT_MUTED).pack()
        self.splash_sep = ctk.CTkFrame(self.splash, height=3, width=240, fg_color=ACCENT, corner_radius=2)
        self.splash_sep.pack(pady=20)
        ctk.CTkLabel(self.splash, text="made by sozip19op", font=(FONT, 12), text_color=TEXT_MUTED).pack()
        self.splash_link = ctk.CTkLabel(self.splash, text="youtube.com/@sozip19op", font=(FONT, 12), text_color=ACCENT, cursor="hand2")
        self.splash_link.pack(pady=4)
        self.splash_link.bind("<Button-1>", lambda e: webbrowser.open("https://youtube.com/@sozip19op"))
        self.splash_bar = ctk.CTkProgressBar(self.splash, width=280, mode="indeterminate", fg_color="#1e1e3a", progress_color=ACCENT, height=4, corner_radius=2)
        self.splash_bar.pack(pady=30)
        self.splash_bar.start()
        self.splash.update()

        try:
            self._init_launcher()
            self.after(5000, self._finish_launch)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            for w in self.splash.winfo_children(): w.destroy()
            self.splash.geometry("600x400")
            ctk.CTkLabel(self.splash, text="INIT ERROR", font=(FONT, 28, "bold"), text_color=RED).pack(pady=(40, 10))
            ctk.CTkLabel(self.splash, text=str(e), font=(FONT, 12), text_color=TEXT_WHITE, wraplength=500).pack(pady=10)
            ctk.CTkLabel(self.splash, text=tb[-600:], font=(FONT, 10), text_color=TEXT_MUTED, wraplength=500, justify="left").pack(pady=10, fill="both", expand=True, padx=20)
            with open("launcher_crash.log", "w") as f:
                f.write(tb)

    def _init_launcher(self):
        global ACCENT, ACCENT_HOVER, BORDER
        icon_dirs = [os.getcwd(), os.path.dirname(sys.argv[0])]
        if getattr(sys, 'frozen', False):
            icon_dirs.insert(0, sys._MEIPASS)
        if IS_WINDOWS:
            for d in icon_dirs:
                icon_path = os.path.join(d, "sozip_icon.ico")
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
                    break
        elif IS_LINUX:
            for d in icon_dirs:
                icon_path = os.path.join(d, "sozip_icon.png")
                if os.path.exists(icon_path):
                    img = tk.PhotoImage(file=icon_path)
                    self.iconphoto(True, img)
                    break

        total_ram = psutil.virtual_memory().total
        self.max_pc_ram = int(total_ram / (1024**3))
        self.config_file = "sozip_config.json"

        default_settings = {
            "username": "Player",
            "ram": 4,
            "server_ram": 2,
            "path": os.path.join(os.getcwd(), "sozip_data"),
            "elyby_token": "",
            "elyby_uuid": ""
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
            except:
                data = default_settings
        else:
            data = default_settings

        self.username = data.get("username", default_settings["username"])
        self.ram = data.get("ram", default_settings["ram"])
        self.server_ram = data.get("server_ram", default_settings["server_ram"])
        self.base_path = data.get("path", default_settings["path"])
        self.elyby_token = data.get("elyby_token", "")
        self.elyby_uuid = data.get("elyby_uuid", "")
        self.elyby_enabled = ctk.BooleanVar(value=bool(self.elyby_token))
        self.accounts = data.get("accounts", [])
        current_type = "elyby" if self.elyby_token else "cracked"
        if self.username and not any(a["username"] == self.username for a in self.accounts):
            self.accounts.append({"username": self.username, "type": current_type})

        saved_accent = data.get("accent")
        if saved_accent and saved_accent != ACCENT:
            saved_hover = data.get("accent_hover", ACCENT_HOVER)
            saved_border = data.get("border", BORDER)
            ACCENT = saved_accent
            ACCENT_HOVER = saved_hover
            BORDER = saved_border
        if hasattr(self, 'splash_title'):
            self.splash_title.configure(text_color=ACCENT)
            self.splash_sep.configure(fg_color=ACCENT)
            self.splash_link.configure(text_color=ACCENT)
            self.splash_bar.configure(progress_color=ACCENT)

        saved_mode = data.get("appearance_mode")
        if saved_mode:
            ctk.set_appearance_mode(saved_mode)
            global BG_DARK, BG_CARD, BG_SIDEBAR, TEXT_MUTED, TEXT_WHITE
            if saved_mode == "Light":
                BG_DARK, BG_CARD, BG_SIDEBAR = LIGHT_BG_DARK, LIGHT_BG_CARD, LIGHT_BG_SIDEBAR
                TEXT_MUTED, TEXT_WHITE, BORDER = LIGHT_TEXT_MUTED, LIGHT_TEXT_WHITE, LIGHT_BORDER

        self.is_installing = False
        self.selected_version = data.get("selected_version", None)
        self.processes = {}
        self.server_ports = {}
        self.tunnel_processes = {}
        self.update_available = False
        self.update_data = None

        os.makedirs(self.base_path, exist_ok=True)
        self.load_settings()

        self.skin_dir = os.path.join(self.base_path, "skins")
        os.makedirs(self.skin_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "servers"), exist_ok=True)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.configure(fg_color=BG_DARK)

        self.sidebar = ctk.CTkFrame(self, width=min(240, self.winfo_screenwidth()//4), corner_radius=0, fg_color=BG_SIDEBAR, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        skin_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        skin_container.pack(pady=(30, 8))
        self.skin_border = ctk.CTkFrame(skin_container, width=90, height=90, fg_color="transparent", border_width=2, border_color=ACCENT, corner_radius=0)
        self.skin_border.pack(pady=(0, 6))
        self.skin_border.pack_propagate(False)
        self.skin_label = ctk.CTkLabel(self.skin_border, text="", width=82, height=82, fg_color=BG_CARD, corner_radius=0)
        self.skin_label.pack(expand=True)
        self.skin_label.pack()
        skin_row = ctk.CTkFrame(skin_container, fg_color="transparent")
        skin_row.pack()
        self.skin_upload_btn = ctk.CTkButton(skin_row, text="Upload", width=54, height=22, font=(FONT, 9), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, command=self.upload_skin)
        self.skin_upload_btn.pack(side="left", padx=2)
        self.skin_fetch_btn = ctk.CTkButton(skin_row, text="Fetch", width=54, height=22, font=(FONT, 9), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, command=self.fetch_skin_from_mojang)
        self.skin_fetch_btn.pack(side="left", padx=2)

        self.sep2 = ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER)
        self.sep2.pack(fill="x", padx=16, pady=8)

        self.dash_btn = ctk.CTkButton(self.sidebar, text="  ⌂  Dashboard", anchor="w", height=34, font=(FONT, 12), fg_color="transparent", text_color=TEXT_WHITE, hover_color=BG_CARD, command=self.draw_home)
        self.dash_btn.pack(fill="x", padx=10, pady=1)
        self.install_btn = ctk.CTkButton(self.sidebar, text="  ⊞  Installer", anchor="w", height=34, font=(FONT, 12), fg_color="transparent", text_color=TEXT_WHITE, hover_color=BG_CARD, command=self.draw_install_screen)
        self.install_btn.pack(fill="x", padx=10, pady=1)
        self.snap_btn = ctk.CTkButton(self.sidebar, text="  ⎔  Snapshots", anchor="w", height=34, font=(FONT, 12), fg_color="transparent", text_color=TEXT_WHITE, hover_color=BG_CARD, command=self.draw_snapshot_screen)
        self.snap_btn.pack(fill="x", padx=10, pady=1)
        self.server_mgr_btn = ctk.CTkButton(self.sidebar, text="  ⚡  Server Manager", anchor="w", height=34, font=(FONT, 12), fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self.draw_server_dashboard)
        self.server_mgr_btn.pack(fill="x", padx=10, pady=1)

        self.sep3 = ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER)
        self.sep3.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(self.sidebar, text="Player", font=(FONT, 9), text_color=TEXT_MUTED).pack(anchor="w", padx=22)
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.pack(fill="x", padx=16, pady=3)
        self.user_entry = ctk.CTkEntry(user_frame, height=30, fg_color=BG_CARD, border_color=BORDER, corner_radius=6)
        self.user_entry.pack(side="left", fill="x", expand=True)
        self.user_entry.insert(0, self.username)
        ctk.CTkButton(user_frame, text="~", width=30, height=30, font=(FONT, 14, "bold"),
                       fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=6,
                       command=self.open_account_manager).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(self.sidebar, text="Game RAM", font=(FONT, 9), text_color=TEXT_MUTED).pack(anchor="w", padx=22, pady=(6, 0))
        self.ram_lbl = ctk.CTkLabel(self.sidebar, text=f"{self.ram} GB", font=(FONT, 12, "bold"), text_color=ACCENT)
        self.ram_lbl.pack()
        ram_steps = int(self.max_pc_ram * 2 - 1)
        self.ram_slider = ctk.CTkSlider(self.sidebar, from_=0.5, to=self.max_pc_ram, number_of_steps=ram_steps, progress_color=ACCENT, button_color=ACCENT, button_hover_color=ACCENT_HOVER, command=self.update_ram_label)
        self.ram_slider.set(self.ram)
        self.ram_slider.pack(fill="x", padx=16, pady=2)

        ctk.CTkLabel(self.sidebar, text="Server RAM", font=(FONT, 9), text_color=TEXT_MUTED).pack(anchor="w", padx=22, pady=(6, 0))
        self.s_ram_lbl = ctk.CTkLabel(self.sidebar, text=f"{self.server_ram} GB", font=(FONT, 12, "bold"), text_color=ACCENT)
        self.s_ram_lbl.pack()
        self.s_ram_slider = ctk.CTkSlider(self.sidebar, from_=0.5, to=self.max_pc_ram, number_of_steps=ram_steps, progress_color=ACCENT, button_color=ACCENT, button_hover_color=ACCENT_HOVER, command=self.update_server_ram_label)
        self.s_ram_slider.set(self.server_ram)
        self.s_ram_slider.pack(fill="x", padx=16, pady=2)

        self.settings_nav_btn = ctk.CTkButton(self.sidebar, text="⚙  Settings", height=30, font=(FONT, 10), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=6, command=self.draw_settings_screen)
        self.settings_nav_btn.pack(fill="x", padx=16, pady=(2, 2))
        self.open_data_btn = ctk.CTkButton(self.sidebar, text="Open Game Data", height=30, font=(FONT, 10), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=6, command=lambda: open_folder(self.base_path))
        self.open_data_btn.pack(fill="x", padx=16, pady=(2, 8))

        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.update_skin_display()
        self.draw_home()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.start_discord_rpc()

    def _finish_launch(self):
        try:
            self.splash.destroy()
        except:
            pass
        for f in ["updater.sh", "updater.bat"]:
            p = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f)
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
        try:
            self.deiconify()
        except:
            pass
        try:
            self.state("normal")
        except:
            pass
        self.lift()
        self.focus_force()
        self.update()
        self.after(100, self.lift)
        self.after(2000, self.check_for_updates)
    
    def is_valid_username(self, name):
        return bool(name) and 3 <= len(name) <= 16 and all(c.isalnum() or c == '_' for c in name)

    def open_link(self, url):
        webbrowser.open_new_tab(url)

    def check_for_updates(self):
        def _check():
            try:
                resp = requests.get(self.UPDATE_URL, timeout=10)
                if resp.status_code != 200:
                    return
                data = resp.json()
                latest = data.get("latest_version", "")
                if latest == self.VERSION:
                    return
                self.update_data = data
                self.update_available = True
                self.after(0, self._show_update_popup)
            except:
                pass
        threading.Thread(target=_check, daemon=True).start()

    def _show_update_popup(self):
        if not self.update_data:
            return
        pop = ctk.CTkToplevel(self)
        pop.title("Update Available")
        pop.geometry("460x420")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        pop.resizable(False, False)
        ctk.CTkLabel(pop, text="Update Available", font=(FONT, 22, "bold"), text_color=TEXT_WHITE).pack(pady=(25, 5))
        ctk.CTkLabel(pop, text=f"Version {self.update_data.get('latest_version', '?')} is available", font=(FONT, 12), text_color=TEXT_MUTED).pack()
        cl = self.update_data.get("changelog", "")
        if cl:
            frame = ctk.CTkScrollableFrame(pop, fg_color=BG_CARD, corner_radius=8, height=80)
            frame.pack(fill="x", padx=30, pady=12)
            ctk.CTkLabel(frame, text="What's new:", font=(FONT, 10, "bold"), text_color=TEXT_WHITE, anchor="w").pack(fill="x")
            ctk.CTkLabel(frame, text=cl, font=(FONT, 10), text_color=TEXT_MUTED, anchor="w", wraplength=380).pack(fill="x", pady=2)
        btn_row = ctk.CTkFrame(pop, fg_color="transparent")
        btn_row.pack(pady=15)
        ctk.CTkButton(btn_row, text="Later", width=100, height=34, font=(FONT, 12),
                      fg_color="transparent", text_color=TEXT_WHITE, hover_color=BORDER, border_width=1, border_color=BORDER, corner_radius=8,
                      command=pop.destroy).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Update Now", width=140, height=34, font=(FONT, 12, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8,
                      command=lambda: [pop.destroy(), self._run_update()]).pack(side="left", padx=6)

    def _run_update(self):
        if not self.update_data:
            return
        exe_path = os.path.realpath(sys.argv[0])
        exe_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path)
        if IS_WINDOWS:
            dl_key = "download_windows"
            script_name = "updater.bat"
            lines = [
                "@echo off",
                "timeout /t 2 /nobreak >nul",
                f'del /f /q "{exe_path}"',
                f'curl -L -o "{exe_path}" "{self.update_data.get(dl_key, "")}"',
                f'start "" "{exe_path}"',
                "del /f /q \"%~f0\""
            ]
        else:
            dl_key = "download_linux"
            script_name = "updater.sh"
            lines = [
                "#!/bin/bash",
                "sleep 2",
                f'rm -f "{exe_path}"',
                f'wget -O "{exe_path}" "{self.update_data.get(dl_key, "")}"',
                f'chmod +x "{exe_path}"',
                f'"{exe_path}" &',
                'rm -f "$0"'
            ]
        script_path = os.path.join(exe_dir, script_name)
        try:
            with open(script_path, "w") as f:
                f.write("\n".join(lines))
            if not IS_WINDOWS:
                os.chmod(script_path, 0o755)
            if IS_WINDOWS:
                os.startfile(script_path)
            else:
                subprocess.Popen(["x-terminal-emulator", "-e", script_path] if shutil.which("x-terminal-emulator") else [script_path])
            self.quit()
        except Exception as e:
            messagebox.showerror("Update Error", f"Could not create updater: {e}")

    def open_account_manager(self):
        pop = ctk.CTkToplevel(self)
        pop.title("Account Manager")
        pop.geometry("520x480")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        pop.resizable(False, False)

        ctk.CTkLabel(pop, text="Account Manager", font=(FONT, 20, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 10))
        ctk.CTkLabel(pop, text="Select or manage your accounts", font=(FONT, 10), text_color=TEXT_MUTED).pack()

        scroll = ctk.CTkScrollableFrame(pop, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
        scroll.pack(fill="both", expand=True, padx=15, pady=10)

        def refresh():
            for w in scroll.winfo_children(): w.destroy()
            for i, acc in enumerate(self.accounts):
                row = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10, border_width=2,
                                    border_color=ACCENT if acc["username"] == self.username else BORDER)
                row.pack(fill="x", pady=3)

                is_current = acc["username"] == self.username
                label_text = acc["username"]
                if acc.get("type") == "elyby":
                    label_text += "  (Ely.by)"
                if is_current:
                    label_text += "  ✓"
                ctk.CTkLabel(row, text=label_text, font=(FONT, 12, "bold"), text_color=TEXT_WHITE, anchor="w").pack(side="left", padx=12, pady=8, fill="x", expand=True)

                if not is_current:
                    ctk.CTkButton(row, text="Select", width=60, height=26, font=(FONT, 10, "bold"),
                                  fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6,
                                  command=lambda idx=i: select_acc(idx)).pack(side="right", padx=(0, 4))
                if acc.get("type") != "elyby":
                    ctk.CTkButton(row, text="✎", width=30, height=26, font=(FONT, 14, "bold"),
                                  fg_color="transparent", text_color=TEXT_WHITE, hover_color=BORDER, border_width=1, border_color=BORDER, corner_radius=6,
                                  command=lambda idx=i: edit_acc(idx)).pack(side="right", padx=2)
                    ctk.CTkButton(row, text="−", width=30, height=26, font=(FONT, 14, "bold"),
                                  fg_color="transparent", text_color=RED, hover_color=RED, border_width=1, border_color=RED, corner_radius=6,
                                  command=lambda idx=i: delete_acc(idx)).pack(side="right", padx=4)

        def select_acc(idx):
            if 0 <= idx < len(self.accounts):
                self.username = self.accounts[idx]["username"]
                self.user_entry.delete(0, "end")
                self.user_entry.insert(0, self.username)
                self.save_settings()
                pop.destroy()

        def delete_acc(idx):
            if 0 <= idx < len(self.accounts):
                acc = self.accounts[idx]
                if acc.get("type") == "elyby":
                    messagebox.showinfo("Account Manager", "Cannot delete Ely.by account from here. Use Settings to logout.", parent=pop)
                    return
                if acc["username"] == self.username and len(self.accounts) > 1:
                    other = next((a for a in self.accounts if a["username"] != self.username), None)
                    if other:
                        self.username = other["username"]
                        self.user_entry.delete(0, "end")
                        self.user_entry.insert(0, self.username)
                elif acc["username"] == self.username:
                    self.username = "Player"
                    self.user_entry.delete(0, "end")
                    self.user_entry.insert(0, "Player")
                self.accounts.pop(idx)
                self.save_settings()
                refresh()

        def edit_acc(idx):
            if 0 <= idx < len(self.accounts):
                acc = self.accounts[idx]
                edit_pop = ctk.CTkToplevel(pop)
                edit_pop.geometry("320x170")
                edit_pop.title("Edit Username")
                edit_pop.attributes("-topmost", True)
                edit_pop.configure(fg_color=BG_DARK)
                edit_pop.resizable(False, False)
                ctk.CTkLabel(edit_pop, text="Edit username", font=(FONT, 14, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 10))
                entry = ctk.CTkEntry(edit_pop, placeholder_text="New username", width=220, fg_color=BG_CARD, border_color=BORDER)
                entry.insert(0, acc["username"])
                entry.pack()
                def do_edit():
                    n = entry.get().strip()
                    if not self.is_valid_username(n):
                        messagebox.showwarning("Invalid", "Username must be 3-16 characters: letters, numbers, underscores only.", parent=edit_pop)
                        return
                    if n != acc["username"] and any(a["username"] == n for a in self.accounts):
                        messagebox.showwarning("Duplicate", "An account with this name already exists.", parent=edit_pop)
                        return
                    old = acc["username"]
                    acc["username"] = n
                    if self.username == old:
                        self.username = n
                        if hasattr(self, 'user_entry') and self.user_entry.winfo_exists():
                            self.user_entry.delete(0, "end")
                            self.user_entry.insert(0, n)
                    self.save_settings()
                    edit_pop.destroy()
                    refresh()
                entry.bind("<Return>", lambda e: do_edit())
                ctk.CTkButton(edit_pop, text="Save", font=(FONT, 12, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6, command=do_edit).pack(pady=10)

        def add_cracked():
            def do_add():
                n = entry.get().strip()
                if not self.is_valid_username(n):
                    messagebox.showwarning("Invalid", "Username must be 3-16 characters: letters, numbers, underscores only.", parent=add_pop)
                    return
                self.accounts.append({"username": n, "type": "cracked"})
                self.save_settings()
                add_pop.destroy()
                refresh()
            add_pop = ctk.CTkToplevel(pop)
            add_pop.geometry("320x150")
            add_pop.title("Add Account")
            add_pop.attributes("-topmost", True)
            add_pop.configure(fg_color=BG_DARK)
            add_pop.resizable(False, False)
            ctk.CTkLabel(add_pop, text="Enter username", font=(FONT, 14, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 10))
            entry = ctk.CTkEntry(add_pop, placeholder_text="Username", width=220, fg_color=BG_CARD, border_color=BORDER)
            entry.pack()
            entry.bind("<Return>", lambda e: do_add())
            ctk.CTkButton(add_pop, text="Add", font=(FONT, 12, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6, command=do_add).pack(pady=10)

        refresh()

        btn_frame = ctk.CTkFrame(pop, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkButton(btn_frame, text="+ Add Cracked Account", font=(FONT, 11, "bold"), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, border_width=1, border_color=BORDER, corner_radius=8, command=add_cracked).pack(side="left", expand=True, fill="x")

    
    def update_ram_label(self, val):
        self.ram = round(float(val) * 2) / 2
        if self.ram < 0.5:
            self.ram = 0.5
        self.ram_lbl.configure(text=f"{self.ram} GB"); self.save_settings()

    def update_server_ram_label(self, val):
        self.server_ram = round(float(val) * 2) / 2
        if self.server_ram < 0.5:
            self.server_ram = 0.5
        self.s_ram_lbl.configure(text=f"{self.server_ram} GB"); self.save_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.username = data.get("username", "Player")
                    self.ram = data.get("ram", 4)
                    self.server_ram = data.get("server_ram", 2)
                    self.base_path = data.get("path", os.path.join(os.getcwd(), "sozip_data"))
            else: raise Exception()
        except:
            self.username, self.ram, self.server_ram, self.base_path = "Player", 4, 2, os.path.join(os.getcwd(), "sozip_data")
        os.makedirs(self.base_path, exist_ok=True)

    def save_settings(self, event=None):
        if hasattr(self, 'user_entry') and self.user_entry.winfo_exists():
            raw = self.user_entry.get()
            if self.is_valid_username(raw):
                self.username = raw
            else:
                self.user_entry.delete(0, "end")
                self.user_entry.insert(0, self.username)
        data = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
            except:
                pass
        data.update({
            "username": self.username,
            "path": self.base_path,
            "ram": self.ram,
            "server_ram": self.server_ram,
            "selected_version": self.selected_version if hasattr(self, 'selected_version') else "",
            "elyby_token": self.elyby_token,
            "elyby_uuid": self.elyby_uuid,
            "accounts": self.accounts
        })
        with open(self.config_file, "w") as f:
            json.dump(data, f)

    
    def draw_server_dashboard(self):
        for w in self.content_area.winfo_children(): w.destroy()
        header = ctk.CTkFrame(self.content_area, fg_color="transparent"); header.pack(fill="x")
        ctk.CTkLabel(header, text="Server Manager", font=(FONT, 28, "bold"), text_color=TEXT_WHITE).pack(side="left")
        ctk.CTkButton(header, text="+  Create Server", font=(FONT, 11), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=10, command=self.show_server_creator).pack(side="right")
        self.server_list_frame = ctk.CTkScrollableFrame(self.content_area, height=600, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
        self.server_list_frame.pack(fill="both", expand=True, pady=15)
        self.refresh_server_list()

    def show_server_creator(self):
        pop = ctk.CTkToplevel(self); pop.geometry("640x680"); pop.title("Create Server"); pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        ctk.CTkLabel(pop, text="Create Server", font=(FONT, 24, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 15))
        ctk.CTkLabel(pop, text="SOFTWARE", font=(FONT, 10, "bold"), text_color=TEXT_MUTED).pack()
        soft_opt = ctk.CTkOptionMenu(pop, values=["Vanilla", "Paper", "Snapshot"], fg_color=BG_CARD, button_color=ACCENT, button_hover_color=ACCENT_HOVER, dropdown_fg_color=BG_CARD, command=lambda m: update_list(m))
        soft_opt.pack(pady=5)
        ctk.CTkLabel(pop, text="VERSION", font=(FONT, 10, "bold"), text_color=TEXT_MUTED).pack(pady=(10, 2))
        search_entry = ctk.CTkEntry(pop, placeholder_text="Search versions...", fg_color=BG_CARD, border_color=BORDER)
        search_entry.pack(fill="x", padx=25, pady=5)
        version_frame = ctk.CTkScrollableFrame(pop, height=250, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
        version_frame.pack(fill="both", expand=True, padx=25, pady=5)
        status_lbl = ctk.CTkLabel(pop, text="Loading...", font=(FONT, 11), text_color=TEXT_MUTED)
        status_lbl.pack(pady=2)

        self._server_creator_data = {"versions": [], "selected": None, "buttons": []}

        def populate_list(vers):
            for w in version_frame.winfo_children(): w.destroy()
            self._server_creator_data["buttons"] = []
            self._server_creator_data["versions"] = vers
            for v in vers:
                btn = ctk.CTkButton(version_frame, text=v, anchor="w", fg_color="transparent", text_color=TEXT_WHITE, hover_color=BG_CARD, font=(FONT, 12), corner_radius=6,
                                    command=lambda x=v: select_version(x))
                btn.pack(fill="x", padx=5, pady=1)
                self._server_creator_data["buttons"].append(btn)

        def select_version(ver):
            self._server_creator_data["selected"] = ver
            status_lbl.configure(text=f"Selected: {ver}")
            for b in self._server_creator_data["buttons"]:
                ver = b.cget("text")
                b.configure(fg_color=ACCENT if ver == self._server_creator_data["selected"] else "transparent", text_color=TEXT_WHITE)

        def filter_versions(*args):
            query = search_entry.get().lower()
            for b in self._server_creator_data["buttons"]:
                ver = b.cget("text")
                b.pack_forget() if query not in ver.lower() else b.pack(fill="x", padx=5, pady=1)

        search_entry.bind("<KeyRelease>", filter_versions)

        def update_list(mode):
            status_lbl.configure(text="Loading...")
            def fetch():
                try:
                    if mode == "Paper":
                        raw = requests.get("https://fill.papermc.io/v3/projects/paper", headers={"User-Agent": "SozipLauncher/1.0"}).json()
                        vers = []
                        for major_ver, sub_vers in raw["versions"].items():
                            for sv in sub_vers:
                                vers.append(sv)
                        vers.reverse()
                    else:
                        m_type = "release" if mode == "Vanilla" else "snapshot"
                        vers = [v['id'] for v in minecraft_launcher_lib.utils.get_version_list() if v['type'] == m_type]
                        vers.reverse()
                    self.after(0, lambda: (populate_list(vers), status_lbl.configure(text=f"{len(vers)} versions loaded. Click one to select.")))
                except Exception as e:
                    self.after(0, lambda: status_lbl.configure(text=f"Error: {e}"))

            threading.Thread(target=fetch, daemon=True).start()

        update_list("Vanilla")
        ctk.CTkLabel(pop, text="By creating server you ACCEPT MOJANG OFFICIAL EULA + SERVER WILL BE CRACKED", font=(FONT, 9), text_color=TEXT_MUTED, wraplength=580).pack(padx=20, pady=(0, 5))
        btn_frame = ctk.CTkFrame(pop, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="CREATE", fg_color=ACCENT, hover_color=ACCENT_HOVER, command=lambda: self.finish_create_server(soft_opt.get(), self._server_creator_data.get("selected"), pop)).pack(side="right")

    def finish_create_server(self, soft, ver, win):
        os.makedirs(os.path.join(self.base_path, "servers", f"{soft}_{ver}"), exist_ok=True)
        win.destroy(); self.refresh_server_list()

    def refresh_server_list(self):
        for w in self.server_list_frame.winfo_children(): w.destroy()
        s_root = os.path.join(self.base_path, "servers")
        if not os.path.exists(s_root): os.makedirs(s_root)
        for folder in os.listdir(s_root):
            path = os.path.join(s_root, folder)
            if not os.path.isdir(path): continue

            card = ctk.CTkFrame(self.server_list_frame, fg_color=BG_CARD, corner_radius=12, border_width=2, border_color=BORDER)
            card.pack(fill="x", pady=5)

            header_row = ctk.CTkFrame(card, fg_color="transparent")
            header_row.pack(fill="x", padx=18, pady=(12, 4))
            ctk.CTkLabel(header_row, text="SERVER", font=(FONT, 10, "bold"), text_color=TEXT_MUTED, anchor="w").pack(fill="x")
            name_row = ctk.CTkFrame(header_row, fg_color="transparent")
            name_row.pack(fill="x")
            ctk.CTkLabel(name_row, text=folder, font=(FONT, 18, "bold"), text_color=TEXT_WHITE, anchor="w").pack(side="left")
            ctk.CTkButton(name_row, text="📁", width=32, height=28, font=(FONT, 12), fg_color="transparent", text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=6, command=lambda p=path: open_folder(p)).pack(side="right")

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=16, pady=(4, 12))

            if "Paper" in folder:
                ctk.CTkButton(btn_frame, text="PLUGINS", width=72, height=28, font=(FONT, 9, "bold"), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=6, border_width=1, border_color=BORDER, command=lambda f=folder: self.open_plugin_browser(f)).pack(side="left", padx=2)

            if not os.path.exists(os.path.join(path, "server.jar")):
                ctk.CTkButton(btn_frame, text="Install JAR", width=90, height=28, font=(FONT, 10, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6, command=lambda p=path, f=folder: self.install_server_jar(p, f)).pack(side="left", padx=2)
            else:
                if folder in self.processes and self.processes[folder].poll() is None:
                    ctk.CTkButton(btn_frame, text="CONSOLE", width=80, height=28, font=(FONT, 9, "bold"), fg_color="#8b5cf6", hover_color="#7c3aed", corner_radius=6, command=lambda f=folder: self.open_server_console(f)).pack(side="left", padx=2)
                    ctk.CTkButton(btn_frame, text="PORT", width=56, height=28, font=(FONT, 9, "bold"), fg_color=GREEN, hover_color="#27ae60", corner_radius=6, command=lambda f=folder: self.copy_server_port(f)).pack(side="left", padx=2)
                    ctk.CTkButton(btn_frame, text="PUBLIC IP", width=80, height=28, font=(FONT, 9, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6, command=lambda f=folder: self.start_pinggy_tunnel(f)).pack(side="left", padx=2)
                    ctk.CTkButton(btn_frame, text="STOP", width=56, height=28, font=(FONT, 9, "bold"), fg_color=RED, hover_color="#c0392b", corner_radius=6, command=lambda f=folder: self.stop_specific_server(f)).pack(side="left", padx=2)
                else:
                    ctk.CTkButton(btn_frame, text="START", width=76, height=28, font=(FONT, 10, "bold"), fg_color=GREEN, hover_color="#27ae60", corner_radius=6, command=lambda p=path, f=folder: self.start_specific_server(p, f)).pack(side="left", padx=2)

            ctk.CTkButton(btn_frame, text="DELETE", width=64, height=28, font=(FONT, 9, "bold"), fg_color="transparent", text_color=RED, hover_color=RED, border_width=1, border_color=RED, corner_radius=6, command=lambda p=path: self.delete_server(p)).pack(side="right", padx=2)

    def install_server_jar(self, path, folder_name):
        soft, version = folder_name.split('_', 1)
        pop, bar, label = self._make_download_popup(f"Downloading {soft} server...")
        def run():
            try:
                if soft == "Paper":
                    headers = {"User-Agent": "SozipLauncher/1.0"}
                    resp = requests.get(
                        f"https://fill.papermc.io/v3/projects/paper/versions/{version}/builds/latest",
                        headers=headers
                    ).json()
                    url = resp["downloads"]["server:default"]["url"]
                else:
                    manifest = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json").json()
                    v_entry = next(v for v in manifest['versions'] if v['id'] == version)
                    url = requests.get(v_entry['url']).json()['downloads']['server']['url']

                res = requests.get(url, stream=True)
                total = int(res.headers.get('content-length', 0))
                written = 0
                with open(os.path.join(path, "server.jar"), "wb") as f:
                    for chunk in res.iter_content(8192):
                        f.write(chunk)
                        written += len(chunk)
                        if total > 0:
                            self.after(0, lambda p=written/total: (bar.configure(value=p), label.configure(text=f"{written//1024}KB / {total//1024}KB")))
                self.after(0, pop.destroy)
                self.after(0, self.refresh_server_list)
            except Exception as e:
                self.after(0, pop.destroy)
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def start_specific_server(self, path, folder_name):
        try:
            server_ver = folder_name.split('_')[-1]
            required_ver = self.get_required_java_version(server_ver)
            portable_java = self.ensure_portable_java(required_ver)
        except:
            portable_java = "java" # Fallback to system java
        port = 25565; used = []
        for f in os.listdir(os.path.join(self.base_path, "servers")):
            prop = os.path.join(self.base_path, "servers", f, "server.properties")
            if os.path.exists(prop):
                with open(prop, "r") as f_obj:
                    for line in f_obj:
                        if "server-port=" in line: used.append(line.split("=")[1].strip())
        while str(port) in used: port += 1
        with open(os.path.join(path, "server.properties"), "w") as f:
            f.write(f"server-port={port}\nonline-mode=false\neula=true\n")
        with open(os.path.join(path, "eula.txt"), "w") as f: f.write("eula=true")
        java = portable_java
        cmd = [java, f"-Xmx{int(self.server_ram * 1024)}M", "-jar", "server.jar", "nogui"]
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if IS_WINDOWS else 0
        proc = subprocess.Popen(cmd, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True, bufsize=1, creationflags=flags)
        self.processes[folder_name] = proc
        self.server_ports[folder_name] = port  # save port
        self.open_server_console(folder_name)
        self.after(500, self.refresh_server_list)

    def open_server_console(self, folder_name):
        win = ctk.CTkToplevel(self); win.geometry("600x400"); win.title(f"Console: {folder_name}")
        txt = ctk.CTkTextbox(win, fg_color="#1a1a1a", text_color="#2ecc71", font=("Consolas", 12))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        ent = ctk.CTkEntry(win, placeholder_text="Command..."); ent.pack(fill="x", padx=10, pady=(0,10))
        def cmd_send(e):
            if folder_name in self.processes:
                self.processes[folder_name].stdin.write(ent.get() + "\n")
                self.processes[folder_name].stdin.flush()
                ent.delete(0, "end")
        ent.bind("<Return>", cmd_send)
        def log_loop():
            proc = self.processes.get(folder_name)
            if not proc: return
            for line in iter(proc.stdout.readline, ''):
                if txt.winfo_exists(): txt.insert("end", line); txt.see("end")
            self.after(0, self.refresh_server_list)
        threading.Thread(target=log_loop, daemon=True).start()

    def stop_specific_server(self, folder_name):
        if folder_name in self.processes:
            try:
                self.processes[folder_name].stdin.write("stop\n")
                self.processes[folder_name].stdin.flush()
            except: self.processes[folder_name].kill()
        if folder_name in self.tunnel_processes:
            try:
                self.tunnel_processes[folder_name].kill()
            except: pass
            del self.tunnel_processes[folder_name]

    def start_pinggy_tunnel(self, folder_name):
        if folder_name in self.tunnel_processes:
            try:
                self.tunnel_processes[folder_name].kill()
            except: pass
            del self.tunnel_processes[folder_name]
        port = self.server_ports.get(folder_name, 25565)
        pop = ctk.CTkToplevel(self)
        pop.title("Public IP - Pinggy")
        pop.geometry("380x180")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        pop.resizable(False, False)
        ctk.CTkLabel(pop, text="Starting Pinggy tunnel...", font=(FONT, 14, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 5))
        ctk.CTkLabel(pop, text="Get new 60 min IP", font=(FONT, 11), text_color=TEXT_MUTED).pack(pady=5)
        status = ctk.CTkLabel(pop, text="Connecting...", font=(FONT, 10), text_color=TEXT_MUTED)
        status.pack(pady=5)

        def tunnel_thread():
            import socket
            try:
                cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-p", "443", "-R", f"0:localhost:{port}", "tcp@a.pinggy.io"]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                self.tunnel_processes[folder_name] = proc
                import re
                for line in iter(proc.stdout.readline, ''):
                    m = re.search(r'tcp://([a-zA-Z0-9.-]+):(\d+)', line)
                    if m:
                        pub_ip = f"{m.group(1)}:{m.group(2)}"
                        self.after(0, lambda ip=pub_ip: self._show_tunnel_ip(pop, status, ip, folder_name))
                        return
                self.after(0, lambda: status.configure(text="Failed to get tunnel address"))
            except Exception as e:
                self.after(0, lambda: status.configure(text=f"Error: {e}"))

        threading.Thread(target=tunnel_thread, daemon=True).start()

    def _make_download_popup(self, title):
        pop = ctk.CTkToplevel(self)
        pop.geometry("420x160")
        pop.title(title)
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        pop.resizable(False, False)
        ctk.CTkLabel(pop, text=title, font=(FONT, 14, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 10))
        bar = ctk.CTkProgressBar(pop, width=340, height=8, corner_radius=4, progress_color=ACCENT, mode="indeterminate")
        bar.pack(pady=10)
        bar.start()
        label = ctk.CTkLabel(pop, text="Starting...", font=(FONT, 10), text_color=TEXT_MUTED)
        label.pack()
        return pop, bar, label

    def _show_tunnel_ip(self, pop, status, pub_ip, folder_name):
        status.configure(text="")
        for w in pop.winfo_children(): w.destroy()
        ctk.CTkLabel(pop, text="✅ Tunnel Active", font=(FONT, 16, "bold"), text_color=GREEN).pack(pady=(20, 5))
        ctk.CTkLabel(pop, text="Public IP (valid 60 min):", font=(FONT, 11), text_color=TEXT_MUTED).pack()
        ip_frame = ctk.CTkFrame(pop, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER)
        ip_frame.pack(pady=8)
        ctk.CTkLabel(ip_frame, text=pub_ip, font=(FONT, 14, "bold"), text_color=ACCENT).pack(padx=20, pady=6)
        self.clipboard_clear()
        self.clipboard_append(pub_ip)
        ctk.CTkLabel(pop, text="✓ Copied to clipboard!", font=(FONT, 10), text_color=GREEN).pack()

    def delete_server(self, path):
        if messagebox.askyesno("Delete", "Delete server?"):
            for folder, proc in list(self.processes.items()):
                if path.endswith(folder):
                    if proc.poll() is None:
                        try: proc.kill()
                        except: pass
                    del self.processes[folder]
            if hasattr(self, 'tunnel_processes'):
                for folder, proc in list(self.tunnel_processes.items()):
                    if path.endswith(folder):
                        try: proc.kill()
                        except: pass
                        del self.tunnel_processes[folder]
            shutil.rmtree(path, ignore_errors=True); self.refresh_server_list()

    
    def upload_skin(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png")])
        if file_path:
            dest = os.path.join(self.skin_dir, "active_skin.png")
            shutil.copy(file_path, dest)
            self.update_skin_display()
            messagebox.showinfo("Skin Updated", "Manual skin uploaded successfully!")

    def fetch_skin_from_mojang(self):
        username = self.user_entry.get()
        if not username or username == "Player":
            messagebox.showwarning("Error", "Enter a player name first!")
            return
        def download():
            try:
                uuid_res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
                if uuid_res.status_code != 200: raise Exception("Player not found")
                uuid = uuid_res.json()['id']
                profile_res = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}")
                props = profile_res.json().get("properties", [])
                for p in props:
                    if p['name'] == 'textures':
                        decoded = json.loads(base64.b64decode(p['value']))
                        skin_url = decoded['textures']['SKIN']['url']
                        skin_data = requests.get(skin_url).content
                        dest = os.path.join(self.skin_dir, "active_skin.png")
                        with open(dest, "wb") as f: f.write(skin_data)
                        self.after(0, self.update_skin_display)
                        return
            except Exception as e: self.after(0, lambda: messagebox.showerror("Skin Error", str(e)))
        threading.Thread(target=download, daemon=True).start()

    def update_skin_display(self):
        skin_path = os.path.join(self.skin_dir, "active_skin.png")
        if os.path.exists(skin_path):
            try:
                img = Image.open(skin_path).convert("RGBA")
                head = img.crop((8, 8, 16, 16))
                hat = img.crop((40, 8, 48, 16))
                head.paste(hat, (0, 0), hat)
                head_large = head.resize((80, 80), Image.NEAREST)
                photo = ImageTk.PhotoImage(head_large)
                self.skin_label.configure(image=photo, text="")
                self.skin_label.image = photo
            except: self.skin_label.configure(text="Skin Error")
        else:
            self.skin_label.configure(text="No Skin")

    def apply_skin_resource_pack(self, instance_path):
        skin_src = os.path.join(self.skin_dir, "active_skin.png")
        if not os.path.exists(skin_src): return
        pack_path = os.path.join(instance_path, "resourcepacks", "SozipSkin")
        tex_path = os.path.join(pack_path, "assets", "minecraft", "textures", "entity")
        os.makedirs(tex_path, exist_ok=True)
        shutil.copy(skin_src, os.path.join(tex_path, "steve.png"))
        shutil.copy(skin_src, os.path.join(tex_path, "alex.png"))
        with open(os.path.join(pack_path, "pack.mcmeta"), "w") as f:
            json.dump({"pack": {"pack_format": 15, "description": "Sozip Skin"}}, f)
        opt_file = os.path.join(instance_path, "options.txt")
        lines = []
        packs = ["vanilla"]
        if os.path.exists(opt_file):
            with open(opt_file, "r") as f:
                lines = f.readlines()
            for line in lines:
                if line.startswith("resourcePacks:"):
                    try:
                        existing = json.loads(line.split(":", 1)[1].strip())
                        if isinstance(existing, list):
                            packs = existing
                    except: pass
                    break
        if "file/SozipSkin" not in packs:
            packs.append("file/SozipSkin")
        new_line = f'resourcePacks:{json.dumps(packs)}\n'
        found = False
        with open(opt_file, "w") as f:
            for line in lines:
                if line.startswith("resourcePacks:"):
                    f.write(new_line)
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(new_line)

    def _install_crash_assistant(self, instance_path):
        try:
            parts = self.selected_version.split('_')
            if len(parts) < 2:
                return
            loader = parts[0].lower()
            mc_ver = parts[1]
            mods_dir = os.path.join(instance_path, "mods")
            os.makedirs(mods_dir, exist_ok=True)

            # Check if already installed
            if any("crash-assistant" in f.lower() or "crashassistant" in f.lower() for f in os.listdir(mods_dir)):
                return

            # Check internet
            try:
                requests.get("https://api.modrinth.com", timeout=5)
            except:
                return

            headers = {"User-Agent": "SozipLauncher/1.1"}
            # Search for crash-assistant project
            r = requests.get(
                "https://api.modrinth.com/v2/project/crash-assistant/version",
                headers=headers, timeout=10
            )
            if r.status_code != 200:
                return
            vers = r.json()
            if not isinstance(vers, list):
                return

            match = None
            for v in vers:
                gv = v.get('game_versions', [])
                loaders = v.get('loaders', [])
                if mc_ver in gv:
                    if loader == "vanilla":
                        if not loaders or all(l == "vanilla" for l in loaders):
                            match = v
                            break
                    elif loader in loaders:
                        match = v
                        break

            if not match:
                return

            fi = match['files'][0]
            dl = requests.get(fi['url'], stream=True, timeout=30)
            if dl.status_code != 200:
                return

            out = os.path.join(mods_dir, fi['filename'])
            with open(out, 'wb') as f:
                for chunk in dl.iter_content(8192):
                    f.write(chunk)
            if os.path.getsize(out) == 0:
                os.remove(out)
        except:
            pass

    def check_dependencies(self):
        if not self.selected_version:
            messagebox.showwarning("Warning", "No version selected!")
            return
        inst_path = os.path.join(self.base_path, "instances", self.selected_version)
        mods_dir = os.path.join(inst_path, "mods")
        if not os.path.exists(mods_dir):
            messagebox.showinfo("Dependencies", "No mods folder found.")
            return

        pop = ctk.CTkToplevel(self)
        pop.geometry("680x580")
        pop.title("Dependency Check")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)

        ctk.CTkLabel(pop, text="Checking Dependencies", font=(FONT, 20, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 5))
        status = ctk.CTkLabel(pop, text="Scanning mods...", font=(FONT, 11), text_color=TEXT_MUTED)
        status.pack()
        tree_frame = ctk.CTkScrollableFrame(pop, fg_color="transparent", height=300, scrollbar_button_hover_color=ACCENT)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)
        pop.resizable(True, True)

        parts = self.selected_version.split('_')
        mc_ver = parts[1] if len(parts) >= 2 else None
        loader = parts[0].lower() if len(parts) >= 2 else None
        if not mc_ver:
            status.configure(text="Cannot determine MC version from instance name."); return

        headers = {"User-Agent": "SozipLauncher/1.1"}
        jars = [f for f in os.listdir(mods_dir) if f.endswith('.jar')]

        dep_cache = {}

        def get_version_info(project_slug_or_id):
            """Get (project_id, slug, deps) for a project by resolving the best version match."""
            cache_key = f"{project_slug_or_id}_{mc_ver}_{loader}"
            if cache_key in dep_cache:
                return dep_cache[cache_key]
            try:
                pr = requests.get(f"https://api.modrinth.com/v2/project/{project_slug_or_id}", headers=headers, timeout=10)
                if pr.status_code != 200:
                    return None
                pd = pr.json()
                pid = pd.get('id', project_slug_or_id)
                slug = pd.get('slug', pid)
                vr = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version", headers=headers, timeout=10)
                if vr.status_code != 200:
                    return None
                for v in vr.json():
                    gv = v.get('game_versions', [])
                    if mc_ver in gv and (not loader or loader == "vanilla" or loader in v.get('loaders', [])):
                        result = (pid, slug, v['dependencies'], v)
                        dep_cache[cache_key] = result
                        return result
            except:
                pass
            dep_cache[cache_key] = None
            return None

        def find_project_by_jar(jar_path):
            """Find project_id for a jar by reading its metadata and searching Modrinth."""
            name = self._get_mod_name(jar_path)
            stem = os.path.basename(jar_path).replace('.jar', '')
            if not name:
                name = stem.rsplit('-', 1)[0] if '-' in stem else stem
            queries = [name]
            if stem.lower() != name.lower():
                queries.append(stem)
            for q in queries:
                try:
                    r = requests.get(
                        f"https://api.modrinth.com/v2/search?query={requests.utils.quote(q)}&facets={requests.utils.quote(json.dumps([['project_type:mod']]))}&limit=5",
                        headers=headers, timeout=10
                    )
                    if r.status_code != 200:
                        continue
                    for hit in r.json().get("hits", []):
                        info = get_version_info(hit['slug'])
                        if info:
                            return info
                except:
                    continue
            return None

        def add_tree_line(text, color=TEXT_WHITE, indent=0):
            def _add():
                ctk.CTkLabel(tree_frame, text=("  " * indent) + text, font=(FONT, 9),
                             text_color=color, anchor="w", wraplength=600).pack(fill="x", padx=4, pady=1)
            self.after(0, _add)

        def run():
            installed_pids = {}
            dep_tree = {}
            resolved = {}
            failed = {}
            incompat_map = {}
            resolve_queue = []

            # Phase 1: Scan installed jars
            add_tree_line("Scanning installed mods...", TEXT_MUTED)
            for jar in jars:
                self.after(0, lambda j=jar: status.configure(text=f"Scanning {j[:45]}..."))
                info = find_project_by_jar(os.path.join(mods_dir, jar))
                if info:
                    pid, slug, deps, ver = info
                    installed_pids[pid] = jar
                    dep_tree[pid] = {"slug": slug, "jar": jar, "deps": deps, "version": ver}
                    add_tree_line(f"✓ {slug}", GREEN, 1)
                    for d in deps:
                        dt = d.get('dependency_type')
                        dpid = d.get('project_id')
                        if not dpid:
                            continue
                        if dt == "required":
                            resolve_queue.append((dpid, pid, slug))
                        elif dt == "incompatible":
                            incompat_map.setdefault(dpid, []).append(slug)

            add_tree_line(f"{len(jars)} mods scanned, {len(resolve_queue)} required deps found", TEXT_MUTED)

            # Phase 2: Recursively resolve and download deps
            visited = set()
            while resolve_queue:
                dpid, parent_pid, parent_slug = resolve_queue.pop(0)
                if dpid in visited or dpid in installed_pids:
                    continue
                visited.add(dpid)

                self.after(0, lambda p=dpid: status.configure(text=f"Resolving dep {p[:20]}..."))
                add_tree_line(f"↳ resolving {dpid[:20]}... (needed by {parent_slug})", TEXT_MUTED, 2)

                info = get_version_info(dpid)
                if not info:
                    failed[dpid] = (f"No {mc_ver}+{loader} version", parent_slug)
                    add_tree_line(f"✗ {dpid[:20]} — no matching version", RED, 2)
                    continue

                pid, slug, deps, ver = info
                add_tree_line(f"✓ {slug} ({ver.get('version_number', '?')})", GREEN, 2)

                try:
                    fi = ver['files'][0]
                    dl = requests.get(fi['url'], stream=True, timeout=30)
                    if dl.status_code != 200:
                        failed[pid] = ("Download failed", parent_slug)
                        add_tree_line(f"✗ {slug} — download failed", RED, 2)
                        continue
                    dst = os.path.join(mods_dir, fi['filename'])
                    with open(dst, 'wb') as f:
                        for chunk in dl.iter_content(8192):
                            f.write(chunk)
                    if os.path.getsize(dst) == 0:
                        os.remove(dst)
                        failed[pid] = ("Empty download", parent_slug)
                        continue
                    resolved[pid] = (fi['filename'], parent_slug)
                    dep_tree[pid] = {"slug": slug, "jar": fi['filename'], "deps": deps, "version": ver}
                    add_tree_line(f"  ✓ downloaded {fi['filename'][:45]}", GREEN, 3)
                except Exception as e:
                    failed[pid] = (str(e), parent_slug)
                    add_tree_line(f"✗ {slug} — {str(e)[:30]}", RED, 2)
                    continue

                # Enqueue this dep's own deps
                for d in deps:
                    if d.get('dependency_type') == "required" and d.get('project_id'):
                        sub_dpid = d['project_id']
                        if sub_dpid not in visited and sub_dpid not in installed_pids:
                            resolve_queue.append((sub_dpid, pid, slug))

            # Phase 3: Check incompatibilities
            incomp_found = []
            for inc_pid, sources in incompat_map.items():
                if inc_pid in installed_pids:
                    incomp_found.append(f"{installed_pids[inc_pid]} conflicts with {', '.join(sources)}")
                if inc_pid in resolved:
                    incomp_found.append(f"{resolved[inc_pid][0]} conflicts with {', '.join(sources)}")

            self.after(0, lambda: show_results(resolved, incomp_found, dep_tree))

        def show_results(resolved, incomp_found, dep_tree):
            for w in pop.winfo_children(): w.destroy()
            pop.resizable(True, True)
            pop.geometry("780x650")
            ctk.CTkLabel(pop, text="Dependency Check Complete", font=(FONT, 20, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 8))
            scroll = ctk.CTkScrollableFrame(pop, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
            scroll.pack(fill="both", expand=True, padx=15, pady=5)

            pid_name = {}
            for pid, pdata in dep_tree.items():
                pid_name[pid] = pdata.get("jar", pdata.get("slug", pid))
            for dpid, (fname, parent) in resolved.items():
                pid_name[dpid] = fname if fname else dpid
            for pid, pdata in dep_tree.items():
                for d in pdata.get("deps", []):
                    cpid = d.get("project_id")
                    if cpid and cpid not in pid_name:
                        pid_name[cpid] = cpid

            tree_children = {}
            for pid, pdata in dep_tree.items():
                if pid not in tree_children:
                    tree_children[pid] = []
                for d in pdata.get("deps", []):
                    if d.get('dependency_type') == "required" and d.get('project_id'):
                        tree_children[pid].append(d['project_id'])

            def render_tree(node_pid, depth=0, is_last=True, prefix=""):
                if depth > 0:
                    branch = "└── " if is_last else "├── "
                    connector = "    " if is_last else "│   "
                else:
                    branch = ""; connector = ""

                has_jar = node_pid in dep_tree and dep_tree[node_pid].get("jar")
                is_res = node_pid in resolved
                has_missing = node_pid in dep_tree and dep_tree[node_pid].get("missing")
                has_incompat = node_pid in dep_tree and dep_tree[node_pid].get("incompat")

                if has_incompat: color = RED; icon = "✗"
                elif has_missing: color = ORANGE; icon = "⚠"
                elif has_jar or is_res: color = GREEN; icon = "✓"
                else: color = TEXT_MUTED; icon = "?"

                display = pid_name.get(node_pid, node_pid[:20])
                row = ctk.CTkFrame(scroll, fg_color="transparent"); row.pack(fill="x")
                ctk.CTkLabel(row, text=f"{prefix}{branch}{icon} {display[:55]}", font=(FONT, 10, "bold" if depth == 0 else "normal"),
                             text_color=color, anchor="w").pack(fill="x", padx=(4, 0))

                if has_missing:
                    for mid, mslug in dep_tree[node_pid]["missing"]:
                        sub = ctk.CTkFrame(scroll, fg_color="transparent"); sub.pack(fill="x")
                        ctk.CTkLabel(sub, text=f"{prefix}{connector}  ⚠ Missing: {mslug[:35]}", font=(FONT, 9),
                                     text_color=TEXT_MUTED).pack(fill="x", padx=(12, 0))
                if has_incompat:
                    for srcs in dep_tree[node_pid]["incompat"]:
                        sub = ctk.CTkFrame(scroll, fg_color="transparent"); sub.pack(fill="x")
                        ctk.CTkLabel(sub, text=f"{prefix}{connector}  ✗ Incompatible with {', '.join(srcs[:2])}", font=(FONT, 9),
                                     text_color=RED).pack(fill="x", padx=(12, 0))

                children = tree_children.get(node_pid, [])
                if not children: return
                known = [c for c in children if c in resolved or c in dep_tree]
                unknown = [c for c in children if c not in known]
                all_kids = known + unknown
                for i, c in enumerate(all_kids):
                    render_tree(c, depth + 1, i == len(all_kids) - 1, prefix + connector)

            all_children = set()
            for ch_list in tree_children.values():
                all_children.update(ch_list)
            roots = [pid for pid in dep_tree if pid not in all_children]

            if roots:
                f = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER)
                f.pack(fill="x", pady=3)
                ctk.CTkLabel(f, text="📊 Dependency Tree", font=(FONT, 13, "bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=12, pady=(8, 4))
                for pid in roots:
                    render_tree(pid)

            installed_count = len(resolved)
            failed_count = len([k for k in dep_tree if dep_tree[k].get("missing")])
            if installed_count > 0:
                ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER).pack(fill="x", pady=3)
                ctk.CTkLabel(scroll, text=f"✓ {installed_count} dependencies installed", font=(FONT, 12, "bold"), text_color=GREEN, anchor="w").pack(fill="x", padx=12, pady=2)
            if incomp_found:
                ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=RED).pack(fill="x", pady=3)
                for s in incomp_found:
                    ctk.CTkLabel(scroll, text=f"✗ {s}", font=(FONT, 10), text_color=RED, anchor="w").pack(fill="x", padx=12, pady=1)

            ctk.CTkButton(pop, text="CLOSE", width=100, height=30, font=(FONT, 10, "bold"),
                         fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8, command=pop.destroy).pack(pady=(10, 15))

        threading.Thread(target=run, daemon=True).start()



    def draw_home(self):
        for w in self.content_area.winfo_children(): w.destroy()

        self.user_entry.bind("<FocusOut>", self.save_settings)
        self.user_entry.bind("<Return>", self.save_settings)

        header_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Dashboard", font=(FONT, 28, "bold"), text_color=TEXT_WHITE).pack(side="left")
        ctk.CTkLabel(header_frame, text="  PRO", font=(FONT, 11, "bold"), text_color=ACCENT).pack(side="left", pady=(6, 0))

        inst_path = os.path.join(self.base_path, "instances")
        os.makedirs(inst_path, exist_ok=True)
        downloaded = [f for f in os.listdir(inst_path) if os.path.isdir(os.path.join(inst_path, f))]

        if downloaded:
            if self.selected_version not in downloaded:
                self.selected_version = downloaded[0]

            card = ctk.CTkFrame(self.content_area, corner_radius=16, fg_color=BG_CARD, border_width=2, border_color=BORDER)
            card.pack(fill="x", pady=5)

            cur_ver_frame = ctk.CTkFrame(card, fg_color="transparent")
            cur_ver_frame.pack(fill="x", padx=25, pady=(20, 5))
            loader_type = self.selected_version.split('_')[0] if '_' in self.selected_version else "Vanilla"
            ctk.CTkLabel(cur_ver_frame, text="CURRENT VERSION", font=(FONT, 9, "bold"), text_color=TEXT_MUTED).pack(anchor="w")
            ver_row = ctk.CTkFrame(cur_ver_frame, fg_color="transparent")
            ver_row.pack(fill="x", pady=3)
            ctk.CTkLabel(ver_row, text=f"{self.selected_version}", font=(FONT, 20, "bold"), text_color=TEXT_WHITE).pack(side="left")
            badge = ctk.CTkFrame(ver_row, fg_color=ACCENT, corner_radius=6)
            badge.pack(side="left", padx=10, pady=3)
            ctk.CTkLabel(badge, text=loader_type.upper(), font=(FONT, 9, "bold"), text_color=TEXT_WHITE).pack(padx=8, pady=2)

            ctk.CTkButton(card, text="All Versions", font=(FONT, 11), height=28, fg_color="transparent", text_color=TEXT_WHITE, hover_color=BORDER, border_width=1, border_color=BORDER, corner_radius=8, command=self.draw_version_manager).pack(padx=25, pady=(5, 10), anchor="w")

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(pady=(15, 20))

            def mk_icon_btn(parent, text, color, cmd):
                return ctk.CTkButton(parent, text=text, width=46, height=54, font=(FONT, 16), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=10, command=cmd)

            mk_icon_btn(row, "📁", BG_DARK, lambda: open_folder(os.path.join(self.base_path, "instances", self.selected_version))).pack(side="left", padx=3)
            ctk.CTkButton(row, text="MODS", width=70, height=54, font=(FONT, 11, "bold"), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=10, border_width=1, border_color=BORDER, command=self.open_modrinth_browser).pack(side="left", padx=3)
            ctk.CTkButton(row, text="DEPS", width=65, height=54, font=(FONT, 11, "bold"), fg_color="#8b5cf6", hover_color="#7c3aed", corner_radius=10, command=self.check_dependencies).pack(side="left", padx=3)

            play_btn = ctk.CTkButton(row, text="▶  PLAY NOW", width=200, height=54, font=(FONT, 18, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=14, command=self.run_game)
            play_btn.pack(side="left", padx=3)

            ctk.CTkButton(row, text="NEWS", width=65, height=54, font=(FONT, 10, "bold"), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=10, border_width=1, border_color=BORDER, command=lambda: self.open_link("https://sozipp.github.io/sozip-launcher/news.html")).pack(side="left", padx=3)
            mk_icon_btn(row, "🗑", RED, self.delete_version).pack(side="left", padx=3)

        else:
            card = ctk.CTkFrame(self.content_area, corner_radius=16, fg_color=BG_CARD, border_width=2, border_color=BORDER)
            card.pack(fill="x", pady=5)
            ctk.CTkLabel(card, text="No instances installed", font=(FONT, 16, "bold"), text_color=TEXT_MUTED).pack(pady=(40, 5))
            ctk.CTkLabel(card, text="Go to Installer to get started!", font=(FONT, 12), text_color=TEXT_MUTED).pack(pady=5)
            ctk.CTkButton(card, text="Open Installer", font=(FONT, 12), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=10, command=self.draw_install_screen).pack(pady=20)

        footer_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=25)

        links = [
            ("Tutorial", "https://sozipp.github.io/sozip-launcher/tutorial.html"),
            ("Features", "https://sozipp.github.io/sozip-launcher/features.html"),
            ("Website", "https://sozipp.github.io/sozip-launcher/index.html"),
            ("Network", "https://sozipp.github.io/sozip-launcher/upload.html"),
            ("YouTube", "https://www.youtube.com/@sozip19op")
        ]
        for text, url in links:
            ctk.CTkButton(footer_frame, text=text, width=110, height=30, font=(FONT, 10), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, corner_radius=8, border_width=1, border_color=BORDER, command=lambda u=url: self.open_link(u)).pack(side="left", padx=8, expand=True)

    def elyby_logout(self):
        self.elyby_token = ""
        self.elyby_uuid = ""
        self.accounts = [a for a in self.accounts if a.get("type") != "elyby"]
        self.save_settings()
        self.draw_home()

    def show_elyby_login_popup(self):
        pop = ctk.CTkToplevel(self)
        pop.title("Ely.by Login")
        pop.geometry("380x200")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        pop.resizable(False, False)

        ctk.CTkLabel(pop, text="Ely.by Login", font=(FONT, 16, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 10))
        user_entry = ctk.CTkEntry(pop, placeholder_text="Email / Username", width=260, fg_color=BG_CARD, border_color=BORDER)
        user_entry.pack(pady=4)
        pass_entry = ctk.CTkEntry(pop, placeholder_text="Password", width=260, show="*", fg_color=BG_CARD, border_color=BORDER)
        pass_entry.pack(pady=4)

        def do_login():
            username = user_entry.get().strip()
            password = pass_entry.get()
            if not username or not password:
                messagebox.showwarning("Ely.by", "Enter username and password!")
                return
            def _login():
                try:
                    resp = requests.post("https://authserver.ely.by/auth/authenticate", json={
                        "username": username, "password": password,
                        "clientToken": uuid.uuid4().hex,
                        "requestUser": True
                    }, timeout=15)
                    if resp.status_code != 200:
                        err = resp.json().get('errorMessage', 'Unknown error')
                        self.after(0, lambda: messagebox.showerror("Ely.by", f"Login failed: {err}"))
                        return
                    data = resp.json()
                    self.elyby_token = data["accessToken"]
                    self.elyby_uuid = data["selectedProfile"]["id"]
                    self.username = data["selectedProfile"]["name"]
                    self.accounts = [a for a in self.accounts if a.get("type") != "elyby"]
                    self.accounts.append({"username": self.username, "type": "elyby"})
                    if hasattr(self, 'user_entry') and self.user_entry.winfo_exists():
                        self.user_entry.delete(0, "end")
                        self.user_entry.insert(0, self.username)
                    self.save_settings()
                    self.after(0, pop.destroy)
                    self.after(0, self.draw_home)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Ely.by", f"Connection error: {e}"))
            threading.Thread(target=_login, daemon=True).start()

        ctk.CTkButton(pop, text="Login", font=(FONT, 12, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6, command=do_login).pack(pady=12)

    def draw_version_manager(self):
        for w in self.content_area.winfo_children(): w.destroy()
        header = ctk.CTkFrame(self.content_area, fg_color="transparent"); header.pack(fill="x")
        ctk.CTkLabel(header, text="All Versions", font=(FONT, 28, "bold"), text_color=TEXT_WHITE).pack(side="left")
        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")
        ctk.CTkButton(btn_row, text="←  Back", font=(FONT, 12), width=80, height=32, fg_color="transparent", text_color=TEXT_WHITE, hover_color=BORDER, border_width=1, border_color=BORDER, corner_radius=8, command=self.draw_home).pack(side="left")

        inst_path = os.path.join(self.base_path, "instances")
        os.makedirs(inst_path, exist_ok=True)
        versions = sorted([f for f in os.listdir(inst_path) if os.path.isdir(os.path.join(inst_path, f))])

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
        scroll.pack(fill="both", expand=True, pady=10)

        if not versions:
            ctk.CTkLabel(scroll, text="No versions installed.", font=(FONT, 14), text_color=TEXT_MUTED).pack(pady=40)
            return

        for v in versions:
            loader = v.split('_')[0] if '_' in v else "Vanilla"
            card = ctk.CTkFrame(scroll, corner_radius=12, fg_color=BG_CARD, border_width=2, border_color=BORDER)
            card.pack(fill="x", pady=5)
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            ctk.CTkLabel(info, text=v, font=(FONT, 14, "bold"), text_color=TEXT_WHITE, anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"Loader: {loader}", font=(FONT, 10), text_color=TEXT_MUTED, anchor="w").pack(fill="x")
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            ctk.CTkButton(btn_frame, text="Select", width=64, height=28, font=(FONT, 9, "bold"), fg_color=GREEN, hover_color="#27ae60", corner_radius=6, command=lambda x=v: [setattr(self, 'selected_version', x), self.save_settings(), self.draw_home()]).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Rename", width=64, height=28, font=(FONT, 9), fg_color=ORANGE, hover_color="#e67e22", corner_radius=6, command=lambda x=v: self.rename_version(x)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Delete", width=64, height=28, font=(FONT, 9), fg_color=RED, hover_color="#c0392b", corner_radius=6, command=lambda x=v: self.delete_version_from_manager(x, scroll)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Migrate", width=72, height=28, font=(FONT, 9, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6, command=lambda x=v: self.open_migration_wizard(x)).pack(side="left", padx=2)

    def rename_version(self, old_name):
        pop = ctk.CTkToplevel(self); pop.geometry("380x180"); pop.title("Rename Version"); pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        ctk.CTkLabel(pop, text=f"Rename '{old_name}'", font=(FONT, 18, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 15))
        entry = ctk.CTkEntry(pop, width=300, fg_color=BG_CARD, border_color=BORDER)
        entry.insert(0, old_name)
        entry.pack(pady=5)
        def do_rename():
            new_name = entry.get().strip()
            if new_name and new_name != old_name:
                old_path = os.path.join(self.base_path, "instances", old_name)
                new_path = os.path.join(self.base_path, "instances", new_name)
                if os.path.exists(new_path):
                    messagebox.showerror("Error", "Name already exists!")
                    return
                os.rename(old_path, new_path)
                if self.selected_version == old_name:
                    self.selected_version = new_name
                self.save_settings()
            pop.destroy(); self.draw_version_manager()
        ctk.CTkButton(pop, text="Rename", font=(FONT, 12), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8, command=do_rename).pack(pady=12)

    def delete_version_from_manager(self, name, scroll_frame):
        if messagebox.askyesno("Delete", f"Delete '{name}'?"):
            shutil.rmtree(os.path.join(self.base_path, "instances", name), ignore_errors=True)
            if self.selected_version == name:
                inst_path = os.path.join(self.base_path, "instances")
                remaining = [f for f in os.listdir(inst_path) if os.path.isdir(os.path.join(inst_path, f))]
                self.selected_version = remaining[0] if remaining else None
            self.draw_version_manager()

    def open_migration_wizard(self, source):
        pop = ctk.CTkToplevel(self)
        pop.geometry("480x420")
        pop.title(f"Migrate — {source}")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        pop.resizable(False, False)

        ctk.CTkLabel(pop, text=f"Migrate from {source}", font=(FONT, 18, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 5))
        ctk.CTkLabel(pop, text="Select what to migrate:", font=(FONT, 11), text_color=TEXT_MUTED).pack()

        options = {}
        opts = [
            ("world", "WORLD", "All saves (overworld, nether, end)"),
            ("shaders", "SHADERS", "Shader packs folder"),
            ("resourcepacks", "RESOURCEPACK", "Resource packs folder"),
            ("settings", "GAME SETTINGS", "Options, servers, hotbar, etc."),
            ("mods", "MODS", "Check + install compatible mods via Modrinth"),
        ]
        frame = ctk.CTkFrame(pop, fg_color="transparent")
        frame.pack(pady=10)
        for key, label, desc in opts:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            var = ctk.BooleanVar(value=True)
            options[key] = var
            ctk.CTkCheckBox(row, text=label, variable=var, font=(FONT, 12, "bold"), text_color=TEXT_WHITE,
                            fg_color=ACCENT, hover_color=ACCENT_HOVER, checkmark_color="white").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=(FONT, 9), text_color=TEXT_MUTED).pack(side="left", padx=10)

        def on_next():
            chosen = {k for k, v in options.items() if v.get()}
            if not chosen:
                messagebox.showwarning("Warning", "Select at least one item!", parent=pop)
                return
            pop.destroy()
            self._migration_target_step(source, chosen)

        ctk.CTkButton(pop, text="NEXT →", width=140, height=36, font=(FONT, 12, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8, command=on_next).pack(pady=(10, 20))

    def _migration_target_step(self, source, options):
        inst_path = os.path.join(self.base_path, "instances")
        targets = sorted([f for f in os.listdir(inst_path) if os.path.isdir(os.path.join(inst_path, f)) and f != source])
        if not targets:
            messagebox.showerror("Error", "No other versions installed to migrate to.")
            return

        pop = ctk.CTkToplevel(self)
        pop.geometry("500x450")
        pop.title(f"Migrate to...")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)

        ctk.CTkLabel(pop, text=f"Select target version", font=(FONT, 18, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 5))
        ctk.CTkLabel(pop, text=f"Source: {source}", font=(FONT, 11), text_color=TEXT_MUTED).pack()
        scroll = ctk.CTkScrollableFrame(pop, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
        scroll.pack(fill="both", expand=True, padx=15, pady=10)

        for v in targets:
            loader = v.split('_')[0] if '_' in v else "Vanilla"
            card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=BG_CARD, border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=3)
            ctk.CTkLabel(card, text=v, font=(FONT, 13, "bold"), text_color=TEXT_WHITE).pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(card, text=loader, font=(FONT, 9), text_color=TEXT_MUTED).pack(side="left", padx=5)
            ctk.CTkButton(card, text="SELECT", width=72, height=28, font=(FONT, 9, "bold"),
                          fg_color=GREEN, hover_color="#27ae60", corner_radius=6,
                          command=lambda t=v: [pop.destroy(), self._run_migration(source, t, options)]).pack(side="right", padx=10)

    def _run_migration(self, source, target, options):
        pop, bar, label = self._make_download_popup(f"Migrating {source} → {target}")
        src_path = os.path.join(self.base_path, "instances", source)
        tgt_path = os.path.join(self.base_path, "instances", target)
        report = []

        def run():
            try:
                if "world" in options:
                    label.configure(text="Migrating worlds...")
                    src_saves = os.path.join(src_path, "saves")
                    tgt_saves = os.path.join(tgt_path, "saves")
                    if os.path.exists(src_saves):
                        shutil.copytree(src_saves, tgt_saves, dirs_exist_ok=True)
                        for w in os.listdir(src_saves):
                            report.append(f"✓ World: {w}")

                if "shaders" in options:
                    label.configure(text="Migrating shaders...")
                    src_sh = os.path.join(src_path, "shaderpacks")
                    tgt_sh = os.path.join(tgt_path, "shaderpacks")
                    if os.path.exists(src_sh):
                        shutil.copytree(src_sh, tgt_sh, dirs_exist_ok=True)
                        for f in os.listdir(src_sh):
                            report.append(f"✓ Shader: {f}")

                if "resourcepacks" in options:
                    label.configure(text="Migrating resource packs...")
                    src_rp = os.path.join(src_path, "resourcepacks")
                    tgt_rp = os.path.join(tgt_path, "resourcepacks")
                    if os.path.exists(src_rp):
                        shutil.copytree(src_rp, tgt_rp, dirs_exist_ok=True)
                        for f in os.listdir(src_rp):
                            report.append(f"✓ Resourcepack: {f}")

                if "settings" in options:
                    label.configure(text="Migrating settings...")
                    for fname in ["options.txt", "optionsof.txt", "servers.dat", "hotbar.nbt", "splashes.dat"]:
                        src_f = os.path.join(src_path, fname)
                        if os.path.exists(src_f):
                            shutil.copy2(src_f, os.path.join(tgt_path, fname))
                            report.append(f"✓ Settings: {fname}")

                if "mods" in options:
                    label.configure(text="Migrating mods (checking compatibility)...")
                    self._migrate_mods(src_path, tgt_path, label, report)

                if "plugins" in options:
                    label.configure(text="Migrating plugins (checking compatibility)...")
                    self._migrate_plugins(src_path, tgt_path, label, report)

                pop.destroy()
                self.after(0, lambda: self._show_migration_report(source, target, report))
            except Exception as e:
                pop.destroy()
                self.after(0, lambda: messagebox.showerror("Migration Error", str(e), parent=self))

        threading.Thread(target=run, daemon=True).start()

    def _show_migration_report(self, source, target, report):
        pop = ctk.CTkToplevel(self)
        pop.geometry("600x520")
        pop.title("Migration Complete")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)

        ctk.CTkLabel(pop, text="Migration Complete", font=(FONT, 20, "bold"), text_color=TEXT_WHITE).pack(pady=(20, 2))
        ctk.CTkLabel(pop, text=f"{source}  →  {target}", font=(FONT, 12), text_color=ACCENT).pack()

        main_scroll = ctk.CTkScrollableFrame(pop, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
        main_scroll.pack(fill="both", expand=True, padx=15, pady=10)

        success = [r for r in report if r.startswith("✓")]
        failed = [r for r in report if r.startswith("⚠")]

        if success:
            frame_s = ctk.CTkFrame(main_scroll, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER)
            frame_s.pack(fill="x", pady=4)
            head_s = ctk.CTkFrame(frame_s, fg_color="transparent")
            head_s.pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(head_s, text=f"✓ Migrated Successfully ({len(success)})", font=(FONT, 12, "bold"), text_color=GREEN).pack(side="left")
            scroll_s = ctk.CTkScrollableFrame(frame_s, fg_color="transparent", height=min(220, len(success) * 22 + 10), scrollbar_button_hover_color=ACCENT)
            scroll_s.pack(fill="x", padx=6, pady=(0, 6))
            for item in success:
                ctk.CTkLabel(scroll_s, text=item, font=(FONT, 10), text_color=TEXT_WHITE, anchor="w").pack(fill="x", padx=6, pady=1)

        if failed:
            frame_f = ctk.CTkFrame(main_scroll, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER)
            frame_f.pack(fill="x", pady=4)
            head_f = ctk.CTkFrame(frame_f, fg_color="transparent")
            head_f.pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(head_f, text=f"⚠ Could Not Be Migrated ({len(failed)})", font=(FONT, 12, "bold"), text_color=ORANGE).pack(side="left")
            scroll_f = ctk.CTkScrollableFrame(frame_f, fg_color="transparent", height=min(220, len(failed) * 22 + 10), scrollbar_button_hover_color=ACCENT)
            scroll_f.pack(fill="x", padx=6, pady=(0, 6))
            for item in failed:
                ctk.CTkLabel(scroll_f, text=item, font=(FONT, 10), text_color=TEXT_MUTED, anchor="w").pack(fill="x", padx=6, pady=1)

        if not success and not failed:
            ctk.CTkLabel(main_scroll, text="Nothing was migrated.", font=(FONT, 12), text_color=TEXT_MUTED).pack(pady=20)

        ctk.CTkLabel(pop, text=f"Total: {len(report)} items", font=(FONT, 10), text_color=TEXT_MUTED).pack(pady=(0, 12))
        ctk.CTkButton(pop, text="CLOSE", width=100, height=30, font=(FONT, 10, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8, command=pop.destroy).pack(pady=(0, 15))

    def _migrate_mods(self, src_path, tgt_path, label, report):
        src_mods = os.path.join(src_path, "mods")
        tgt_mods = os.path.join(tgt_path, "mods")
        if not os.path.exists(src_mods):
            return
        os.makedirs(tgt_mods, exist_ok=True)

        parts = os.path.basename(tgt_path).split('_')
        if len(parts) < 2:
            report.append("⚠ Target has no MC version in name, skipping mods")
            return
        target_loader = parts[0].lower()
        target_mc = parts[1]

        jars = [f for f in os.listdir(src_mods) if f.endswith('.jar')]
        headers = {"User-Agent": "SozipLauncher/1.1"}
        total = len(jars)
        done = [0]
        lock = threading.Lock()

        def _find_mod_on_modrinth(query):
            r = requests.get(
                f"https://api.modrinth.com/v2/search"
                f"?query={requests.utils.quote(query)}"
                f"&facets={requests.utils.quote(json.dumps([['project_type:mod']]))}"
                f"&limit=5",
                headers=headers, timeout=10
            )
            return r.json().get("hits", []) if r.status_code == 200 else []

        def resolve_one(jar):
            jar_path = os.path.join(src_mods, jar)
            mod_id = self._get_mod_name(jar_path)
            queries = []
            if mod_id:
                queries.append(mod_id)
            name_part = jar.rsplit('-', 1)[0] if '-' in jar else jar.replace('.jar', '')
            if name_part and name_part != mod_id:
                queries.append(name_part)
            stem = jar.replace('.jar', '')
            if stem not in queries:
                queries.append(stem)

            for query in queries:
                try:
                    hits = _find_mod_on_modrinth(query)
                    if not hits:
                        continue

                    for hit in hits:
                        slug = hit["slug"]
                        vr = requests.get(
                            f"https://api.modrinth.com/v2/project/{slug}/version",
                            headers=headers, timeout=10
                        )
                        if vr.status_code != 200:
                            continue
                        vers = vr.json()
                        if not isinstance(vers, list) or not vers:
                            continue

                        # EXACT match: target MC version + target loader
                        match = None
                        for v in vers:
                            gv = v.get('game_versions', [])
                            loaders = v.get('loaders', [])
                            if target_mc in gv:
                                if target_loader == "vanilla":
                                    if not loaders or all(l == "vanilla" for l in loaders):
                                        match = v
                                        break
                                elif target_loader in loaders:
                                    match = v
                                    break

                        if not match:
                            continue

                        fi = match["files"][0]
                        dl = requests.get(fi["url"], stream=True, timeout=60)
                        if dl.status_code != 200:
                            continue

                        out_path = os.path.join(tgt_mods, fi["filename"])
                        with open(out_path, "wb") as f:
                            for chunk in dl.iter_content(8192):
                                f.write(chunk)

                        if os.path.getsize(out_path) == 0:
                            os.remove(out_path)
                            continue

                        return (f"✓ Mod: {fi['filename']}", jar)

                except Exception:
                    continue

            return (f"⚠ No {target_loader}+{target_mc} version: {jar}", jar)

        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=8) as ex:
            fut_map = {ex.submit(resolve_one, jar): jar for jar in jars}
            for fut in as_completed(fut_map):
                with lock:
                    done[0] += 1
                    label.configure(text=f"Mods ({done[0]}/{total}): {fut_map[fut][:40]}")
                result, _ = fut.result()
                report.append(result)

    def _get_mod_name(self, jar_path):
        try:
            with zipfile.ZipFile(jar_path, 'r') as z:
                if 'fabric.mod.json' in z.namelist():
                    data = json.loads(z.read('fabric.mod.json'))
                    return data.get('name', data.get('id', ''))

                for toml_path in ['META-INF/mods.toml', 'META-INF/neoforge.mods.toml']:
                    if toml_path in z.namelist():
                        text = z.read(toml_path).decode('utf-8')
                        # Try to find [[mods]] array entries first
                        mods_blocks = re.split(r'^\s*\[\[mods\]\]\s*$', text, flags=re.MULTILINE)
                        if len(mods_blocks) > 1:
                            # Parse each [[mods]] block
                            for block in mods_blocks[1:]:
                                dn = self._parse_toml_value(block, 'displayName')
                                if dn:
                                    return dn
                                mid = self._parse_toml_value(block, 'modId')
                                if mid:
                                    return mid
                        # Fallback: top-level keys (older format)
                        dn = self._parse_toml_value(text, 'displayName')
                        if dn:
                            return dn
                        mid = self._parse_toml_value(text, 'modId')
                        if mid:
                            return mid

                if 'mcmod.info' in z.namelist():
                    data = json.loads(z.read('mcmod.info'))
                    if isinstance(data, list) and data:
                        return data[0].get('name', '')
        except:
            pass
        return None

    def _parse_toml_value(self, text, key):
        """Extract a TOML key's value, supporting quoted and single-quoted strings."""
        m = re.search(rf'^{key}\s*=\s*"([^"]*)"', text, re.MULTILINE)
        if m:
            return m.group(1)
        m = re.search(rf"^{key}\s*=\s*'([^']*)'", text, re.MULTILINE)
        if m:
            return m.group(1)
        return None

    def _migrate_plugins(self, src_path, tgt_path, label, report):
        src_plugins = os.path.join(src_path, "plugins")
        tgt_plugins = os.path.join(tgt_path, "plugins")
        if not os.path.exists(src_plugins):
            return
        os.makedirs(tgt_plugins, exist_ok=True)

        parts = os.path.basename(tgt_path).split('_')
        mc_ver = parts[1] if len(parts) >= 2 else None

        headers = {"User-Agent": "SozipLauncher/1.1"}
        jars = [f for f in os.listdir(src_plugins) if f.endswith('.jar')]
        for i, jar in enumerate(jars):
            label.configure(text=f"Checking plugin ({i+1}/{len(jars)}): {jar[:50]}")
            jar_path = os.path.join(src_plugins, jar)
            plugin_name = self._get_plugin_name(jar_path)
            if not plugin_name:
                plugin_name = jar.rsplit('-', 1)[0] if '-' in jar else jar.replace('.jar', '')

            installed = False
            # Try Spiget first
            try:
                resp = requests.get(
                    f"https://api.spiget.org/v2/search/resources/{plugin_name}?field=name&size=3",
                    headers=headers, timeout=10
                )
                if resp.status_code == 200 and resp.text.strip():
                    results = resp.json()
                    if results and not results[0].get('premium'):
                        item = results[0]
                        res_id = item['id']
                        tested = item.get('testedVersions', [])
                        if not mc_ver or not tested or mc_ver in tested:
                            label.configure(text=f"Downloading {plugin_name[:60]}...")
                            dl = requests.get(f"https://api.spiget.org/v2/resources/{res_id}/download",
                                              headers=headers, stream=True, timeout=20)
                            if dl.status_code == 200:
                                dest = os.path.join(tgt_plugins, f"{plugin_name}.jar")
                                with open(dest, 'wb') as f:
                                    for chunk in dl.iter_content(8192):
                                        f.write(chunk)
                                report.append(f"✓ Plugin: {plugin_name}")
                                installed = True
            except:
                pass

            if installed:
                continue

            # Fallback: try Modrinth
            label.configure(text=f"Trying Modrinth for {plugin_name[:50]}...")
            try:
                facets = json.dumps([["project_type:mod"], ["categories:bukkit"]])
                params = {"query": plugin_name, "facets": facets, "limit": 3}
                search = requests.get("https://api.modrinth.com/v2/search", params=params).json()
                hits = search.get('hits', [])
                if hits:
                    slug = hits[0]['slug']
                    vers = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version").json()
                    match = self._find_best_version(vers, mc_ver, "bukkit") if mc_ver else None
                    if match:
                        fi = match['files'][0]
                        label.configure(text=f"Downloading {fi['filename'][:60]}...")
                        r = requests.get(fi['url'], stream=True)
                        with open(os.path.join(tgt_plugins, fi['filename']), 'wb') as f:
                            for chunk in r.iter_content(8192):
                                f.write(chunk)
                        report.append(f"✓ Plugin: {fi['filename']}")
                        installed = True
            except:
                pass

            if not installed:
                report.append(f"⚠ No compatible version: {jar}")

    def _get_plugin_name(self, jar_path):
        try:
            with zipfile.ZipFile(jar_path, 'r') as z:
                if 'plugin.yml' in z.namelist():
                    text = z.read('plugin.yml').decode('utf-8')
                    m = re.search(r'^name:\s*(.+)', text, re.MULTILINE)
                    if m:
                        return m.group(1).strip().strip('"\'')
        except:
            pass
        return None

    def draw_install_screen(self):
        self.current_mode = "release"; self.setup_installer_view("INSTALLER")
        threading.Thread(target=self.get_versions_thread, daemon=True).start()

    def draw_snapshot_screen(self):
        self.current_mode = "snapshot"; self.setup_installer_view("SNAPSHOTS")
        threading.Thread(target=self.get_versions_thread, daemon=True).start()

    def setup_installer_view(self, title):
        for w in self.content_area.winfo_children(): w.destroy()
        header = ctk.CTkFrame(self.content_area, fg_color="transparent"); header.pack(fill="x")
        ctk.CTkLabel(header, text=title, font=(FONT, 28, "bold"), text_color=TEXT_WHITE).pack(side="left")
        self.search_var = ctk.StringVar(); self.search_var.trace_add("write", self.filter_versions)
        ctk.CTkEntry(header, placeholder_text="Search versions...", width=250, textvariable=self.search_var, fg_color=BG_CARD, border_color=BORDER, corner_radius=6).pack(side="right", pady=10)
        self.scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent", scrollbar_button_hover_color=ACCENT); self.scroll.pack(fill="both", expand=True, pady=10)
        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading..."); self.loading_lbl.pack(pady=20)
        self.batch_size = 50
        self.displayed_count = 0
        self.show_more_btn = None

    def get_versions_thread(self):
        try:
            self.full_version_list = [v for v in minecraft_launcher_lib.utils.get_version_list() if v['type'] == self.current_mode]
            self.after(0, self.loading_lbl.destroy)
            self.after(0, lambda: self.render_list(self.full_version_list))
        except:
            self.after(0, lambda: self.loading_lbl.configure(text="Error!"))

    def filter_versions(self, *args):
        query = self.search_var.get().lower()
        filtered = [v for v in self.full_version_list if query in v['id'].lower()]
        self.render_list(filtered)

    def render_list(self, data):
        for w in self.scroll.winfo_children(): w.destroy()
        self.displayed_count = 0
        self._render_batch(data)

    def _render_batch(self, data):
        batch = data[self.displayed_count:self.displayed_count + self.batch_size]
        for v in batch:
            card = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=2, border_color=BORDER)
            card.pack(fill="x", pady=5)
            v_id = v['id']
            header_row = ctk.CTkFrame(card, fg_color="transparent")
            header_row.pack(fill="x", padx=18, pady=(14, 4))
            ctk.CTkLabel(header_row, text=f"Minecraft", font=(FONT, 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(header_row, text=v_id, font=(FONT, 18, "bold"), text_color=TEXT_WHITE).pack(anchor="w")
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=16, pady=(4, 12))
            ctk.CTkButton(btn_frame, text="▸ Vanilla", width=90, height=30, font=(FONT, 10, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8, command=lambda x=v_id: self.start_download(x, "Vanilla")).pack(side="left", padx=3)
            if self.current_mode == "release":
                if supports_forge(v_id):
                    ctk.CTkButton(btn_frame, text="▸ Forge", width=90, height=30, font=(FONT, 10, "bold"), fg_color="#e67e22", hover_color="#d35400", corner_radius=8, command=lambda x=v_id: self.start_download(x, "Forge")).pack(side="left", padx=3)
                if supports_fabric(v_id):
                    ctk.CTkButton(btn_frame, text="▸ Fabric", width=90, height=30, font=(FONT, 10, "bold"), fg_color="#3498db", hover_color="#2980b9", corner_radius=8, command=lambda x=v_id: self.start_download(x, "Fabric")).pack(side="left", padx=3)
                if supports_neoforge(v_id):
                    ctk.CTkButton(btn_frame, text="▸ NeoForge", width=100, height=30, font=(FONT, 10, "bold"), fg_color="#d4a017", hover_color="#b8890d", corner_radius=8, command=lambda x=v_id: self.start_download(x, "NeoForge")).pack(side="left", padx=3)
        self.displayed_count += len(batch)
        remaining = len(data) - self.displayed_count
        if self.show_more_btn and self.show_more_btn.winfo_exists():
            self.show_more_btn.destroy()
            self.show_more_btn = None
        if remaining > 0:
            self.show_more_btn = ctk.CTkButton(
                self.scroll, text=f"Show {min(self.batch_size, remaining)} more ({remaining} left)",
                font=(FONT, 11), fg_color=BG_CARD, hover_color=BORDER, corner_radius=8, command=lambda d=data: self._render_batch(d)
            )
            self.show_more_btn.pack(pady=8)

    def start_download(self, version, mtype):
        if self.is_installing: return
        self.is_installing = True

        pop = ctk.CTkToplevel(self)
        pop.geometry("480x280")
        pop.title(f"Installing {mtype}")
        pop.attributes("-topmost", True)
        pop.configure(fg_color=BG_DARK)
        pop.resizable(False, False)

        ctk.CTkLabel(pop, text=f"Installing {mtype} {version}", font=(FONT, 20, "bold"), text_color=TEXT_WHITE).pack(pady=(30, 15))

        bar = ctk.CTkProgressBar(pop, width=380, fg_color="#1e1e3a", progress_color=ACCENT, height=6, corner_radius=3)
        bar.set(0)
        bar.pack(pady=(10, 10))

        lbl = ctk.CTkLabel(pop, text="Initializing...", font=(FONT, 12), text_color=TEXT_MUTED)
        lbl.pack(pady=5)
        
        # Smooth Animation Variables
        progress_data = {"max": 0, "current": 0}

        def run_installation():
            instance_name = f"{mtype}_{version}"
            path = os.path.join(self.base_path, "instances", instance_name)
            
            # --- NEW: RETRY LOGIC VARIABLES ---
            max_retries = 5  # Try 5 times before giving up
            retry_delay = 3  # Wait 3 seconds between attempts
            
            for attempt in range(max_retries):
                try:
                    # Setup Callbacks
                    current_max = 0
                    def set_status(status):
                        self.after(0, lambda: lbl.configure(text=f"(Attempt {attempt+1}) {status}"))

                    def set_progress(progress):
                        nonlocal current_max
                        try:
                            val = float(progress) / float(current_max) if float(current_max) > 0 else 0
                        except (ValueError, TypeError, ZeroDivisionError):
                            val = 0
                        self.after(0, lambda v=val: bar.set(v))

                    def set_max(new_max):
                        nonlocal current_max
                        try:
                            current_max = float(new_max)
                        except (ValueError, TypeError):
                            current_max = 1

                    callback = {"setStatus": set_status, "setProgress": set_progress, "setMax": set_max}

                    # Clean start only on the first attempt
                    if attempt == 0:
                        if os.path.exists(path):
                            shutil.rmtree(path, ignore_errors=True)
                        os.makedirs(path, exist_ok=True)

                    # 1. Base Minecraft Installation
                    minecraft_launcher_lib.install.install_minecraft_version(version, path, callback=callback)
                    
                    # 2. Loader Logic
                    if mtype == "Forge":
                        f_ver = minecraft_launcher_lib.forge.find_forge_version(version)
                        if f_ver:
                            minecraft_launcher_lib.forge.install_forge_version(f_ver, path, callback=callback)
                    elif mtype == "Fabric":
                        minecraft_launcher_lib.fabric.install_fabric(version, path, callback=callback)
                    elif mtype == "NeoForge":
                        try:
                            from portablemc.standard import Context
                            from portablemc.forge import _NeoForgeVersion
                            from pathlib import Path
                        except ImportError:
                            raise Exception("NeoForge support requires portablemc.\nRun: pip install portablemc")
                        c = Context(main_dir=Path(path), work_dir=Path(path))
                        nf = _NeoForgeVersion(version, context=c)
                        nf.install()
                    
                    # If it reaches here, it succeeded!
                    self.is_installing = False
                    self.after(0, pop.destroy)
                    self.after(0, self.draw_home)
                    messagebox.showinfo("Success", f"{instance_name} installed!")
                    return # Exit the loop and function

                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay) # Wait before trying again
                        continue 
                    else:
                        # Out of retries
                        self.is_installing = False
                        self.after(0, pop.destroy)
                        messagebox.showerror("Install Error", f"Failed after {max_retries} attempts: {e}")

        threading.Thread(target=run_installation, daemon=True).start()

        
    def get_auth_injector(self, download_ui=None):
        injector_path = os.path.join(self.base_path, "authlib-injector.jar")
        if not os.path.exists(injector_path):
            import threading, time as _time

            own_popup = False
            if download_ui is None:
                pop, bar, label = self._make_download_popup("Downloading authlib-injector...")
                own_popup = True
            else:
                pop, bar, label = download_ui
                self.after(0, lambda: label.configure(text="Downloading authlib-injector..."))
            pop.grab_set()
            pop.update_idletasks()

            result = {"path": None}
            done = threading.Event()

            def task():
                try:
                    try:
                        api_url = "https://api.github.com/repos/yushijinhun/authlib-injector/releases/latest"
                        headers = {"Accept": "application/json", "User-Agent": "SozipLauncher/1.0"}
                        r = requests.get(api_url, timeout=15, headers=headers)
                        if r.status_code == 200:
                            assets = r.json().get("assets", [])
                            for a in assets:
                                name = a["name"]
                                if name.endswith(".jar") and "javadoc" not in name and "sources" not in name:
                                    dl_url = a["browser_download_url"]
                                    r2 = requests.get(dl_url, timeout=30, stream=True)
                                    with open(injector_path, "wb") as f:
                                        for chunk in r2.iter_content(8192):
                                            f.write(chunk)
                                    if r2.status_code == 200 and os.path.getsize(injector_path) > 10000:
                                        result["path"] = injector_path
                                        return
                    except:
                        pass
                    try:
                        url = "https://github.com/yushijinhun/authlib-injector/releases/download/v1.2.5/authlib-injector-1.2.5.jar"
                        r = requests.get(url, timeout=30, stream=True)
                        with open(injector_path, "wb") as f:
                            for chunk in r.iter_content(8192):
                                f.write(chunk)
                        if r.status_code == 200 and os.path.getsize(injector_path) > 10000:
                            result["path"] = injector_path
                    except:
                        pass
                finally:
                    done.set()

            threading.Thread(target=task, daemon=True).start()

            while not done.is_set():
                pop.update()
                _time.sleep(0.05)

            if own_popup:
                pop.destroy()

            if result["path"] is None:
                messagebox.showerror("Auth Error", "Failed to download authlib-injector. Check your internet connection.")
            return result["path"]
        return injector_path


    def get_launch_id(self, path):
        v_dir = os.path.join(path, "versions")
        if not os.path.exists(v_dir): return None
        ids = []
        for root, dirs, files in os.walk(v_dir):
            for f in files:
                if f.endswith(".json"):
                    ids.append(f.replace(".json", ""))
        if not ids: return None
        # Prioritize Forge/Fabric over Vanilla
        return next((v for v in ids if 'neoforge' in v.lower() or 'forge' in v.lower() or 'fabric' in v.lower()), ids[0])
	
    def copy_server_port(self, folder):
    	port = self.server_ports.get(folder)
    	if port:
            self.clipboard_clear()
            self.clipboard_append(str(port))
            self.update()
            messagebox.showinfo("Copied", f"Server port {port} copied to clipboard!")
  

    

    def open_modrinth_browser(self):
        if not self.selected_version:
            messagebox.showwarning("Warning", "Please select a version first!", parent=self)
            return

        self.mod_pop = ctk.CTkToplevel(self)
        self.mod_pop.geometry("1000x800")
        self.mod_pop.title("Sozip Modrinth Browser")
        self.mod_pop.attributes("-topmost", True)
        self.mod_pop.focus_set()
        self.mod_pop.configure(fg_color=BG_DARK)

        ctrl_frame = ctk.CTkFrame(self.mod_pop, fg_color=BG_CARD, corner_radius=12)
        ctrl_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(ctrl_frame, text="Type:", font=(FONT, 11), text_color=TEXT_WHITE).pack(side="left", padx=5)
        self.mod_type = ctk.CTkComboBox(ctrl_frame, values=["mod", "modpack", "resourcepack", "shader"],
                                       fg_color=BG_DARK, border_color=BORDER, button_color=ACCENT, button_hover_color=ACCENT_HOVER, dropdown_fg_color=BG_CARD,
                                       command=lambda _: self.search_now(), state="readonly")
        self.mod_type.pack(side="left", padx=5)

        instance_ver = self.selected_version.split('_')[-1]
        self.current_mc_version = instance_ver
        ctk.CTkLabel(ctrl_frame, text=f"MC: {instance_ver}", font=(FONT, 12, "bold"), text_color=ACCENT).pack(side="left", padx=(15, 5))

        self.loader_container = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        ctk.CTkLabel(self.loader_container, text="Software:", font=(FONT, 11), text_color=TEXT_WHITE).pack(side="left", padx=5)
        self.loader_opt = ctk.CTkComboBox(self.loader_container, values=["All", "fabric", "forge", "neoforge"],
                                         fg_color=BG_DARK, border_color=BORDER, button_color=ACCENT, button_hover_color=ACCENT_HOVER, dropdown_fg_color=BG_CARD,
                                         command=lambda _: self.search_now(), state="readonly")
        self.loader_opt.pack(side="left", padx=5)

        self.search_val = ctk.CTkEntry(ctrl_frame, placeholder_text="Search Modrinth...", width=180, fg_color=BG_CARD, border_color=BORDER)
        self.search_val.pack(side="left", padx=10)
        self.search_val.bind("<Return>", lambda e: self.search_now())

        ctk.CTkButton(ctrl_frame, text="SEARCH", width=80, fg_color="#3498db", 
                      command=self.search_now).pack(side="left", padx=5)

        self.results_frame = ctk.CTkScrollableFrame(self.mod_pop)
        self.results_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.update_modrinth_ui()
        self.search_now()

    def update_modrinth_ui(self):
        if self.mod_type.get() == "mod":
            self.loader_container.pack(side="left", padx=5)
        else:
            self.loader_container.pack_forget()
            self.loader_opt.set("All")

    def search_now(self):
        self.update_modrinth_ui()
        for w in self.results_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.results_frame, text="Searching Modrinth...").pack(pady=20)
        
        def run_query():
            query = self.search_val.get()
            m_type = self.mod_type.get()
            ver = self.current_mc_version
            ldr = self.loader_opt.get().lower()

            facets = [[f"project_type:{m_type}"], [f"versions:{ver}"]]
            if m_type == "mod" and ldr != "all": 
                facets.append([f"categories:{ldr}"])
            
            try:
                url = "https://api.modrinth.com/v2/search"
                params = {"query": query, "facets": json.dumps(facets), "limit": 24}
                resp = requests.get(url, params=params).json()
                self.after(0, lambda: self.render_modrinth_results(resp.get('hits', []), m_type))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Search failed: {e}", parent=self.mod_pop))

        threading.Thread(target=run_query, daemon=True).start()

    def render_modrinth_results(self, hits, m_type):
        for w in self.results_frame.winfo_children(): w.destroy()
        if not hits:
            ctk.CTkLabel(self.results_frame, text=f"No {m_type}s found", font=(FONT, 14), text_color=TEXT_MUTED).pack(pady=20)
            return

        def load_icon(url):
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    from io import BytesIO
                    img = Image.open(BytesIO(r.content)).resize((48, 48), Image.LANCZOS)
                    return ctk.CTkImage(img, size=(48, 48))
            except:
                pass
            return None

        def build_card(item):
            card = ctk.CTkFrame(self.results_frame, fg_color=BG_CARD, corner_radius=12, border_width=2, border_color=BORDER)
            card.pack(fill="x", pady=5, padx=5)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(12, 4))

            icon_lbl = ctk.CTkLabel(row, text="", width=48, height=48, fg_color="transparent")
            icon_lbl.pack(side="left", padx=(0, 12))

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True)

            loaders = [c.capitalize() for c in item.get('categories', []) if c in ['fabric', 'forge', 'neoforge', 'quilt']]
            loader_str = f"[{'/'.join(loaders)}]" if loaders else ""
            title_text = f"{item['title']}  {loader_str}"
            ctk.CTkLabel(text_col, text=title_text, font=(FONT, 14, "bold"), text_color=TEXT_WHITE, anchor="w").pack(fill="x")
            ctk.CTkLabel(text_col, text=f"by {item['author']}  ({item.get('latest_version', 'N/A')})", font=(FONT, 10), text_color=TEXT_MUTED, anchor="w").pack(fill="x")

            desc = item.get('description', '')
            if desc:
                desc_lbl = ctk.CTkLabel(text_col, text=desc[:120] + ('...' if len(desc) > 120 else ''), font=(FONT, 10), text_color=TEXT_MUTED, anchor="w", wraplength=500)
                desc_lbl.pack(fill="x", pady=(2, 0))

            downloads = item.get('downloads', 0)
            follows = item.get('follows', 0)
            stats_text = f"📥 {self._fmt_num(downloads)}  ★ {self._fmt_num(follows)}"
            ctk.CTkLabel(text_col, text=stats_text, font=(FONT, 9), text_color=TEXT_MUTED, anchor="w").pack(fill="x", pady=(2, 0))

            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=(10, 0))

            ctk.CTkButton(btn_frame, text="INFO", width=60, height=28, font=(FONT, 9, "bold"), fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, border_width=1, border_color=BORDER, corner_radius=6,
                          command=lambda s=item['slug']: webbrowser.open(f"https://modrinth.com/{m_type}/{s}")).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="INSTALL", width=80, height=28, font=(FONT, 9, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6,
                          command=lambda s=item['slug'], t=m_type: self.download_logic(s, t)).pack(side="left", padx=2)

            icon_url = item.get('icon_url')
            if icon_url:
                def set_icon(lbl, url):
                    img = load_icon(url)
                    if img:
                        lbl.configure(image=img, text="")
                threading.Thread(target=set_icon, args=(icon_lbl, icon_url), daemon=True).start()

        for item in hits:
            build_card(item)

    def _fmt_num(self, n):
        if n >= 1000000:
            return f"{n/1000000:.1f}M"
        if n >= 1000:
            return f"{n/1000:.1f}K"
        return str(n)

    def _get_instance_loader(self):
        parts = self.selected_version.split('_')
        return parts[0].lower() if len(parts) >= 2 else None

    def _find_best_version(self, versions, target_mc, target_loader=None):
        if not versions or not target_mc:
            return None
        exact = []
        for v in versions:
            gv = v.get('game_versions', [])
            loaders = v.get('loaders', [])
            if target_mc in gv:
                if not target_loader or target_loader == "vanilla":
                    if not loaders or all(l == "vanilla" for l in loaders):
                        exact.append(v)
                elif target_loader in loaders:
                    exact.append(v)
        if exact:
            exact.sort(key=lambda v: v.get('date_published', ''), reverse=True)
            return exact[0]
        return None

    def download_logic(self, slug, m_type):
        if m_type == "modpack":
            self.install_modpack(slug)
            return
        try:
            versions = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version").json()
            valid_vers = [v for v in versions if self.current_mc_version in v['game_versions']]
            
            if not valid_vers:
                messagebox.showerror("Error", "No compatible version found.", parent=self.mod_pop)
                return

            available_loaders = set()
            for v in valid_vers:
                for l in v['loaders']:
                    if l in ['fabric', 'forge', 'neoforge']: available_loaders.add(l)

            if len(available_loaders) > 1:
                inst_loader = self._get_instance_loader()
                if inst_loader and inst_loader in available_loaders:
                    self.start_download_mod(slug, m_type, inst_loader)
                else:
                    ask_win = ctk.CTkToplevel(self.mod_pop)
                    ask_win.geometry("300x150")
                    ask_win.title("Select Loader")
                    ask_win.transient(self.mod_pop)
                    ask_win.grab_set() 
                    
                    ctk.CTkLabel(ask_win, text="Choose your mod loader:", font=("Arial", 12, "bold")).pack(pady=15)
                    btn_frame = ctk.CTkFrame(ask_win, fg_color="transparent")
                    btn_frame.pack(pady=5)
                    
                    for loader in available_loaders:
                        ctk.CTkButton(btn_frame, text=loader.capitalize(), width=100,
                                      command=lambda l=loader: [self.start_download_mod(slug, m_type, l), ask_win.destroy()]).pack(side="left", padx=5)
            else:
                loader_to_use = list(available_loaders)[0] if available_loaders else None
                self.start_download_mod(slug, m_type, loader_to_use)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get versions: {e}", parent=self.mod_pop)

    # RENAMED FUNCTION
    def start_download_mod(self, slug, m_type, preferred_loader=None):
        instance_ver = self.current_mc_version
        folders = {"mod": "mods", "resourcepack": "resourcepacks", "shader": "shaderpacks"}
        target_path = os.path.join(self.base_path, "instances", self.selected_version, folders.get(m_type, "mods"))
        os.makedirs(target_path, exist_ok=True)

        def dl_thread():
            try:
                vers = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version").json()
                match = self._find_best_version(vers, instance_ver, preferred_loader)
                
                if not match:
                    self.after(0, lambda: messagebox.showerror("Error", f"No compatible version for MC {instance_ver}", parent=self.mod_pop))
                    return

                file_info = match['files'][0]
                r = requests.get(file_info['url'], stream=True)
                with open(os.path.join(target_path, file_info['filename']), "wb") as f:
                    for chunk in r.iter_content(8192): f.write(chunk)
                
                self.after(0, lambda: messagebox.showinfo("Success", f"Installed {file_info['filename']}!", parent=self.mod_pop))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Download Error", str(e), parent=self.mod_pop))

        threading.Thread(target=dl_thread, daemon=True).start()

    def install_modpack(self, slug):
        pop, bar, label = self._make_download_popup("Installing modpack...")
        instance_path = os.path.join(self.base_path, "instances", self.selected_version)

        def run():
            try:
                label.configure(text="Fetching modpack versions...")
                vers = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version").json()

                match = None
                inst_loader = self._get_instance_loader()
                for v in vers:
                    if self.current_mc_version in v['game_versions']:
                        if not inst_loader or inst_loader in v['loaders']:
                            match = v
                            break
                if not match:
                    for v in vers:
                        if self.current_mc_version in v['game_versions']:
                            match = v
                            break
                if not match:
                    match = vers[0]

                file_info = match['files'][0]
                mrpack_url = file_info['url']

                label.configure(text=f"Downloading {file_info['filename']}...")
                r = requests.get(mrpack_url, stream=True)
                with tempfile.NamedTemporaryFile(suffix='.mrpack', delete=False) as tmp:
                    for chunk in r.iter_content(8192):
                        tmp.write(chunk)
                    mrpack_path = tmp.name

                label.configure(text="Extracting modpack...")
                extract_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(mrpack_path, 'r') as z:
                    z.extractall(extract_dir)

                index_path = os.path.join(extract_dir, 'modrinth.index.json')
                if not os.path.exists(index_path):
                    raise Exception("Invalid modpack: missing modrinth.index.json")

                with open(index_path) as f:
                    index = json.load(f)

                deps = index.get('dependencies', {})
                mc_dep = deps.get('minecraft', '?')

                files = index.get('files', [])
                for i, file_entry in enumerate(files):
                    path = file_entry['path']
                    dl_url = file_entry['downloads'][0] if file_entry.get('downloads') else None
                    if dl_url:
                        label.configure(text=f"Downloading ({i+1}/{len(files)}): {os.path.basename(path)}")
                        dest = os.path.join(instance_path, path)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        r = requests.get(dl_url, stream=True)
                        with open(dest, 'wb') as f:
                            for chunk in r.iter_content(8192):
                                f.write(chunk)

                for override_dir in ['overrides', 'client-overrides']:
                    src = os.path.join(extract_dir, override_dir)
                    if os.path.exists(src):
                        label.configure(text=f"Applying {override_dir}...")
                        for root, dirs, files_ in os.walk(src):
                            rel = os.path.relpath(root, src)
                            for f in files_:
                                src_file = os.path.join(root, f)
                                dst_file = os.path.join(instance_path, rel, f)
                                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                                shutil.copy2(src_file, dst_file)

                os.unlink(mrpack_path)
                shutil.rmtree(extract_dir, ignore_errors=True)

                pop.destroy()
                self.after(0, lambda: messagebox.showinfo("Success",
                    f"Modpack installed!\nRequires: Minecraft {mc_dep}", parent=self.mod_pop))
            except Exception as e:
                pop.destroy()
                self.after(0, lambda: messagebox.showerror("Install Error",
                    str(e), parent=self.mod_pop))

        threading.Thread(target=run, daemon=True).start()

    def open_plugin_browser(self, server_folder):
        soft, version = server_folder.split('_', 1)
        self._plugin_mc_ver = version

        if not hasattr(self, 'plug_pop') or not self.plug_pop or not self.plug_pop.winfo_exists():
            self.plug_pop = ctk.CTkToplevel(self)
            self.plug_pop.geometry("1000x800")
            self.plug_pop.title(f"Sozip Plugin Browser - {server_folder}")
            self.plug_pop.attributes("-topmost", True)
            self.plug_pop.configure(fg_color=BG_DARK)
            self.plug_pop.focus_set()

            ctrl_frame = ctk.CTkFrame(self.plug_pop, fg_color=BG_CARD, corner_radius=12)
            ctrl_frame.pack(fill="x", padx=15, pady=15)

            ctk.CTkLabel(ctrl_frame, text="Type:", font=(FONT, 11), text_color=TEXT_WHITE).pack(side="left", padx=5)
            self._plug_type = ctk.CTkComboBox(ctrl_frame, values=["bukkit", "paper"],
                                              fg_color=BG_DARK, border_color=BORDER, button_color=ACCENT, button_hover_color=ACCENT_HOVER, dropdown_fg_color=BG_CARD,
                                              command=lambda _: self._search_plugins_mr(), state="readonly")
            self._plug_type.pack(side="left", padx=5)

            ctk.CTkLabel(ctrl_frame, text=f"MC: {version}", font=(FONT, 12, "bold"), text_color=ACCENT).pack(side="left", padx=(15, 5))

            self.plug_search_val = ctk.CTkEntry(ctrl_frame, placeholder_text="Search Modrinth plugins...", width=250,
                                                fg_color=BG_CARD, border_color=BORDER)
            self.plug_search_val.pack(side="left", padx=10)
            self.plug_search_val.bind("<Return>", lambda e: self._search_plugins_mr())

            ctk.CTkButton(ctrl_frame, text="SEARCH", width=80, fg_color="#3498db",
                          command=self._search_plugins_mr).pack(side="left", padx=5)

            self.plug_results_frame = ctk.CTkScrollableFrame(self.plug_pop, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
            self.plug_results_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.target_server_folder = server_folder
        self._search_plugins_mr()

    def _search_plugins_mr(self):
        for w in self.plug_results_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.plug_results_frame, text="Searching Modrinth...", font=(FONT, 14), text_color=TEXT_MUTED).pack(pady=20)

        def run():
            query = self.plug_search_val.get().strip()
            ptype = self._plug_type.get()
            facets = [["project_type:mod"], [f"categories:{ptype}"]]
            try:
                params = {"query": query, "facets": json.dumps(facets), "limit": 30}
                resp = requests.get("https://api.modrinth.com/v2/search", params=params).json()
                hits = resp.get('hits', [])
                self.after(0, lambda: self._render_plugin_results(hits))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Search failed: {e}", parent=self.plug_pop))

        threading.Thread(target=run, daemon=True).start()

    def _render_plugin_results(self, hits):
        for w in self.plug_results_frame.winfo_children(): w.destroy()
        if not hits:
            ctk.CTkLabel(self.plug_results_frame, text="No plugins found.", font=(FONT, 14), text_color=TEXT_MUTED).pack(pady=20)
            return

        def load_icon(url):
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    from io import BytesIO
                    img = Image.open(BytesIO(r.content)).resize((48, 48), Image.LANCZOS)
                    return ctk.CTkImage(img, size=(48, 48))
            except:
                pass
            return None

        def build_card(item):
            card = ctk.CTkFrame(self.plug_results_frame, fg_color=BG_CARD, corner_radius=12, border_width=2, border_color=BORDER)
            card.pack(fill="x", pady=5, padx=5)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(12, 4))

            icon_lbl = ctk.CTkLabel(row, text="", width=48, height=48, fg_color="transparent")
            icon_lbl.pack(side="left", padx=(0, 12))

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True)

            title_text = item['title']
            ctk.CTkLabel(text_col, text=title_text, font=(FONT, 14, "bold"), text_color=TEXT_WHITE, anchor="w").pack(fill="x")
            ctk.CTkLabel(text_col, text=f"by {item['author']}", font=(FONT, 10), text_color=TEXT_MUTED, anchor="w").pack(fill="x")

            desc = item.get('description', '')
            if desc:
                ctk.CTkLabel(text_col, text=desc[:120] + ('...' if len(desc) > 120 else ''),
                             font=(FONT, 10), text_color=TEXT_MUTED, anchor="w", wraplength=500).pack(fill="x", pady=(2, 0))

            downloads = item.get('downloads', 0)
            ctk.CTkLabel(text_col, text=f"📥 {self._fmt_num(downloads)}", font=(FONT, 9), text_color=TEXT_MUTED, anchor="w").pack(fill="x", pady=(2, 0))

            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=(10, 0))

            slug = item['slug']
            ctk.CTkButton(btn_frame, text="INFO", width=60, height=28, font=(FONT, 9, "bold"),
                          fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER, border_width=1, border_color=BORDER, corner_radius=6,
                          command=lambda s=slug: webbrowser.open(f"https://modrinth.com/mod/{s}")).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="INSTALL", width=80, height=28, font=(FONT, 9, "bold"),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6,
                          command=lambda s=slug: self._download_plugin_mr(s)).pack(side="left", padx=2)

            icon_url = item.get('icon_url')
            if icon_url:
                def set_icon(lbl, url):
                    img = load_icon(url)
                    if img:
                        lbl.configure(image=img, text="")
                threading.Thread(target=set_icon, args=(icon_lbl, icon_url), daemon=True).start()

        for item in hits:
            build_card(item)

    def _download_plugin_mr(self, slug):
        pop, bar, label = self._make_download_popup("Installing plugin...")
        server_path = os.path.join(self.base_path, "servers", self.target_server_folder)
        tgt = os.path.join(server_path, "plugins")
        os.makedirs(tgt, exist_ok=True)
        ptype = self._plug_type.get()

        def run():
            try:
                vers = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version").json()
                match = self._find_best_version(vers, self._plugin_mc_ver, ptype)
                if not match:
                    pop.destroy()
                    self.after(0, lambda: messagebox.showerror("Error", f"No compatible plugin for MC {self._plugin_mc_ver}", parent=self.plug_pop))
                    return

                fi = match['files'][0]
                label.configure(text=f"Downloading {fi['filename']}...")
                r = requests.get(fi['url'], stream=True)
                with open(os.path.join(tgt, fi['filename']), 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                pop.destroy()
                self.after(0, lambda: messagebox.showinfo("Success", f"Installed {fi['filename']}!", parent=self.plug_pop))
            except Exception as e:
                pop.destroy()
                self.after(0, lambda: messagebox.showerror("Error", str(e), parent=self.plug_pop))

        threading.Thread(target=run, daemon=True).start()

    def on_close(self):
        # Check if self.processes exists and find active ones
        running_servers = []
        if hasattr(self, 'processes'):
            running_servers = [folder for folder, proc in self.processes.items() if proc.poll() is None]
        
        if running_servers:
            java_name = get_java_name()
            msg = (
                "⚠ The following server(s) are still running:\n\n"
                + "\n".join([f"• {s}" for s in running_servers])
                + "\n\nDo you really want to quit the launcher?\n\n"
                "Note: Servers will keep running in the background. "
                f"You will need to use Task Manager to stop '{java_name}' later."
            )
            if not messagebox.askyesno("Servers Still Active", msg):
                return  # Stop the closing process

        # Optional: Force kill processes started by the launcher
        if hasattr(self, 'processes'):
            for proc in self.processes.values():
                if proc.poll() is None: proc.kill()
        if hasattr(self, 'tunnel_processes'):
            for proc in self.tunnel_processes.values():
                try: proc.kill()
                except: pass
        self.destroy()
    def setup_custom_skin_loader(self, path, mtype, version):
        if mtype not in ("Fabric", "Forge"):
            return

        def setup_thread():
            try:
                mods_folder = os.path.join(path, "mods")
                os.makedirs(mods_folder, exist_ok=True)

                dest = os.path.join(mods_folder, "CustomSkinLoader.jar")
                if os.path.exists(dest):
                    return

                filenames = [
                    "CustomSkinLoader_Universal-15.0.1.jar",
                    "CustomSkinLoader_Fabric-14.28-SNAPSHOT-66.jar",
                    "CustomSkinLoader_Universal-14.28-SNAPSHOT-66.jar",
                    "CustomSkinLoader_ForgeV1-14.28.jar"
                ]
                bases = [
                    "https://github.com/xfl03/MCCustomSkinLoader/releases/download/v15.0.1",
                    "https://github.com/xfl03/MCCustomSkinLoader/releases/download/CI-Build",
                    "https://cdn.modrinth.com/data/idMHQ4n2/versions/5rz5EZ6x",
                    "https://mediafilez.forgecdn.net/files/6061/171",
                    "https://github.com/xfl03/MCCustomSkinLoader/releases/download/CI-Build",
                    "https://github.com/xfl03/MCCustomSkinLoader/releases/download/CI-Build"
                ]
                for i, fn in enumerate(filenames):
                    url = f"{bases[i]}/{fn}"
                    try:
                        r = requests.get(url, timeout=15)
                        if r.status_code == 200 and len(r.content) > 50000:
                            with open(dest, "wb") as f:
                                f.write(r.content)
                            return
                    except:
                        pass
            except:
                pass

        threading.Thread(target=setup_thread, daemon=True).start()

    def build_jvm_args(self, gb, java_ver):
        safety = [
            "-Dfml.ignorePatchDiscrepancies=true",
            "-Dfml.ignoreInvalidMinecraftCertificates=true"
        ]

        xmx = int(gb * 1024)
        xms = max(xmx // 2, 96)

        if gb <= 1.0:
            return [
                f"-Xms{xms}M", f"-Xmx{xmx}M",
                "-XX:+UseSerialGC",
                "-XX:+DisableExplicitGC",
                "-XX:+UseCompressedOops",
            ] + safety

        if gb <= 2.0:
            return [
                f"-Xms{xms}M", f"-Xmx{xmx}M",
                "-XX:+UseG1GC",
                "-XX:MaxGCPauseMillis=200",
                "-XX:G1HeapRegionSize=4M",
                "-XX:+DisableExplicitGC",
                "-XX:+UseCompressedOops",
            ] + safety

        perf = [
            "-XX:+AlwaysPreTouch",
            "-XX:+DisableExplicitGC",
            "-XX:+ParallelRefProcEnabled",
            "-XX:+UseStringDeduplication",
            "-XX:+UseFastJNIAccessors",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+AlwaysActAsServerClassMachine",
            "-XX:+UseContainerSupport",
            "-XX:+OptimizeStringConcat",
            "-XX:+UseCompressedOops",
            "-Xss1M",
        ]
        if IS_LINUX:
            perf.append("-XX:+UseTransparentHugePages")

        if java_ver >= 21:
            gc = [
                "-XX:+UseZGC",
                "-XX:+ZGenerational",
                "-XX:ZAllocationSpikeTolerance=2.0",
                "-XX:ZCollectionInterval=120",
                "-XX:ZFragmentationLimit=25",
            ]
        elif java_ver >= 17:
            gc = [
                "-XX:+UseZGC",
                "-XX:ZAllocationSpikeTolerance=2.0",
                "-XX:ZCollectionInterval=120",
            ]
        else:
            gc = [
                "-XX:+UseG1GC",
                "-XX:MaxGCPauseMillis=50",
                "-XX:G1NewSizePercent=30",
                "-XX:G1MaxNewSizePercent=40",
                "-XX:G1HeapRegionSize=8M",
                "-XX:G1ReservePercent=15",
                "-XX:G1HeapWastePercent=3",
                "-XX:G1MixedGCCountTarget=4",
                "-XX:InitiatingHeapOccupancyPercent=15",
                "-XX:G1MixedGCLiveThresholdPercent=90",
                "-XX:SurvivorRatio=8",
                "-XX:MaxTenuringThreshold=1",
            ]

        return gc + [f"-Xms{xms}M", f"-Xmx{xmx}M"] + perf + safety

    def write_minecraft_options(self, path):
        opts_path = os.path.join(path, "options.txt")
        if os.path.exists(opts_path):
            return
        try:
            with open(opts_path, "w") as f:
                f.write('''renderDistance:6
graphics:1
smoothLighting:0
mipmapLevels:0
entityDistanceScaling:0.5
particles:1
ambientOcclusion:0
maxFps:120
fullscreen:false
ao:0
gamma:0.5
bobView:true
language:en_us
fov:70
screenEffectScale:0
entityShadows:false
advancedItemTooltips:false
pauseOnLostFocus:false
''')
        except:
            pass

    THEMES = [
        ("#7c5cbf", "#6a4dab", "#2a2a50", "Purple"),
        ("#4a90d9", "#3a7bc8", "#1e3a5f", "Blue"),
        ("#00bcd4", "#00acc1", "#005662", "Cyan"),
        ("#2ecc71", "#27ae60", "#145a32", "Green"),
        ("#8bc34a", "#7cb342", "#3d5a1e", "Lime"),
        ("#f1c40f", "#d4ac0d", "#5c4a00", "Yellow"),
        ("#f39c12", "#e67e22", "#5c3a00", "Orange"),
        ("#e67e22", "#d35400", "#5c2400", "Deep Orange"),
        ("#8b1a1a", "#6b1010", "#3a0505", "Demon"),
        ("#e91e63", "#c2185b", "#5c0a2e", "Pink"),
        ("#9b59b6", "#8e44ad", "#3d1a4a", "Magenta"),
        ("#3f51b5", "#303f9f", "#1a1a3d", "Indigo"),
        ("#009688", "#00897b", "#003d3a", "Teal"),
        ("#1abc9c", "#17a086", "#0a4a3e", "Mint"),
        ("#27ae60", "#1e8449", "#0a3a1e", "Emerald"),
        ("#3498db", "#2980b9", "#1a3a5c", "Sky Blue"),
        ("#8e44ad", "#7d3c98", "#3a1a4a", "Violet"),
        ("#c0392b", "#a93226", "#4a1a0a", "Crimson"),
        ("#ff6b6b", "#ee5a24", "#5c2020", "Coral"),
        ("#d4a017", "#b8860b", "#4a3a00", "Gold"),
        ("#2a5dc9", "#1e4da8", "#0e2a5a", "ZIP"),
    ]

    def draw_settings_screen(self):
        for w in self.content_area.winfo_children(): w.destroy()
        header = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text="Settings", font=(FONT, 28, "bold"), text_color=TEXT_WHITE).pack(side="left")

        card = ctk.CTkFrame(self.content_area, corner_radius=16, fg_color=BG_CARD, border_width=2, border_color=BORDER)
        card.pack(fill="x", pady=20)

        ctk.CTkLabel(card, text="APPEARANCE", font=(FONT, 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=25, pady=(20, 10))

        preview_row = ctk.CTkFrame(card, fg_color="transparent")
        preview_row.pack(fill="x", padx=25, pady=10)

        swatch = ctk.CTkFrame(preview_row, width=48, height=48, fg_color=ACCENT, corner_radius=12)
        swatch.pack(side="left")
        info_col = ctk.CTkFrame(preview_row, fg_color="transparent")
        info_col.pack(side="left", fill="x", expand=True, padx=(15, 0))
        theme_name = "Custom"
        for a, h, b, n in self.THEMES:
            if a == ACCENT:
                theme_name = n
                break
        ctk.CTkLabel(info_col, text=f"Current Theme: {theme_name}", font=(FONT, 16, "bold"), text_color=TEXT_WHITE, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_col, text=f"Accent: {ACCENT}", font=(FONT, 10), text_color=TEXT_MUTED, anchor="w").pack(fill="x")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=25, pady=(10, 20))
        ctk.CTkButton(btn_row, text="  ✦  Change Theme", font=(FONT, 12, "bold"), height=36, fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=10, command=self.show_theme_picker).pack(side="left")

        mode_frame = ctk.CTkFrame(btn_row, fg_color="transparent")
        mode_frame.pack(side="right")
        is_dark = ctk.get_appearance_mode() == "Dark"
        ctk.CTkLabel(mode_frame, text="☾", font=(FONT, 16), text_color=TEXT_WHITE).pack(side="left", padx=0)
        self.mode_switch = ctk.CTkSwitch(mode_frame, text="", onvalue="Light", offvalue="Dark", command=self.toggle_mode, progress_color=ACCENT, button_color=ACCENT, button_hover_color=ACCENT_HOVER, width=32)
        self.mode_switch.pack(side="left", padx=1)
        self.mode_switch.deselect() if is_dark else self.mode_switch.select()
        ctk.CTkLabel(mode_frame, text="☀", font=(FONT, 16), text_color=TEXT_MUTED).pack(side="left", padx=0)

        ctk.CTkLabel(card, text="ACCOUNT", font=(FONT, 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=25, pady=(25, 10))
        if self.elyby_token:
            logged_row = ctk.CTkFrame(card, fg_color="transparent")
            logged_row.pack(fill="x", padx=25, pady=(0, 20))
            ctk.CTkLabel(logged_row, text="✓  Logged in with Ely.by", font=(FONT, 12, "bold"), text_color=GREEN).pack(side="left")
            ctk.CTkButton(logged_row, text="Logout", width=80, height=28, font=(FONT, 10, "bold"), fg_color="transparent", hover_color=RED, border_width=1, border_color=RED, text_color=RED, corner_radius=6, command=self.elyby_logout).pack(side="right")
        else:
            ctk.CTkLabel(card, text="Login with your Ely.by account for online play.", font=(FONT, 10), text_color=TEXT_MUTED, wraplength=500, anchor="w").pack(anchor="w", padx=25)
            btn_row2 = ctk.CTkFrame(card, fg_color="transparent")
            btn_row2.pack(fill="x", padx=25, pady=(8, 20))
            ctk.CTkButton(btn_row2, text="Ely.by Login", width=120, height=30, font=(FONT, 10, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6, command=self.show_elyby_login_popup).pack(side="left")

        if self.update_available:
            ctk.CTkLabel(card, text="UPDATE", font=(FONT, 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=25, pady=(25, 10))
            update_row = ctk.CTkFrame(card, fg_color="transparent")
            update_row.pack(fill="x", padx=25, pady=(0, 20))
            ctk.CTkLabel(update_row, text=f"Version {self.update_data.get('latest_version', '?')} available", font=(FONT, 12, "bold"), text_color=GREEN, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(update_row, text="Update Now", width=110, height=30, font=(FONT, 10, "bold"),
                          fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=6, command=self._run_update).pack(side="right")

        ctk.CTkLabel(self.content_area, text="More settings coming soon...", font=(FONT, 11), text_color=TEXT_MUTED).pack(pady=10)

    def toggle_mode(self):
        new_mode = self.mode_switch.get()
        ctk.set_appearance_mode(new_mode)
        global BG_DARK, BG_CARD, BG_SIDEBAR, TEXT_MUTED, TEXT_WHITE, BORDER
        if new_mode == "Light":
            BG_DARK, BG_CARD, BG_SIDEBAR = LIGHT_BG_DARK, LIGHT_BG_CARD, LIGHT_BG_SIDEBAR
            TEXT_MUTED, TEXT_WHITE, BORDER = LIGHT_TEXT_MUTED, LIGHT_TEXT_WHITE, LIGHT_BORDER
        else:
            BG_DARK, BG_CARD, BG_SIDEBAR = "#0a0a14", "#14142a", "#0c0c1e"
            TEXT_MUTED, TEXT_WHITE, BORDER = "#8888bb", "#ffffff", "#2a2a50"
        self.configure(fg_color=BG_DARK)
        self.sidebar.configure(fg_color=BG_SIDEBAR)
        self.dash_btn.configure(text_color=TEXT_WHITE, hover_color=BG_CARD)
        self.install_btn.configure(text_color=TEXT_WHITE, hover_color=BG_CARD)
        self.snap_btn.configure(text_color=TEXT_WHITE, hover_color=BG_CARD)
        self.settings_nav_btn.configure(fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER)
        self.skin_label.configure(fg_color=BG_CARD)
        self.skin_border.configure(border_color=ACCENT)
        self.skin_upload_btn.configure(fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER)
        self.skin_fetch_btn.configure(fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER)
        self.sep2.configure(fg_color=BORDER)
        self.sep3.configure(fg_color=BORDER)
        self.user_entry.configure(fg_color=BG_CARD, border_color=BORDER)
        self.open_data_btn.configure(fg_color=BG_CARD, text_color=TEXT_WHITE, hover_color=BORDER)
        data = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
            except: pass
        data["appearance_mode"] = new_mode
        with open(self.config_file, "w") as f:
            json.dump(data, f)
        self.after(100, self.draw_home)

    def show_theme_picker(self):
        picker = ctk.CTkToplevel(self)
        picker.geometry("720x580")
        picker.title("Choose Theme")
        picker.attributes("-topmost", True)
        picker.configure(fg_color=BG_DARK)
        picker.resizable(False, False)

        top = ctk.CTkFrame(picker, fg_color="transparent")
        top.pack(fill="x", padx=25, pady=(20, 5))
        ctk.CTkLabel(top, text="Choose Theme", font=(FONT, 24, "bold"), text_color=TEXT_WHITE).pack(side="left")
        ctk.CTkLabel(top, text=f"  {len(self.THEMES)} presets", font=(FONT, 11), text_color=TEXT_MUTED).pack(side="left", pady=(6, 0))

        frame = ctk.CTkScrollableFrame(picker, fg_color="transparent", scrollbar_button_hover_color=ACCENT)
        frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        for i, (accent, hover, border, name) in enumerate(self.THEMES):
            row_idx, col_idx = divmod(i, 4)
            if col_idx == 0:
                grid_row = ctk.CTkFrame(frame, fg_color="transparent")
                grid_row.pack(fill="x", pady=6)

            is_current = accent == ACCENT
            card = ctk.CTkFrame(grid_row, fg_color=BG_CARD, corner_radius=14, border_width=3 if is_current else 2, border_color=ACCENT if is_current else border)
            card.pack(side="left", padx=6, expand=True, fill="x")

            swatch = ctk.CTkFrame(card, height=60, fg_color=accent, corner_radius=10)
            swatch.pack(fill="x", padx=8, pady=(8, 3))

            ctk.CTkLabel(card, text=name, font=(FONT, 11, "bold"), text_color=TEXT_WHITE).pack()
            ctk.CTkLabel(card, text=accent, font=(FONT, 8), text_color=TEXT_MUTED).pack(pady=(0, 4))

            if is_current:
                ctk.CTkLabel(card, text="✓ ACTIVE", font=(FONT, 8, "bold"), text_color=ACCENT).pack(pady=(0, 6))

            card.bind("<Button-1>", lambda e, a=accent, h=hover, b=border: self.apply_theme(a, h, b, picker))
            swatch.bind("<Button-1>", lambda e, a=accent, h=hover, b=border: self.apply_theme(a, h, b, picker))

    def apply_theme(self, accent, hover, border, win=None):
        global ACCENT, ACCENT_HOVER, BORDER
        ACCENT = accent
        ACCENT_HOVER = hover
        BORDER = border
        data = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
            except: pass
        data["accent"] = accent
        data["accent_hover"] = hover
        data["border"] = border
        with open(self.config_file, "w") as f:
            json.dump(data, f)
        self.ram_lbl.configure(text_color=accent)
        self.s_ram_lbl.configure(text_color=accent)
        self.ram_slider.configure(progress_color=accent, button_color=accent, button_hover_color=hover)
        self.s_ram_slider.configure(progress_color=accent, button_color=accent, button_hover_color=hover)
        self.server_mgr_btn.configure(fg_color=accent, hover_color=hover)
        self.skin_border.configure(border_color=accent)
        if win:
            win.destroy()
        self.after(100, self.draw_home)

    def start_discord_rpc(self):
        try:
            client_id = "1468150193231761470"
            self.RPC = Presence(client_id)
            self.RPC.connect()
            self.RPC.update(
                state="Managing Versions",
                details="Main Menu",
                start=time.time(),
                large_image="logo"
            )
        except:
            pass
    def get_required_java_version(self, mc_version):
        try:
            parts = mc_version.split('_')
            version_str = parts[1] if len(parts) > 1 else mc_version
            major, minor = parse_mc_version(version_str)

            if major >= 2 or (major == 1 and minor >= 26):
                return 25
            if major == 1 and minor >= 21:
                return 21
            if major == 1 and minor >= 18:
                return 17
            return 8
        except:
            return 8

    def ensure_portable_java(self, java_ver, download_ui=None):
        import zipfile, tarfile, threading, time as _time
        base_path = os.path.join(os.getcwd(), "runtime", f"java-{java_ver}")
        java_exe = os.path.join(base_path, "bin", get_java_name())

        if os.path.exists(java_exe):
            return java_exe

        own_popup = False
        if download_ui is None:
            pop, bar, label = self._make_download_popup(f"Downloading Java {java_ver}...")
            own_popup = True
        else:
            pop, bar, label = download_ui
            self.after(0, lambda: label.configure(text=f"Downloading Java {java_ver}..."))
        pop.grab_set()
        pop.update_idletasks()

        result = {"path": "java", "ok": False}
        done = threading.Event()

        def task():
            try:
                os_name = "windows" if IS_WINDOWS else "linux"
                api_url = f"https://api.adoptium.net/v3/binary/latest/{java_ver}/ga/{os_name}/x64/jre/hotspot/normal/eclipse"
                response = requests.get(api_url, stream=True, allow_redirects=True)
                if response.status_code == 200:
                    os.makedirs("runtime", exist_ok=True)
                    archive = os.path.join("runtime", "temp_java.zip" if IS_WINDOWS else "temp_java.tar.gz")
                    with open(archive, 'wb') as f:
                        for chunk in response.iter_content(8192):
                            f.write(chunk)
                    self.after(0, lambda: label.configure(text="Extracting..."))
                    before = set(os.listdir("runtime"))
                    if archive.endswith(".zip"):
                        with zipfile.ZipFile(archive, 'r') as z: z.extractall("runtime")
                    else:
                        with tarfile.open(archive, 'r:gz') as t: t.extractall("runtime")
                    after = set(os.listdir("runtime"))
                    new_dirs = [d for d in (after - before) if os.path.isdir(os.path.join("runtime", d))]
                    if new_dirs:
                        os.rename(os.path.join("runtime", new_dirs[0]), base_path)
                    os.remove(archive)
                    for d in new_dirs[1:]:
                        shutil.rmtree(os.path.join("runtime", d), ignore_errors=True)
                    result["path"] = java_exe
                    result["ok"] = True
            except:
                pass
            finally:
                done.set()

        threading.Thread(target=task, daemon=True).start()

        while not done.is_set():
            pop.update()
            _time.sleep(0.05)

        if own_popup:
            pop.destroy()
        return result["path"]
    def run_game(self):
        import uuid, subprocess, threading

        path = os.path.join(self.base_path, "instances", self.selected_version)
        required_ver = 8
        try:
            required_ver = self.get_required_java_version(self.selected_version)
        except:
            pass

        use_elyby = bool(self.elyby_token.strip())
        java_exe = os.path.join(os.getcwd(), "runtime", f"java-{required_ver}", "bin", get_java_name())
        needs_java = not os.path.exists(java_exe)
        needs_auth = not os.path.exists(os.path.join(self.base_path, "authlib-injector.jar")) and use_elyby

        download_ui = None
        if needs_java or needs_auth:
            download_ui = self._make_download_popup("Preparing dependencies...")

        portable_java_path = "java"
        try:
            if needs_java:
                portable_java_path = self.ensure_portable_java(required_ver, download_ui)
            else:
                portable_java_path = java_exe
        except:
            portable_java_path = "java"
        try:
            parts = self.selected_version.split('_')
            if len(parts) >= 2:
                mtype = parts[0]   # Fabric or Forge
                mc_ver = parts[1]  # 1.20.1
                # Run this in a thread so the launcher doesn't freeze
                threading.Thread(target=self.setup_custom_skin_loader, args=(path, mtype, mc_ver), daemon=True).start()
        except:
            pass

        self.apply_skin_resource_pack(path)
        threading.Thread(target=self._install_crash_assistant, args=(path,), daemon=True).start()
        self.write_minecraft_options(path)
        self.save_settings()

        launch_id = self.get_launch_id(path)
        if not launch_id:
            if download_ui:
                self.after(0, download_ui[0].destroy)
            messagebox.showerror("Error", "Game files corrupted or not installed properly.")
            return

        if use_elyby:
            ely_uuid = getattr(self, 'elyby_uuid', '')
            final_uuid = ely_uuid if ely_uuid else str(uuid.uuid3(uuid.NAMESPACE_DNS, self.username))
            final_token = self.elyby_token.strip()
        else:
            final_uuid = str(uuid.uuid4())
            final_token = "0"

        reserved = 0.5 if self.max_pc_ram <= 2 else 1
        safe_ram = max(0.5, min(self.ram, self.max_pc_ram - reserved))
        safe_ram = round(safe_ram * 2) / 2

        jvm_args = self.build_jvm_args(safe_ram, required_ver)


        opts = {
        "username": self.username,
        "executablePath": portable_java_path,
        "uuid": final_uuid,
        "token": final_token,
        "gameDirectory": path,
        "jvmArguments": jvm_args
    }

        try:
            cmd = minecraft_launcher_lib.command.get_minecraft_command(launch_id, path, opts)

            if use_elyby:
                injector_path = self.get_auth_injector(download_ui)
                if injector_path is None:
                    if download_ui:
                        self.after(0, download_ui[0].destroy)
                    return
                cmd = [cmd[0], f"-javaagent:{injector_path}=ely.by"] + cmd[1:]

            if download_ui:
                self.after(0, download_ui[0].destroy)

            def launch():
                self.withdraw()
                try:
                    proc = subprocess.Popen(
                        cmd,
                        cwd=path,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) if IS_WINDOWS else 0
                    )
                    err_lines = []
                    def read_err():
                        for line in iter(proc.stderr.readline, b''):
                            err_lines.append(line)
                        proc.stderr.close()
                    threading.Thread(target=read_err, daemon=True).start()

                    import time as _time
                    _time.sleep(3)
                    if proc.poll() is not None and proc.returncode != 0:
                        err_text = b''.join(err_lines).decode(errors='replace')[:500]
                        self.after(0, lambda: messagebox.showerror("Game Crashed", f"Minecraft failed to start:\n{err_text or f'Exit code: {proc.returncode}'}"))
                        self.after(0, self.deiconify)
                        return

                    proc.wait()
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Launch Error", str(e)))
                finally:
                    self.after(0, self.deiconify)

            threading.Thread(target=launch, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Launch Error", str(e))

    def delete_version(self):
        if self.selected_version and messagebox.askyesno("Delete", "Delete version?"):
            shutil.rmtree(os.path.join(self.base_path, "instances", self.selected_version), ignore_errors=True); self.draw_home()

if __name__ == "__main__":
    try:
        app = SozipLauncher()
        app.mainloop()
    except Exception:
        import traceback
        traceback.print_exc()
        with open("launcher_crash.log", "w") as f:
            traceback.print_exc(file=f)
        input("Press Enter to exit...")