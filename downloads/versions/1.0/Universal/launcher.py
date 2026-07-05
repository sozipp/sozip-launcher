import customtkinter as ctk
import minecraft_launcher_lib
import subprocess, os, threading, json, shutil, psutil
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

# OR: Temporary bypass (If the above doesn't work)


# Theme Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class SozipLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SOZIP LAUNCHER PRO")
        self.geometry("1150x850")
        icon_path = os.path.join(os.getcwd(), "sozip_icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
    
        
        
        total_ram = psutil.virtual_memory().total
        self.max_pc_ram = int(total_ram / (1024**3))
        self.config_file = "sozip_config.json"
        
        
        default_settings = {
            "username": "Player",
            "ram": 4,
            "server_ram": 2,
            "path": os.path.join(os.getcwd(), "sozip_data"),
            "network_on": True,
            "uuid": "",
            "token": ""
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
        self.sozip_network_enabled = ctk.BooleanVar(value=data.get("network_on", True))
        self.user_uuid = data.get("uuid", "")
        self.user_token = data.get("token", "")

        
        self.is_installing = False
        self.selected_version = None
        self.processes = {}  
        self.server_ports = {}  # stores running server ports

        os.makedirs(self.base_path, exist_ok=True)
        self.load_settings()
        
        
        self.skin_dir = os.path.join(self.base_path, "skins")
        os.makedirs(self.skin_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "servers"), exist_ok=True)
        
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="SOZIP", font=("Impact", 45), text_color="#2ecc71").pack(pady=20)

        
        self.skin_label = ctk.CTkLabel(self.sidebar, text="", width=100, height=100, fg_color="#1a1a1a", corner_radius=10)
        self.skin_label.pack(pady=5)
        
        skin_btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        skin_btn_frame.pack(pady=5)
        ctk.CTkButton(skin_btn_frame, text="Upload", width=70, height=25, command=self.upload_skin).pack(side="left", padx=2)
        ctk.CTkButton(skin_btn_frame, text="Fetch", width=70, height=25, fg_color="#3498db", command=self.fetch_skin_from_mojang).pack(side="left", padx=2)
        
        
        ctk.CTkButton(self.sidebar, text="Dashboard", fg_color="transparent", anchor="w", command=self.draw_home).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(self.sidebar, text="Installer", fg_color="transparent", anchor="w", command=self.draw_install_screen).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(self.sidebar, text="Snapshots", fg_color="transparent", anchor="w", command=self.draw_snapshot_screen).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(self.sidebar, text="Server Manager", fg_color="#3498db", anchor="w", command=self.draw_server_dashboard).pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(self.sidebar, text="PLAYER NAME", font=("Arial", 11, "bold"), text_color="gray").pack(pady=(20, 5))
        self.user_entry = ctk.CTkEntry(self.sidebar, height=35)
        self.user_entry.pack(padx=20, pady=5)
        self.user_entry.insert(0, self.username)
        
        ctk.CTkLabel(self.sidebar, text="GAME RAM (GB)", font=("Arial", 11, "bold"), text_color="gray").pack(pady=(15, 0))
        self.ram_lbl = ctk.CTkLabel(self.sidebar, text=f"{self.ram} GB"); self.ram_lbl.pack()
        self.ram_slider = ctk.CTkSlider(self.sidebar, from_=1, to=self.max_pc_ram, number_of_steps=self.max_pc_ram-1, command=self.update_ram_label)
        self.ram_slider.set(self.ram); self.ram_slider.pack(padx=20, pady=5)

        ctk.CTkLabel(self.sidebar, text="SERVER RAM (GB)", font=("Arial", 11, "bold"), text_color="gray").pack(pady=(15, 0))
        self.s_ram_lbl = ctk.CTkLabel(self.sidebar, text=f"{self.server_ram} GB"); self.s_ram_lbl.pack()
        self.s_ram_slider = ctk.CTkSlider(self.sidebar, from_=1, to=self.max_pc_ram, number_of_steps=self.max_pc_ram-1, command=self.update_server_ram_label)
        self.s_ram_slider.set(self.server_ram); self.s_ram_slider.pack(padx=20, pady=5)
        
        ctk.CTkButton(self.sidebar, text="Open Game Data", height=35, fg_color="#34495e", command=lambda: os.startfile(self.base_path)).pack(fill="x", padx=20, pady=(40, 5))
        
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        self.update_skin_display()
        self.draw_home()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.start_discord_rpc()
    
    def open_link(self, url):
        webbrowser.open_new_tab(url)

    
    def update_ram_label(self, val):
        self.ram = int(val); self.ram_lbl.configure(text=f"{self.ram} GB"); self.save_settings()

    def update_server_ram_label(self, val):
        self.server_ram = int(val); self.s_ram_lbl.configure(text=f"{self.server_ram} GB"); self.save_settings()

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
        self.username = self.user_entry.get()
        
        # Check if the widget actually exists and is visible
        if hasattr(self, 'uuid_entry') and self.uuid_entry.winfo_exists():
            self.user_uuid = self.uuid_entry.get()
            self.user_token = self.token_entry.get()
            
        with open(self.config_file, "w") as f:
            json.dump({
                "username": self.username, 
                "path": self.base_path, 
                "ram": self.ram, 
                "server_ram": self.server_ram,
                "network_on": self.sozip_network_enabled.get(),
                "uuid": self.user_uuid,
                "token": self.user_token
            }, f)

    
    def draw_server_dashboard(self):
        for w in self.content_area.winfo_children(): w.destroy()
        header = ctk.CTkFrame(self.content_area, fg_color="transparent"); header.pack(fill="x")
        ctk.CTkLabel(header, text="SERVER MANAGER", font=("Arial", 32, "bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Create New Server", command=self.show_server_creator).pack(side="right")
        self.server_list_frame = ctk.CTkScrollableFrame(self.content_area, height=600)
        self.server_list_frame.pack(fill="both", expand=True, pady=10)
        self.refresh_server_list()

    def show_server_creator(self):
        pop = ctk.CTkToplevel(self); pop.geometry("400x400"); pop.title("Create Server"); pop.attributes("-topmost", True)
        ctk.CTkLabel(pop, text="SOFTWARE", font=("Arial", 12, "bold")).pack(pady=(20,5))
        soft_opt = ctk.CTkOptionMenu(pop, values=["Vanilla", "Paper", "Snapshot"], command=lambda m: update_list(m))
        soft_opt.pack(pady=5)
        ctk.CTkLabel(pop, text="VERSION", font=("Arial", 12, "bold")).pack(pady=(10,5))
        self.ver_selector = ctk.CTkOptionMenu(pop, values=["Loading..."])
        self.ver_selector.pack(pady=5)

        def update_list(mode):
            self.ver_selector.configure(values=["Loading..."]); self.ver_selector.set("Loading...")
            def fetch():
                try:
                    if mode == "Paper":
                        vers = requests.get("https://api.papermc.io/v2/projects/paper").json()["versions"]
                        vers.reverse()
                    else:
                        m_type = "release" if mode == "Vanilla" else "snapshot"
                        vers = [v['id'] for v in minecraft_launcher_lib.utils.get_version_list() if v['type'] == m_type]
                    self.after(0, lambda: (self.ver_selector.configure(values=vers), self.ver_selector.set(vers[0])))
                except: self.after(0, lambda: self.ver_selector.set("Error"))
            threading.Thread(target=fetch, daemon=True).start()

        update_list("Vanilla")
        ctk.CTkButton(pop, text="CREATE", fg_color="#2ecc71", command=lambda: self.finish_create_server(soft_opt.get(), self.ver_selector.get(), pop)).pack(pady=30)

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
            
            card = ctk.CTkFrame(self.server_list_frame); card.pack(fill="x", pady=4, padx=5)
            ctk.CTkLabel(card, text=f"📂 {folder}", font=("Arial", 13, "bold")).pack(side="left", padx=10)
            btn_frame = ctk.CTkFrame(card, fg_color="transparent"); btn_frame.pack(side="right", padx=10)
            
            # Open Folder Button
            ctk.CTkButton(btn_frame, text="📁", width=40, fg_color="#34495e", command=lambda p=path: os.startfile(p)).pack(side="left", padx=2)

            # NEW: PLUGINS button (Only for Paper servers)
            if "Paper" in folder:
                ctk.CTkButton(btn_frame, text="PLUGINS", width=80, fg_color="#16a085", 
                              command=lambda f=folder: self.open_spigot_browser(f)).pack(side="left", padx=2)

            if not os.path.exists(os.path.join(path, "server.jar")):
                ctk.CTkButton(btn_frame, text="Install JAR", width=80, command=lambda p=path, f=folder: self.install_server_jar(p, f)).pack(side="left", padx=2)
            else:
                # Existing Start/Stop logic...
                if folder in self.processes and self.processes[folder].poll() is None:
                    ctk.CTkButton(btn_frame, text="CONSOLE", fg_color="#9b59b6", width=80, command=lambda f=folder: self.open_server_console(f)).pack(side="left", padx=2)
                    ctk.CTkButton(btn_frame, text="PORT", fg_color="#16a085", width=60, command=lambda f=folder: self.copy_server_port(f)).pack(side="left", padx=2)
                    ctk.CTkButton(btn_frame, text="STOP", fg_color="#e74c3c", width=60, command=lambda f=folder: self.stop_specific_server(f)).pack(side="left", padx=2)
                else:
                    ctk.CTkButton(btn_frame, text="START", fg_color="#2ecc71", width=80, command=lambda p=path, f=folder: self.start_specific_server(p, f)).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="🗑", fg_color="#c0392b", width=40, command=lambda p=path: self.delete_server(p)).pack(side="left", padx=2)

    def install_server_jar(self, path, folder_name):
        soft, version = folder_name.split('_', 1)
        def run():
            try:
                if soft == "Paper":
                    builds = requests.get(f"https://api.papermc.io/v2/projects/paper/versions/{version}").json()["builds"]
                    url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{builds[-1]}/downloads/paper-{version}-{builds[-1]}.jar"
                else:
                    manifest = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json").json()
                    v_entry = next(v for v in manifest['versions'] if v['id'] == version)
                    url = requests.get(v_entry['url']).json()['downloads']['server']['url']
                
                res = requests.get(url, stream=True)
                with open(os.path.join(path, "server.jar"), "wb") as f:
                    for chunk in res.iter_content(8192): f.write(chunk)
                self.after(0, self.refresh_server_list)
            except Exception as e: self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def start_specific_server(self, path, folder_name):
        try:
            # folder_name is like "Paper_1.20.1", we extract the version
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
        cmd = [java, f"-Xmx{self.server_ram}G", "-jar", "server.jar", "nogui"]
        proc = subprocess.Popen(cmd, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
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

    def delete_server(self, path):
        if messagebox.askyesno("Delete", "Delete server?"):
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
        new_line = 'resourcePacks:["vanilla","file/SozipSkin"]\n'
        if os.path.exists(opt_file):
            with open(opt_file, "r") as f: lines = f.readlines()
            with open(opt_file, "w") as f:
                found = False
                for line in lines:
                    if line.startswith("resourcePacks:"): f.write(new_line); found = True
                    else: f.write(line)
                if not found: f.write(new_line)
        else:
            with open(opt_file, "w") as f: f.write(new_line)

   
    def draw_home(self):
        for w in self.content_area.winfo_children(): w.destroy()
        
        self.user_entry.bind("<FocusOut>", self.save_settings)
        self.user_entry.bind("<Return>", self.save_settings)

        ctk.CTkLabel(self.content_area, text="DASHBOARD", font=("Arial", 32, "bold")).pack(anchor="w")
        
        card = ctk.CTkFrame(self.content_area, corner_radius=20)
        card.pack(fill="x", pady=20, ipady=20)

        
        inst_path = os.path.join(self.base_path, "instances")
        os.makedirs(inst_path, exist_ok=True)
        downloaded = [f for f in os.listdir(inst_path) if os.path.isdir(os.path.join(inst_path, f))]

        if downloaded:
            self.ver_menu = ctk.CTkOptionMenu(card, values=downloaded, width=400, height=45, 
                                             command=lambda v: setattr(self, 'selected_version', v))
            self.ver_menu.pack(pady=(20, 10))
            self.selected_version = downloaded[0]
            
            
            self.network_switch = ctk.CTkSwitch(
                card, text="Sozip Network (Custom Auth)", 
                variable=self.sozip_network_enabled,
                command=self.toggle_network_fields
            )
            self.network_switch.pack(pady=10)

            self.auth_frame = ctk.CTkFrame(card, fg_color="transparent")
            self.auth_frame.pack(fill="x", padx=40)
            self.toggle_network_fields()

            
            # --- UPDATED BUTTON ROW ---
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(pady=20)

            # Folder Button
            ctk.CTkButton(row, text="📁", width=50, height=70, fg_color="#34495e", 
                          command=lambda: os.startfile(os.path.join(self.base_path, "instances", self.selected_version))).pack(side="left", padx=5)

            # NEW: Mods & Packs Button
            ctk.CTkButton(row, text="📦\nMODS", width=80, height=70, font=("Arial", 12, "bold"), 
                          fg_color="#16a085", hover_color="#1abc9c",
                          command=self.open_modrinth_browser).pack(side="left", padx=5)

            # Play Button
            ctk.CTkButton(row, text="PLAY NOW", width=200, height=70, font=("Arial", 22, "bold"), 
                          fg_color="#2ecc71", command=self.run_game).pack(side="left", padx=5)
            
            # News Button
            ctk.CTkButton(row, text="NEWS", width=80, height=70, font=("Arial", 14, "bold"),
                          fg_color="#e67e22", hover_color="#d35400",
                          command=lambda: self.open_link("https://sozip19op.github.io/Sozip-launcher/note.html")).pack(side="left", padx=5)

            # Delete Button
            ctk.CTkButton(row, text="🗑", width=50, height=70, fg_color="#e74c3c", 
                          command=self.delete_version).pack(side="left", padx=5)
        else:
            ctk.CTkLabel(card, text="No instances installed. Go to Installer!", font=("Arial", 16)).pack(pady=40)

        # --- NEW LINKS FOOTER (The part you were missing) ---
        footer_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=20)

        links = [
            ("📘 Tutorial", "https://sozip19op.github.io/Sozip-launcher/tutorial.html"),
            ("✨ Features", "https://sozip19op.github.io/Sozip-launcher/features.html"),
            ("🌐 Website", "https://sozip19op.github.io/Sozip-launcher/"),
            ("☁ Network", "https://sozip19op.github.io/Sozip-launcher/upload.html"),
            ("📺 YouTube", "https://www.youtube.com/@sozip19op")
        ]

        for text, url in links:
            btn = ctk.CTkButton(footer_frame, text=text, width=120, height=35, 
                                fg_color="#2c3e50", hover_color="#34495e",
                                command=lambda u=url: self.open_link(u))
            btn.pack(side="left", padx=10, expand=True)

    def toggle_network_fields(self):
        
        for w in self.auth_frame.winfo_children():
            w.destroy()
        
        
        self.save_settings()
        
        
        if self.sozip_network_enabled.get():
            
            if not hasattr(self, 'show_auth_data'): self.show_auth_data = False
            
            def toggle_visibility():
                self.show_auth_data = not self.show_auth_data
                self.toggle_network_fields() # Refresh UI

            
            eye_btn = ctk.CTkButton(self.auth_frame, text="👁" if self.show_auth_data else "🔒", 
                                    width=35, height=35, command=toggle_visibility)
            eye_btn.pack(side="left", padx=(0, 10))

            
            ctk.CTkLabel(self.auth_frame, text="UUID:", font=("Arial", 10)).pack(side="left", padx=5)
            self.uuid_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="User UUID", width=200, 
                                           show="" if self.show_auth_data else "*")
            self.uuid_entry.insert(0, self.user_uuid) 
            self.uuid_entry.pack(side="left", padx=5)
            self.uuid_entry.bind("<FocusOut>", self.save_settings)

            
            ctk.CTkLabel(self.auth_frame, text="Token:", font=("Arial", 10)).pack(side="left", padx=5)
            self.token_entry = ctk.CTkEntry(self.auth_frame, placeholder_text="Access Token", width=200, 
                                            show="" if self.show_auth_data else "*")
            self.token_entry.insert(0, self.user_token)
            self.token_entry.pack(side="left", padx=5)
            self.token_entry.bind("<FocusOut>", self.save_settings)

    def draw_install_screen(self):
        self.current_mode = "release"; self.setup_installer_view("INSTALLER")
        threading.Thread(target=self.get_versions_thread, daemon=True).start()

    def draw_snapshot_screen(self):
        self.current_mode = "snapshot"; self.setup_installer_view("SNAPSHOTS")
        threading.Thread(target=self.get_versions_thread, daemon=True).start()

    def setup_installer_view(self, title):
        for w in self.content_area.winfo_children(): w.destroy()
        header = ctk.CTkFrame(self.content_area, fg_color="transparent"); header.pack(fill="x")
        ctk.CTkLabel(header, text=title, font=("Arial", 32, "bold")).pack(side="left")
        self.search_var = ctk.StringVar(); self.search_var.trace_add("write", self.filter_versions)
        ctk.CTkEntry(header, placeholder_text="Search...", width=250, textvariable=self.search_var).pack(side="right", pady=10)
        self.scroll = ctk.CTkScrollableFrame(self.content_area, height=520); self.scroll.pack(fill="both", expand=True, pady=10)
        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading..."); self.loading_lbl.pack(pady=20)

    def get_versions_thread(self):
        try:
            self.full_version_list = [v for v in minecraft_launcher_lib.utils.get_version_list() if v['type'] == self.current_mode]
            self.after(0, self.loading_lbl.destroy); self.after(0, lambda: self.render_list(self.full_version_list))
        except: self.after(0, lambda: self.loading_lbl.configure(text="Error!"))

    def filter_versions(self, *args):
        query = self.search_var.get().lower()
        filtered = [v for v in self.full_version_list if query in v['id'].lower()]
        self.render_list(filtered)

    def render_list(self, data):
        for w in self.scroll.winfo_children(): w.destroy()
        for v in data:
            f = ctk.CTkFrame(self.scroll, fg_color="transparent"); f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=f"Minecraft {v['id']}", font=("Arial", 14, "bold")).pack(side="left", padx=10)
            v_id = v['id']
            ctk.CTkButton(f, text="Vanilla", width=70, command=lambda x=v_id: self.start_download(x, "Vanilla")).pack(side="right", padx=5)
            if self.current_mode == "release":
                p = v_id.split('.')
                try:
                    minor = int(p[1])
                except (IndexError, ValueError):
                    minor = 0
                if minor >= 8: ctk.CTkButton(f, text="Forge", width=70, fg_color="#e67e22", command=lambda x=v_id: self.start_download(x, "Forge")).pack(side="right", padx=5)
                if minor >= 14: ctk.CTkButton(f, text="Fabric", width=70, fg_color="#3498db", command=lambda x=v_id: self.start_download(x, "Fabric")).pack(side="right", padx=5)

    def start_download(self, version, mtype):
        if self.is_installing: return
        self.is_installing = True
        
        # Setup Smooth Progress UI
        pop = ctk.CTkToplevel(self)
        pop.geometry("400x220")
        pop.title(f"Installing {mtype}")
        pop.attributes("-topmost", True)
        
        bar = ctk.CTkProgressBar(pop, width=320)
        bar.set(0)
        bar.pack(pady=(40, 10))
        
        lbl = ctk.CTkLabel(pop, text=f"Initializing {mtype}...", font=("Arial", 12))
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
                        if current_max > 0:
                            self.after(0, lambda: bar.set(progress / current_max))

                    def set_max(new_max):
                        nonlocal current_max
                        current_max = new_max

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

        
    def get_auth_injector(self):
        injector_path = os.path.join(self.base_path, "authlib-injector.jar")
        if not os.path.exists(injector_path):
            try:
                
                url = "https://github.com/yushijinhun/authlib-injector/releases/download/v1.2.5/authlib-injector-1.2.5.jar"
                res = requests.get(url)
                with open(injector_path, "wb") as f:
                    f.write(res.content)
            except Exception as e:
                print(f"Failed to download injector: {e}")
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
        return next((v for v in ids if 'forge' in v.lower() or 'fabric' in v.lower()), ids[0])
	
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

        # Main Browser Window
        self.mod_pop = ctk.CTkToplevel(self)
        self.mod_pop.geometry("1000x800")
        self.mod_pop.title("Sozip Modrinth Browser")
        self.mod_pop.attributes("-topmost", True)
        self.mod_pop.focus_set() 

        # Control Bar
        ctrl_frame = ctk.CTkFrame(self.mod_pop)
        ctrl_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(ctrl_frame, text="Type:").pack(side="left", padx=5)
        self.mod_type = ctk.CTkOptionMenu(ctrl_frame, values=["mod", "resourcepack", "shader"], 
                                         command=lambda _: self.search_now())
        self.mod_type.pack(side="left", padx=5)

        instance_ver = self.selected_version.split('_')[-1]
        self.current_mc_version = instance_ver
        ctk.CTkLabel(ctrl_frame, text=f"MC: {instance_ver}", font=("Arial", 12, "bold"), text_color="#2ecc71").pack(side="left", padx=(15, 5))

        self.loader_container = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        ctk.CTkLabel(self.loader_container, text="Software:").pack(side="left", padx=5)
        self.loader_opt = ctk.CTkOptionMenu(self.loader_container, values=["All", "fabric", "forge"],
                                           command=lambda _: self.search_now())
        self.loader_opt.pack(side="left", padx=5)

        self.search_val = ctk.CTkEntry(ctrl_frame, placeholder_text="Search Modrinth...", width=180)
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
            ctk.CTkLabel(self.results_frame, text=f"No {m_type}s found").pack(pady=20)
            return

        for item in hits:
            card = ctk.CTkFrame(self.results_frame)
            card.pack(fill="x", pady=4, padx=5)
            
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=10, pady=5)
            
            loaders = [c.capitalize() for c in item.get('categories', []) if c in ['fabric', 'forge', 'quilt']]
            loader_str = f"[{'/'.join(loaders)}]" if loaders else ""
            ver_str = f"({item.get('latest_version', 'N/A')})"
            
            title_text = f"{item['title']}  {loader_str}"
            ctk.CTkLabel(info, text=title_text, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"by {item['author']} {ver_str}", font=("Arial", 10), text_color="gray", anchor="w").pack(fill="x")
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)

            # INFO BUTTON
            ctk.CTkButton(btn_frame, text="INFO", width=60, fg_color="#34495e", 
                          command=lambda s=item['slug']: webbrowser.open(f"https://modrinth.com/mod/{s}")).pack(side="left", padx=2)

            # INSTALL BUTTON
            ctk.CTkButton(btn_frame, text="INSTALL", width=90, fg_color="#2ecc71", 
                          command=lambda s=item['slug'], t=m_type: self.download_logic(s, t)).pack(side="left", padx=2)

    def download_logic(self, slug, m_type):
        try:
            versions = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version").json()
            valid_vers = [v for v in versions if self.current_mc_version in v['game_versions']]
            
            if not valid_vers:
                messagebox.showerror("Error", "No compatible version found.", parent=self.mod_pop)
                return

            available_loaders = set()
            for v in valid_vers:
                for l in v['loaders']:
                    if l in ['fabric', 'forge']: available_loaders.add(l)

            if len(available_loaders) > 1:
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
                match = None
                for v in vers:
                    if instance_ver in v['game_versions']:
                        if not preferred_loader or preferred_loader in v['loaders']:
                            match = v
                            break
                
                if not match: match = vers[0]
                
                file_info = match['files'][0]
                r = requests.get(file_info['url'], stream=True)
                with open(os.path.join(target_path, file_info['filename']), "wb") as f:
                    for chunk in r.iter_content(8192): f.write(chunk)
                
                self.after(0, lambda: messagebox.showinfo("Success", f"Installed {file_info['filename']}!", parent=self.mod_pop))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Download Error", str(e), parent=self.mod_pop))

        threading.Thread(target=dl_thread, daemon=True).start()

    def open_spigot_browser(self, server_folder):
        """Full Browser for Spigot/Paper Plugins."""
        if not hasattr(self, 'plug_pop') or not self.plug_pop or not self.plug_pop.winfo_exists():
            self.plug_pop = ctk.CTkToplevel(self)
            self.plug_pop.geometry("1000x800")
            self.plug_pop.title(f"Sozip Spigot Browser - {server_folder}")
            self.plug_pop.attributes("-topmost", True)
            self.plug_pop.focus_set()

            # Control Bar
            ctrl_frame = ctk.CTkFrame(self.plug_pop)
            ctrl_frame.pack(fill="x", padx=15, pady=15)

            ctk.CTkLabel(ctrl_frame, text="Plugin Search:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
            self.plug_search_val = ctk.CTkEntry(ctrl_frame, placeholder_text="Search SpigotMC...", width=380)
            self.plug_search_val.pack(side="left", padx=10)
            self.plug_search_val.bind("<Return>", lambda e: self.search_plugins())

            ctk.CTkButton(ctrl_frame, text="SEARCH", width=100, fg_color="#3498db", 
                          command=self.search_plugins).pack(side="left", padx=5)

            self.plug_results_frame = ctk.CTkScrollableFrame(self.plug_pop)
            self.plug_results_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.target_server_folder = server_folder
        self.search_plugins()

    def search_plugins(self):
        """Fetches plugins. Shows 10 featured items if search is empty."""
        for w in self.plug_results_frame.winfo_children():
            w.destroy()
            
        ctk.CTkLabel(self.plug_results_frame, text="Loading Plugins...").pack(pady=20)
        query = self.plug_search_val.get().strip()
        
        def run_plug_query():
            headers = {"User-Agent": "SozipLauncher/1.1"} 
            try:
                # --- HOME PAGE LOGIC (No Text Header) ---
                if not query:
                    home_plugins = [9089, 4100, 34315, 28140, 31811, 2674, 1997, 75097, 19254, 13873]
                    results = []
                    for pid in home_plugins:
                        try:
                            p_resp = requests.get(f"https://api.spiget.org/v2/resources/{pid}", headers=headers, timeout=5)
                            if p_resp.status_code == 200:
                                results.append(p_resp.json())
                        except: continue
                    self.after(0, lambda: self.render_plugin_results(results))
                    return

                # --- SEARCH LOGIC ---
                url = f"https://api.spiget.org/v2/search/resources/{query}?field=name&size=25"
                resp = requests.get(url, headers=headers, timeout=10)
                
                if resp.status_code == 200 and resp.text.strip():
                    data = resp.json()
                    self.after(0, lambda: self.render_plugin_results(data))
                else:
                    self.after(0, lambda: self.render_plugin_results([]))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("API Error", "Spigot API busy or no data returned.", parent=self.plug_pop))

        threading.Thread(target=run_plug_query, daemon=True).start()

    def render_plugin_results(self, plugins):
        for w in self.plug_results_frame.winfo_children():
            w.destroy()
            
        if not plugins:
            ctk.CTkLabel(self.plug_results_frame, text="No plugins found.").pack(pady=20)
            return

        for item in plugins:
            if item.get('premium'): continue 

            card = ctk.CTkFrame(self.plug_results_frame)
            card.pack(fill="x", pady=4, padx=5)
            
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=10, pady=5)
            
            name = item.get('name', 'Unknown Plugin')
            tag = item.get('tag', 'No description available')[:120] + "..."
            
            ctk.CTkLabel(info, text=name, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=tag, font=("Arial", 10), text_color="gray", anchor="w").pack(fill="x")
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)

            # INFO: Open SpigotMC page
            res_id = item['id']
            ctk.CTkButton(btn_frame, text="INFO", width=60, fg_color="#34495e", 
                          command=lambda r=res_id: webbrowser.open(f"https://www.spigotmc.org/resources/{r}")).pack(side="left", padx=2)

            # INSTALL
            ctk.CTkButton(btn_frame, text="INSTALL", width=90, fg_color="#9b59b6", 
                          command=lambda r=res_id, n=name: self.start_download_plugin(r, n)).pack(side="left", padx=2)

    def start_download_plugin(self, resource_id, plugin_name):
        server_path = os.path.join(self.base_path, "servers", self.target_server_folder)
        target_path = os.path.join(server_path, "plugins")
        os.makedirs(target_path, exist_ok=True)

        def dl():
            try:
                clean_name = "".join([c for c in plugin_name if c.isalnum() or c in (' ', '.', '_')]).strip()
                dest = os.path.join(target_path, f"{clean_name}.jar")
                
                url = f"https://api.spiget.org/v2/resources/{resource_id}/download"
                headers = {"User-Agent": "SozipLauncher/1.1"}
                
                r = requests.get(url, headers=headers, stream=True, timeout=20)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                    self.after(0, lambda: messagebox.showinfo("Success", f"Installed {plugin_name}!", parent=self.plug_pop))
                else:
                    self.after(0, lambda: messagebox.showerror("Download Error", "Blocked by Spigot. Use INFO button.", parent=self.plug_pop))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Download failed: {e}", parent=self.plug_pop))

        threading.Thread(target=dl, daemon=True).start()

    def on_close(self):
        # Check if self.processes exists and find active ones
        running_servers = []
        if hasattr(self, 'processes'):
            running_servers = [folder for folder, proc in self.processes.items() if proc.poll() is None]
        
        if running_servers:
            msg = (
                "⚠ The following server(s) are still running:\n\n"
                + "\n".join([f"• {s}" for s in running_servers])
                + "\n\nDo you really want to quit the launcher?\n\n"
                "Note: Servers will keep running in the background. "
                "You will need to use Task Manager to stop 'java.exe' later."
            )
            if not messagebox.askyesno("Servers Still Active", msg):
                return  # Stop the closing process

        # Optional: Force kill processes started by the launcher
        if hasattr(self, 'processes'):
            for proc in self.processes.values():
                try:
                    proc.terminate() # Try to close nicely first
                except:
                    pass
        
        self.destroy()
    def setup_custom_skin_loader(self, path, mtype, version):
        """Checks for CustomSkinLoader mod and sets up the config file."""
        # Map launcher types to Modrinth loader filters
        loader_map = {"Fabric": "fabric", "Forge": "forge"}
        if mtype not in loader_map:
            return # Only for Fabric/Forge

        def setup_thread():
            try:
                # 1. Search Modrinth for CustomSkinLoader compatible with this version/loader
                slug = "customskinloader"
                url = f"https://api.modrinth.com/v2/project/{slug}/version"
                params = {"loaders": json.dumps([loader_map[mtype]]), "game_versions": json.dumps([version])}
                
                resp = requests.get(url, params=params)
                if resp.status_code != 200: return
                
                versions = resp.json()
                if not versions: return # Mod not available for this version

                # 2. Download the Mod Jar
                mods_folder = os.path.join(path, "mods")
                os.makedirs(mods_folder, exist_ok=True)
                
                # Check if already exists to avoid redundant downloads
                file_info = versions[0]['files'][0]
                mod_dest = os.path.join(mods_folder, file_info['filename'])
                
                if not os.path.exists(mod_dest):
                    r = requests.get(file_info['url'])
                    with open(mod_dest, "wb") as f:
                        f.write(r.content)

                # 3. Create CustomSkinLoader Folder and Download Config
                # This goes in the instance root (same place as 'mods' folder)
                csl_dir = os.path.join(path, "CustomSkinLoader")
                os.makedirs(csl_dir, exist_ok=True)
                
                config_url = "https://sozip19op.github.io/Sozip-launcher/files/CustomSkinLoader.json"
                config_path = os.path.join(csl_dir, "CustomSkinLoader.json")
                
                # Always update config to ensure it's pointing to your network
                c_res = requests.get(config_url)
                if c_res.status_code == 200:
                    with open(config_path, "wb") as f:
                        f.write(c_res.content)
                        
            except Exception as e:
                print(f"CSL Auto-setup failed: {e}")

        threading.Thread(target=setup_thread, daemon=True).start()
    def start_discord_rpc(self):
        """Starts the signal to Discord using your ID"""
        client_id = "1468150193231761470"
        try:
            self.RPC = Presence(client_id)
            self.RPC.connect()
            self.RPC.update(
                state="Managing Versions",
                details="Main Menu",
                start=time.time(), # This starts the "00:00 elapsed" timer
                large_image="logo" # Make sure to upload an asset named 'logo' in Discord Portal
            )
        
        except Exception as e:
            print(f"Discord RPC Error: {e}")
    def get_required_java_version(self, mc_version):
        try:
            # Extracts the main version number, e.g., "1.20" from "Fabric_1.20.1"
            parts = mc_version.split('_')
            version_str = parts[1] if len(parts) > 1 else mc_version
            major = int(version_str.split('.')[1])
            
            if major >= 21: return 21  # 1.21+
            if major >= 18: return 17  # 1.18 - 1.20
            return 8                   # 1.17 and below (standard fallback)
        except:
            return 8

    def ensure_portable_java(self, java_ver):
        import zipfile, tarfile
        base_path = os.path.join(os.getcwd(), "runtime", f"java-{java_ver}")
        java_exe = os.path.join(base_path, "bin", "javaw.exe" if os.name == "nt" else "bin/java")
        
        if os.path.exists(java_exe):
            return java_exe

        # Adoptium API for portable JRE
        os_name = "windows" if os.name == "nt" else "linux"
        api_url = f"https://api.adoptium.net/v3/binary/latest/{java_ver}/ga/{os_name}/x64/jre/hotspot/normal/eclipse"
        
        print(f"Downloading Portable Java {java_ver}...")
        response = requests.get(api_url, stream=True)
        if response.status_code == 200:
            os.makedirs("runtime", exist_ok=True)
            archive = os.path.join("runtime", "temp_java.zip" if os.name == "nt" else "temp_java.tar.gz")
            with open(archive, 'wb') as f:
                for chunk in response.iter_content(8192): f.write(chunk)
            
            # Extract
            if archive.endswith(".zip"):
                with zipfile.ZipFile(archive, 'r') as z: z.extractall("runtime")
            else:
                with tarfile.open(archive, 'r:gz') as t: t.extractall("runtime")
            
            # Find the extracted folder and rename it to our base_path
            extracted_folder = [d for d in os.listdir("runtime") if d.startswith("jdk") or d.startswith("jre")][0]
            os.rename(os.path.join("runtime", extracted_folder), base_path)
            os.remove(archive)
            return java_exe
        return "java" # Fallback
    def run_game(self):
        import uuid, subprocess, threading

        path = os.path.join(self.base_path, "instances", self.selected_version)
        try:
            required_ver = self.get_required_java_version(self.selected_version)
            portable_java_path = self.ensure_portable_java(required_ver)
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
        self.save_settings()

        launch_id = self.get_launch_id(path)
        if not launch_id:
            messagebox.showerror("Error", "Game files corrupted or not installed properly.")
            return

        network_on = self.sozip_network_enabled.get()

        # UUID + Token
        if network_on:
            final_uuid = self.user_uuid if self.user_uuid else str(uuid.uuid3(uuid.NAMESPACE_DNS, self.username))
            final_token = self.user_token if self.user_token else "0"
        else:
            final_uuid = str(uuid.uuid4())
            final_token = "0"

    # SAFE RAM (prevents 100% CPU crash)
        safe_ram = max(2, min(self.ram, self.max_pc_ram - 2))

    # STABLE JVM ARGS (works on old CPUs like yours)
        jvm_args = [
        f"-Xms2G",
        f"-Xmx{safe_ram}G",
        "-XX:+UseG1GC",
        "-XX:MaxGCPauseMillis=120",
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:G1NewSizePercent=20",
        "-XX:G1ReservePercent=20",
        "-XX:InitiatingHeapOccupancyPercent=15",
        "-XX:G1HeapRegionSize=16M"
    ]


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

        # SAFE agent injection (correct way)
            if network_on:
                injector_path = self.get_auth_injector()
                auth_url = "https://sozip19op-sozip-auth-serve.hf.space"
                cmd = [cmd[0], f"-javaagent:{injector_path}={auth_url}"] + cmd[1:]

            def launch():
                self.withdraw()

                proc = subprocess.Popen(
                    cmd,
                    cwd=path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                proc.wait()

                self.after(0, self.deiconify)

            threading.Thread(target=launch, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Launch Error", str(e))

    def delete_version(self):
        if self.selected_version and messagebox.askyesno("Delete", "Delete version?"):
            shutil.rmtree(os.path.join(self.base_path, "instances", self.selected_version), ignore_errors=True); self.draw_home()

if __name__ == "__main__":
    app = SozipLauncher(); app.mainloop()