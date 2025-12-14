import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import tkintermapview
import os
import platform
import math
import datetime
import threading
import requests
from io import BytesIO
import concurrent.futures
import pandas as pd
import random

# 引用模組
from data_manager import DataManager
from passport_manager import PassportManager
from image_generator import ImageGenerator

# ==========================================
# 🛠️ 系統與外觀設定
# ==========================================

ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("blue")

SYSTEM_OS = platform.system()
SAVE_DIR = "my_trip_memories"
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

# 字體系統
if SYSTEM_OS == "Darwin":
    FONT_UI = "PingFang TC"
else:
    FONT_UI = "Microsoft JhengHei"

FONT_MAIN = (FONT_UI, 12)
FONT_BOLD = (FONT_UI, 12, "bold")
FONT_TITLE = (FONT_UI, 16, "bold") 
FONT_HERO = (FONT_UI, 28, "bold")
STAMP_FONT = "Arial"

# ==========================================
# 🚀 非同步圖片載入器
# ==========================================
class AsyncImageLoader:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.cache = {}

    def load(self, url, callback, size=None, processor=None):
        if not url: return
        proc_id = id(processor) if processor else "raw"
        cache_key = (url, size, proc_id)

        if cache_key in self.cache:
            img = self.cache[cache_key]
            callback(img)
            return

        self.executor.submit(self._download, url, callback, size, processor, cache_key)

    def _download(self, url, callback, size, processor, cache_key):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pil_img = Image.open(BytesIO(response.content)).convert("RGB")
                
                if size:
                    pil_img = self._resize_cover(pil_img, size)
                
                if processor:
                    pil_img = processor(pil_img)

                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                self.cache[cache_key] = ctk_img
                callback(ctk_img)
        except Exception as e:
            print(f"Image load failed: {e}")

    def _resize_cover(self, image, size):
        w, h = size
        img_ratio = image.width / image.height
        ratio = w / h
        if img_ratio > ratio:
            new_height = h
            new_width = int(new_height * img_ratio)
            img = image.resize((new_width, new_height), Image.LANCZOS)
            left = (new_width - w) / 2
            img = img.crop((left, 0, left + w, h))
        else:
            new_width = w
            new_height = int(new_width / img_ratio)
            img = image.resize((new_width, new_height), Image.LANCZOS)
            top = (new_height - h) / 2
            img = img.crop((0, top, w, top + h))
        return img

loader = AsyncImageLoader()

# ==========================================
# 📱 主程式 App
# ==========================================

class AnitabiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("AniTrip － 君の名は。")
        self.geometry("1300x850")
        
        # 資料初始化
        self.dm = DataManager()
        self.pm = PassportManager()
        self.ig = ImageGenerator()
        
        self.all_scenes = self.dm.get_all_scenes()
        self.clusters = self._generate_clusters(self.all_scenes)
        self.current_filter = 'all'
        
        self.scene_to_cluster_map = {}
        for c in self.clusters:
            for p in c['points']: self.scene_to_cluster_map[p['id']] = c['name']

        self.custom_pins = {}
        
        # 佈局
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_content()
        
        self.show_feed()

    def _generate_clusters(self, points):
        if not points: return []
        def dist(p1, p2): return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
        clusters = []
        unassigned = points[:]
        while unassigned:
            center = unassigned.pop(0)
            c_geo = center.get('geo', [0,0])
            if not c_geo: continue
            group = [center]
            neighbors = [p for p in unassigned if dist(c_geo, p.get('geo', [0,0])) < 0.02]
            for n in neighbors:
                group.append(n)
                unassigned.remove(n)
            name = center['name'].split(' ')[0].split('駅')[0] + " 周邊"
            clusters.append({"name": name, "points": group})
        clusters.sort(key=lambda c: len(c['points']), reverse=True)
        return clusters

    def format_seconds(self, seconds):
        if pd.isna(seconds) or seconds == "": return "--:--"
        try:
            sec = int(seconds)
            return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}" if sec >= 3600 else f"{(sec%3600)//60:02d}:{sec%60:02d}"
        except: return str(seconds)

    # --- UI 結構 ---
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="white")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        logo = ctk.CTkLabel(self.sidebar, text="🅰 AniTrip", font=("Arial", 28, "bold"), text_color="#2563EB")
        logo.pack(pady=40, padx=30, anchor="w")

        self.create_nav_btn("🔍  探索景點", self.show_feed)
        self.create_nav_btn("🗺️  地圖模式", self.show_map)
        self.create_nav_btn("📘  打卡護照", self.show_passport)

    def create_nav_btn(self, text, cmd):
        btn = ctk.CTkButton(self.sidebar, text=text, font=FONT_BOLD, fg_color="transparent", 
                            text_color="#64748B", hover_color="#EFF6FF", anchor="w", height=50, command=cmd)
        btn.pack(fill="x", padx=10, pady=5)

    def setup_content(self):
        self.content = ctk.CTkFrame(self, fg_color="#F8FAFC", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def clear_content(self):
        for w in self.content.winfo_children(): w.destroy()

    # ==========================================
    # 🔍 Feed Page
    # ==========================================
    def show_feed(self):
        self.clear_content()
        main_scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True)

        # Hero Header
        hero_height = 340
        hero = ctk.CTkFrame(main_scroll, height=hero_height, fg_color="#0F172A", corner_radius=0)
        hero.pack(fill="x")
        hero.grid_rowconfigure(0, weight=1)
        hero.grid_columnconfigure(0, weight=1)

        bg_lbl = ctk.CTkLabel(hero, text="")
        bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

        def hero_bg_processor(img):
            img = img.filter(ImageFilter.GaussianBlur(radius=15))
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.5) 
            if img.mode != 'RGBA': img = img.convert('RGBA')
            overlay = Image.new('RGBA', img.size, (0,0,0,0))
            draw = ImageDraw.Draw(overlay)
            w, h = img.size
            grad_start = int(h * 0.3)
            grad_h = h - grad_start
            for y in range(grad_h):
                alpha = int(230 * (y / grad_h))
                draw.line([(0, grad_start+y), (w, grad_start+y)], fill=(0, 0, 0, alpha))
            return Image.alpha_composite(img, overlay)

        bg_url = "https://upload.wikimedia.org/wikipedia/zh/4/4e/Your_name_poster.jpg"
        local_poster_file = "封面.jpeg"
        
        if os.path.exists(local_poster_file):
            def load_local_bg():
                try:
                    pil = Image.open(local_poster_file).convert("RGB")
                    pil = hero_bg_processor(pil)
                    w, h = 1200, hero_height
                    img_ratio = pil.width / pil.height
                    target_ratio = w / h
                    if img_ratio > target_ratio:
                        new_h = h
                        new_w = int(new_h * img_ratio)
                        pil = pil.resize((new_w, new_h), Image.LANCZOS)
                        left = (new_w - w) // 2
                        pil = pil.crop((left, 0, left+w, h))
                    else:
                        new_w = w
                        new_h = int(new_w / img_ratio)
                        pil = pil.resize((new_w, new_h), Image.LANCZOS)
                        top = (new_h - h) // 2
                        pil = pil.crop((0, top, w, top+h))
                    ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(1200, hero_height))
                    self.after(0, lambda: bg_lbl.configure(image=ctk_img))
                except: pass
            threading.Thread(target=load_local_bg, daemon=True).start()
        else:
            loader.load(bg_url, lambda i: self.after(0, lambda: bg_lbl.configure(image=i)), 
                        size=(1200, hero_height), processor=hero_bg_processor)

        content_frame = ctk.CTkFrame(hero, fg_color="transparent")
        content_frame.place(relx=0.08, rely=0.5, anchor="w", relwidth=0.85, relheight=0.8)

        poster_frame = ctk.CTkFrame(content_frame, width=180, height=260, fg_color="white", corner_radius=4, border_width=0)
        poster_frame.pack(side="left", padx=(0, 40))
        poster_frame.pack_propagate(False) 
        poster_img = ctk.CTkLabel(poster_frame, text="", width=172, height=252, corner_radius=0, fg_color="#334155")
        poster_img.place(relx=0.5, rely=0.5, anchor="center")
        
        def load_clean_poster():
            if os.path.exists(local_poster_file):
                try:
                    pil = Image.open(local_poster_file).convert("RGB")
                    pil = ImageOps.fit(pil, (172, 252), method=Image.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(172, 252))
                    self.after(0, lambda: poster_img.configure(image=ctk_img))
                except: pass
            else:
                loader.load(bg_url, lambda i: self.after(0, lambda: poster_img.configure(image=i)), size=(172, 252))
        threading.Thread(target=load_clean_poster, daemon=True).start()

        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="y", pady=10)

        ctk.CTkLabel(info_frame, text="君の名は。", font=(FONT_UI, 20), text_color="#CBD5E1", anchor="w").pack(anchor="w")
        ctk.CTkLabel(info_frame, text="你的名字。", font=(FONT_UI, 48, "bold"), text_color="white", anchor="w").pack(anchor="w", pady=(0, 15))

        tags_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        tags_frame.pack(anchor="w", pady=(0, 25))
        
        def create_pill_tag(parent, text):
            btn = ctk.CTkButton(parent, text=text, font=("Arial", 12, "bold"), 
                                fg_color="transparent", border_width=1, border_color="#94A3B8", 
                                text_color="white", hover=False, height=28, corner_radius=14, width=60)
            btn.pack(side="left", padx=(0, 10))

        create_pill_tag(tags_frame, "2016")
        create_pill_tag(tags_frame, "Romance")
        create_pill_tag(tags_frame, "Fantasy")
        create_pill_tag(tags_frame, f"{len(self.all_scenes)} SCENES")

        btn_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        btn_frame.pack(anchor="w")

        map_btn = ctk.CTkButton(btn_frame, text="🗺️  開啟地圖", font=(FONT_UI, 15, "bold"), 
                                fg_color="#3B82F6", hover_color="#2563EB", 
                                height=45, width=140, corner_radius=22, command=self.show_map)
        map_btn.pack(side="left", padx=(0, 15))

        passport_btn = ctk.CTkButton(btn_frame, text="📘  打卡護照", font=(FONT_UI, 15, "bold"),
                                     fg_color="transparent", border_width=1, border_color="#64748B",
                                     hover_color="#334155", height=45, width=140, corner_radius=22, command=self.show_passport)
        passport_btn.pack(side="left")

        filter_bar = ctk.CTkScrollableFrame(main_scroll, orientation="horizontal", height=60, fg_color="transparent")
        filter_bar.pack(fill="x", padx=30, pady=(30, 20))
        self.create_pill(filter_bar, "全部區域", 'all')
        for i, c in enumerate(self.clusters[:15]):
            label = f"{c['name']} ({len(c['points'])})"
            self.create_pill(filter_bar, label, i)

        target = self.clusters if self.current_filter == 'all' else [self.clusters[self.current_filter]]
        limit = 3 if self.current_filter == 'all' else len(target)
        for c in target[:limit]:
            title_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
            title_frame.pack(fill="x", padx=40, pady=(15, 5))
            ctk.CTkFrame(title_frame, width=4, height=24, fg_color="#2563EB", corner_radius=2).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(title_frame, text=c['name'], font=(FONT_UI, 18, "bold"), text_color="#0F172A").pack(side="left")
            count_lbl = ctk.CTkFrame(title_frame, fg_color="#F1F5F9", corner_radius=10)
            count_lbl.pack(side="left", padx=10)
            ctk.CTkLabel(count_lbl, text=f"{len(c['points'])} Scenes", font=("Arial", 11), text_color="#64748B").pack(padx=8, pady=2)
            for s in c['points']:
                self.create_card(main_scroll, s)
        
        if self.current_filter == 'all':
            ctk.CTkLabel(main_scroll, text="...請點選上方區域查看更多...", text_color="#999").pack(pady=20)

    def create_pill(self, parent, text, val):
        active = (self.current_filter == val)
        fg = "#2563EB" if active else "white"
        txt = "white" if active else "#334155"
        border_col = "#2563EB" if active else "#E2E8F0"
        border_w = 0 if active else 1
        btn = ctk.CTkButton(parent, text=text, fg_color=fg, text_color=txt, border_width=border_w, border_color=border_col, corner_radius=20, font=FONT_BOLD, width=len(text)*16+30, command=lambda v=val: [setattr(self, 'current_filter', v), self.show_feed()])
        btn.pack(side="left", padx=5)

    def create_card(self, parent, scene):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        card.pack(fill="x", padx=40, pady=8)
        card.grid_columnconfigure(1, weight=1)
        img = ctk.CTkLabel(card, text="", width=240, height=160, fg_color="#F1F5F9", corner_radius=8)
        img.grid(row=0, column=0, rowspan=2, padx=12, pady=12)
        def update_image(i):
            if self.winfo_exists(): img.configure(image=i)
        loader.load(scene.get('image'), lambda i: self.after(0, lambda: update_image(i)), size=(240, 160))
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        cn = scene.get('cn'); name = cn if cn and str(cn).lower() != 'nan' else scene['name']
        ctk.CTkLabel(info, text=name, font=FONT_TITLE, text_color="#0F172A", anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=f"原名：{scene['name']}  •  {self.format_seconds(scene.get('s'))}", font=FONT_MAIN, text_color="#64748B", anchor="w").pack(fill="x", pady=(2, 10))
        btns = ctk.CTkFrame(info, fg_color="transparent")
        btns.pack(side="bottom", fill="x")
        if self.pm.is_visited(scene['id']):
            ctk.CTkLabel(btns, text="✅ 已完成打卡", font=FONT_BOLD, text_color="#10B981").pack(side="left")
        else:
            ctk.CTkButton(btns, text="打卡 Challenge", fg_color="#2563EB", hover_color="#1D4ED8", command=lambda: self.open_overlay(scene)).pack(side="left")

    # ==========================================
    # 🗺️ Map Page
    # ==========================================
    def show_map(self):
        self.clear_content()
        map_frame = ctk.CTkFrame(self.content, fg_color="white")
        map_frame.pack(fill="both", expand=True)
        self.map_widget = tkintermapview.TkinterMapView(map_frame, corner_radius=0)
        self.map_widget.pack(fill="both", expand=True)
        if self.all_scenes:
            s = random.choice(self.all_scenes)
            self.map_widget.set_position(s['geo'][0], s['geo'][1])
            self.map_widget.set_zoom(14)
        markers_to_add = []
        for c in self.clusters:
            for s in c['points']: markers_to_add.append(s)
        self.add_markers_lazy(markers_to_add, 0)

    def add_markers_lazy(self, markers, index):
        batch_size = 5
        limit = min(index + batch_size, len(markers))
        for i in range(index, limit):
            s = markers[i]
            visited = self.pm.is_visited(s['id'])
            if not hasattr(self, 'map_widget') or not self.map_widget.winfo_exists(): return
            self.map_widget.set_marker(s['geo'][0], s['geo'][1], text=None, icon=self._get_pin_icon(visited), command=lambda m, data=s: self.open_map_card(data))
        if limit < len(markers): self.after(10, lambda: self.add_markers_lazy(markers, limit))

    def _get_pin_icon(self, visited):
        color = "#10B981" if visited else "#EF4444"
        key = f"pin_{color}"
        if key in self.custom_pins: return self.custom_pins[key]
        img = Image.new("RGBA", (60, 60), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((10, 5, 50, 45), fill=color)
        draw.polygon([(10, 25), (50, 25), (30, 60)], fill=color)
        draw.ellipse((20, 15, 40, 35), fill="white")
        icon = ImageTk.PhotoImage(img)
        self.custom_pins[key] = icon
        return icon

    def open_map_card(self, scene):
        if hasattr(self, 'map_card') and self.map_card.winfo_exists(): self.map_card.destroy()
        self.map_card = ctk.CTkFrame(self.map_widget, fg_color="white", height=160, corner_radius=16, border_width=0)
        self.map_card.place(relx=0.5, rely=0.92, anchor="s", relwidth=0.5)
        ctk.CTkFrame(self.map_card, height=4, fg_color="#2563EB", corner_radius=0).pack(fill="x", side="top")
        grid = ctk.CTkFrame(self.map_card, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=16, pady=12)
        img = ctk.CTkLabel(grid, text="", width=120, height=90, fg_color="#F1F5F9", corner_radius=8)
        img.pack(side="left")
        loader.load(scene.get('image'), lambda i: self.after(0, lambda: img.configure(image=i)), size=(120, 90))
        info = ctk.CTkFrame(grid, fg_color="transparent")
        info.pack(side="left", padx=16, fill="both", expand=True)
        cn = scene.get('cn')
        title_name = cn if cn and str(cn).lower() != 'nan' else scene['name']
        ctk.CTkLabel(info, text=title_name, font=FONT_BOLD, text_color="#0F172A").pack(anchor="w")
        sub_text = f"原名：{scene['name']}  •  {self.format_seconds(scene.get('s'))}"
        ctk.CTkLabel(info, text=sub_text, font=("Arial", 10), text_color="#64748B", anchor="w").pack(anchor="w")
        btns = ctk.CTkFrame(info, fg_color="transparent")
        btns.pack(anchor="w", pady=5)
        if self.pm.is_visited(scene['id']):
            ctk.CTkLabel(btns, text="✅ 已完成", text_color="#10B981", font=FONT_BOLD).pack(side="left")
        else:
            ctk.CTkButton(btns, text="打卡 Challenge", height=28, fg_color="#2563EB", command=lambda: self.open_overlay(scene)).pack(side="left")
        ctk.CTkButton(self.map_card, text="✕", width=30, height=30, fg_color="transparent", text_color="#94A3B8", command=self.map_card.destroy).place(relx=0.96, rely=0.05, anchor="ne")

    # ==========================================
    # 📘 Passport
    # ==========================================
    def show_passport(self):
        self.clear_content()
        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header_frame = ctk.CTkFrame(scroll, fg_color="white", corner_radius=20)
        header_frame.pack(fill="x", padx=40, pady=30)
        
        def get_user_avatar():
            av_size = 120
            img = Image.new("RGBA", (av_size, av_size), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((0, 0, av_size, av_size), fill="#2563EB")
            try: fnt = ImageFont.truetype("Arial Bold.ttf", 60)
            except: fnt = ImageFont.load_default()
            text = "R"
            bbox = draw.textbbox((0, 0), text, font=fnt)
            w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text(((av_size-w)/2, (av_size-h)/2 - 5), text, fill="white", font=fnt)
            return ctk.CTkImage(img, size=(70, 70))

        left_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_box.pack(side="left", padx=30, pady=25)
        ctk.CTkLabel(left_box, text="", image=get_user_avatar()).pack(side="left", padx=(0, 20))
        text_box = ctk.CTkFrame(left_box, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="Rita's Passport", font=("Arial", 26, "bold"), text_color="#0F172A").pack(anchor="w")
        ctk.CTkLabel(text_box, text="尋找君の名は • 打卡回憶", font=("Arial", 13), text_color="#64748B").pack(anchor="w")

        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right", padx=40)
        total_visited = self.pm.get_visited_count()
        visited_clusters_count = len([c for c in self.clusters if any(self.pm.is_visited(p['id']) for p in c['points'])])
        ctk.CTkFrame(right_box, width=2, height=50, fg_color="#E2E8F0").pack(side="right", padx=20)
        def create_stat(parent, num, label):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(side="right", padx=20)
            ctk.CTkLabel(f, text=str(num), font=("Arial", 32, "bold"), text_color="#2563EB").pack()
            ctk.CTkLabel(f, text=label, font=("Arial", 11, "bold"), text_color="#94A3B8").pack()
        create_stat(right_box, visited_clusters_count, "REGIONS")
        create_stat(right_box, total_visited, "STAMPS")

        grid_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        grid_frame.pack(fill="both", padx=30, pady=10)
        
        active_clusters = []
        for c in self.clusters:
            visited_in_cluster = [p for p in c['points'] if self.pm.is_visited(p['id'])]
            if visited_in_cluster:
                active_clusters.append({"cluster_data": c, "visited_scenes": visited_in_cluster})
        
        if not active_clusters:
             ctk.CTkLabel(scroll, text="尚未有旅程紀錄，快去地圖打卡吧！", font=FONT_TITLE, text_color="#94a3b8").pack(pady=50)
             return

        for i, item in enumerate(active_clusters):
            row, col = divmod(i, 3) 
            self.create_region_collection_card(grid_frame, item, row, col)

    def create_region_collection_card(self, parent, item, row, col):
        cluster = item['cluster_data']
        visited_scenes = item['visited_scenes']
        card = ctk.CTkFrame(parent, width=300, height=320, fg_color="white", corner_radius=16)
        card.grid(row=row, column=col, padx=15, pady=15)
        card.grid_propagate(False)
        def on_click(event):
            self.show_passport_detail(cluster['name'], visited_scenes)
        card.bind("<Button-1>", on_click)
        img_h = 200
        img_container = ctk.CTkLabel(card, text="", width=280, height=img_h, corner_radius=12, fg_color="#1E293B")
        img_container.place(x=10, y=10)
        img_container.bind("<Button-1>", on_click)
        rep_point = cluster['points'][0]
        rep_image_url = rep_point.get('image')
        def heavy_gradient_processor(img):
            if img.mode != 'RGBA': img = img.convert('RGBA')
            overlay = Image.new('RGBA', img.size, (0,0,0,0))
            draw = ImageDraw.Draw(overlay)
            w, h = img.size
            gradient_h = int(h * 0.7) 
            start_y = h - gradient_h
            for y in range(gradient_h):
                alpha = int(240 * (y / gradient_h))
                draw.line([(0, start_y + y), (w, start_y + y)], fill=(0, 0, 0, alpha))
            return Image.alpha_composite(img, overlay)
        loader.load(rep_image_url, lambda i: self.after(0, lambda: img_container.configure(image=i)), size=(280, img_h), processor=heavy_gradient_processor)
        lbl_series = ctk.CTkLabel(img_container, text="REGION COLLECTION", font=("Arial", 9, "bold"), text_color="#E2E8F0", bg_color="transparent")
        lbl_series.place(x=15, y=145)
        lbl_title = ctk.CTkLabel(img_container, text=cluster['name'], font=(FONT_UI, 18, "bold"), text_color="white", bg_color="transparent")
        lbl_title.place(x=15, y=165)
        lbl_series.bind("<Button-1>", on_click)
        lbl_title.bind("<Button-1>", on_click)
        count_val = ctk.CTkLabel(card, text=f"{len(visited_scenes)}", font=("Arial", 28, "bold"), text_color="#0F172A")
        count_val.place(x=20, y=220)
        count_lbl = ctk.CTkLabel(card, text="MEMORIES COLLECTED", font=("Arial", 10, "bold"), text_color="#94A3B8")
        count_lbl.place(x=20, y=255)
        update_lbl = ctk.CTkLabel(card, text=f"Last update: {datetime.date.today()}", font=("Arial", 9), text_color="#CBD5E1")
        update_lbl.place(x=20, y=280)
        icon_lbl = ctk.CTkLabel(card, text="📖", font=("Arial", 20), text_color="#2563EB")
        icon_lbl.place(x=250, y=230)
        count_val.bind("<Button-1>", on_click)
        count_lbl.bind("<Button-1>", on_click)
        icon_lbl.bind("<Button-1>", on_click)

    def show_passport_detail(self, title, scenes):
        self.clear_content()
        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        header = ctk.CTkFrame(scroll, fg_color="transparent", height=60)
        header.pack(fill="x", padx=40, pady=20)
        back_btn = ctk.CTkButton(header, text="←", font=("Arial", 20), width=40, height=40, corner_radius=20, fg_color="white", text_color="black", hover_color="#E2E8F0", command=self.show_passport)
        back_btn.pack(side="left")
        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(side="left", padx=20)
        ctk.CTkLabel(info_frame, text=title, font=("Microsoft JhengHei", 24, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"共 {len(scenes)} 張回憶卡", font=("Arial", 12), text_color="#64748B").pack(anchor="w")
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="both", padx=40, pady=10)
        for i, s in enumerate(scenes):
            r, c = divmod(i, 3) 
            self.create_memory_polaroid(grid, s, r, c)

    def create_memory_polaroid(self, parent, scene, row, col):
        card = ctk.CTkFrame(parent, width=280, height=320, fg_color="transparent")
        card.grid(row=row, column=col, padx=15, pady=15)
        file_path = os.path.join(SAVE_DIR, f"{scene['id']}.png")
        img_lbl = ctk.CTkLabel(card, text="", corner_radius=8)
        img_lbl.pack()
        def load_image_smartly():
            target_path = file_path if os.path.exists(file_path) else None
            if target_path:
                try: pil = Image.open(target_path)
                except: pil = None
            else:
                try:
                    r = requests.get(scene.get('image'), timeout=3)
                    pil = Image.open(BytesIO(r.content)).convert("RGB")
                except: pil = None
            if pil:
                w_disp = 280
                # 這裡不需要 strict ratio，只要維持原圖比例縮放即可
                ratio = w_disp / pil.width
                h_disp = int(pil.height * ratio)
                pil_resized = pil.resize((w_disp, h_disp), Image.LANCZOS)
                ctk_img = ctk.CTkImage(pil_resized, size=(w_disp, h_disp))
                self.after(0, lambda: img_lbl.configure(image=ctk_img))
            else:
                self.after(0, lambda: img_lbl.configure(text="No Image", text_color="grey"))
        threading.Thread(target=load_image_smartly).start()

    # ==========================================
    # 🌑 打卡 Overlay (🔥【最終修正】所見即所得：嚴格 45/30/25 比例)
    # ==========================================
    def open_overlay(self, scene):
        top = ctk.CTkToplevel(self)
        top.geometry("1100x800")
        top.title("Scene Card Creator")
        top.grab_set() 
        top.configure(fg_color="#0F172A")
        
        container = ctk.CTkFrame(top, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")

        # --- 1. UI 顯示部分 ---
        # 總高度 540px
        card_w, card_h = 360, 540
        card_frame = ctk.CTkFrame(container, width=card_w, height=card_h, fg_color="white", corner_radius=12)
        card_frame.pack(pady=(0, 30))
        card_frame.grid_propagate(False) 
        
        # 定義比例 (45% : 30% : 25%)
        h1 = int(card_h * 0.45) # Scene
        h2 = int(card_h * 0.30) # User
        h3 = card_h - h1 - h2   # Info (25%)

        # 1. Scene Image (Top)
        scene_lbl = ctk.CTkLabel(card_frame, text="", width=card_w, height=h1, corner_radius=0)
        scene_lbl.place(x=0, y=0)
        loader.load(scene.get('image'), lambda i: self.after(0, lambda: scene_lbl.configure(image=i)), size=(card_w, h1))
        
        # 2. User Image (Middle)
        user_lbl = ctk.CTkLabel(card_frame, text="📷 Upload Photo", font=("Arial", 14), text_color="#94A3B8", fg_color="#F1F5F9", width=card_w, height=h2, corner_radius=0)
        user_lbl.place(x=0, y=h1)
        
        # 3. Info Area (Bottom) - White Background
        info_area = ctk.CTkFrame(card_frame, fg_color="white", width=card_w, height=h3, corner_radius=0)
        info_area.place(x=0, y=h1 + h2)
        
        cn_name = scene.get('cn') if scene.get('cn') and str(scene.get('cn')).lower() != 'nan' else scene['name']
        ctk.CTkLabel(info_area, text=cn_name, font=("Microsoft JhengHei", 18, "bold"), text_color="black", anchor="w").place(x=20, y=15)
        sub_info = f"{scene['name']} | {self.format_seconds(scene.get('s'))}"
        ctk.CTkLabel(info_area, text=sub_info, font=("Arial", 11), text_color="#64748B", anchor="w").place(x=20, y=45)
        date_str = datetime.date.today().strftime("%Y/%m/%d")
        ctk.CTkLabel(info_area, text=f"{date_str} • Takayama/Tokyo", font=("Arial", 10), text_color="#94A3B8", anchor="w").place(x=20, y=65)

        stamp_canvas = ctk.CTkCanvas(info_area, width=80, height=80, bg="white", highlightthickness=0)
        stamp_canvas.place(x=card_w-90, y=5)
        stamp_canvas.create_oval(5, 5, 75, 75, outline="#EF4444", width=2)
        stamp_canvas.create_text(40, 30, text="ANITRIP", fill="#EF4444", font=("Arial", 8, "bold"))
        stamp_canvas.create_text(40, 50, text="SCENE", fill="#EF4444", font=("Arial", 8, "bold"))

        ctrl_frame = ctk.CTkFrame(container, fg_color="transparent")
        ctrl_frame.pack()
        self.user_upload_pil = None 

        def _select_photo(event=None):
            path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg")])
            if path:
                try:
                    pil = Image.open(path).convert("RGB")
                    self.user_upload_pil = pil 
                    # UI 顯示 (Object Fit: Cover)
                    display_img = ImageOps.fit(pil, (card_w, h2), method=Image.LANCZOS)
                    ctk_img = ctk.CTkImage(display_img, size=(card_w, h2))
                    user_lbl.configure(image=ctk_img, text="") 
                    btn_save.configure(state="normal", fg_color="#2563EB") 
                except Exception as e:
                    messagebox.showerror("Error", f"圖片讀取失敗: {e}")
        user_lbl.bind("<Button-1>", _select_photo)

        # --- 2. 存檔部分 (Logic) ---
        # 必須完全依照上面的 h1, h2, h3 比例來繪製
        def _save_and_close():
            if not self.user_upload_pil: return
            try:
                scale = 3 
                out_w, out_h = card_w * scale, card_h * scale
                
                # 計算真實像素高度 (Strict Ratio)
                h1_real = h1 * scale
                h2_real = h2 * scale
                h3_real = out_h - h1_real - h2_real
                
                canvas = Image.new("RGB", (out_w, out_h), "white")
                draw = ImageDraw.Draw(canvas)
                
                # 1. Scene Image
                r = requests.get(scene.get('image'))
                scene_pil = Image.open(BytesIO(r.content)).convert("RGB")
                scene_resized = ImageOps.fit(scene_pil, (out_w, h1_real), method=Image.LANCZOS)
                canvas.paste(scene_resized, (0, 0))
                
                # 2. User Image
                user_resized = ImageOps.fit(self.user_upload_pil, (out_w, h2_real), method=Image.LANCZOS)
                canvas.paste(user_resized, (0, h1_real))
                
                # 3. Info Area (White Background)
                info_y_real = h1_real + h2_real
                draw.rectangle([(0, info_y_real), (out_w, out_h)], fill="white")

                # 4. Text
                font_path = "arial.ttf" 
                system = platform.system()
                if system == "Darwin": font_path = "/System/Library/Fonts/PingFang.ttc" 
                elif system == "Windows": font_path = "msjh.ttc"
                try:
                    font_title = ImageFont.truetype(font_path, 18 * scale) 
                    font_sub = ImageFont.truetype("Arial.ttf", 11 * scale)
                except:
                    font_title = ImageFont.load_default()
                    font_sub = ImageFont.load_default()
                
                text_x = 20 * scale
                # 文字基線相對於 info_y_real
                draw.text((text_x, info_y_real + 15*scale), cn_name, fill="black", font=font_title)
                draw.text((text_x, info_y_real + 50*scale), sub_info, fill="#64748B", font=font_sub)
                draw.text((text_x, info_y_real + 75*scale), f"{date_str} • Takayama/Tokyo", fill="#94A3B8", font=font_sub)
                
                # 5. Stamp
                stamp_cx, stamp_cy = out_w - 50*scale, info_y_real + 40*scale
                r = 35 * scale
                draw.ellipse((stamp_cx-r, stamp_cy-r, stamp_cx+r, stamp_cy+r), outline="#EF4444", width=3*scale)
                draw.text((stamp_cx-25*scale, stamp_cy-10*scale), "ANITRIP", fill="#EF4444", font=font_sub)
                draw.text((stamp_cx-25*scale, stamp_cy+5*scale), "SCENE", fill="#EF4444", font=font_sub)

                file_name = f"{scene['id']}.png"
                save_path = os.path.join(SAVE_DIR, file_name)
                canvas.save(save_path)
                
                self.pm.check_in(scene['id'])
                messagebox.showinfo("Success", "Scene Card 已製作並收藏！")
                top.destroy()
                self.show_feed() 
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

        btn_upload = ctk.CTkButton(ctrl_frame, text="📷 Select Photo", command=_select_photo, width=160, height=40, fg_color="#334155", hover_color="#475569")
        btn_upload.pack(side="left", padx=10)
        btn_save = ctk.CTkButton(ctrl_frame, text="💾 Generate Scene Card", command=_save_and_close, width=200, height=40, fg_color="#94A3B8", state="disabled") 
        btn_save.pack(side="left", padx=10)