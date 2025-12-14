from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import datetime

class ImageGenerator:
    def load_image_from_url(self, url):
        """從網址下載圖片 (需要 requests)"""
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        except Exception as e:
            print(f"圖片下載失敗: {e}")
            # 回傳一張灰底圖當作錯誤替代
            return Image.new("RGB", (600, 400), color="#CCCCCC")

    def resize_cover(self, image, target_width, target_height):
        """裁切並縮放圖片以填滿區域 (Object Fit: Cover)"""
        img_ratio = image.width / image.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            new_height = target_height
            new_width = int(new_height * img_ratio)
            img = image.resize((new_width, new_height), Image.LANCZOS)
            left = (new_width - target_width) / 2
            img = img.crop((left, 0, left + target_width, target_height))
        else:
            new_width = target_width
            new_height = int(new_width / img_ratio)
            img = image.resize((new_width, new_height), Image.LANCZOS)
            top = (new_height - target_height) / 2
            img = img.crop((0, top, target_width, top + target_height))
        return img

    def create_card(self, scene_img, user_img, title, location, date_str, layout="Classic"):
        """生成合成卡片"""
        base_width = 800
        target_size = (base_width, int(base_width * 4/3)) # 3:4 比例
        cw, ch = target_size
        
        bg_color = "#F9FAFB"
        text_color = "#1F2937"
        
        # 建立畫布
        canvas = Image.new("RGB", target_size, bg_color)
        draw = ImageDraw.Draw(canvas)
        
        # 簡單字型處理 (如果沒有字型檔，使用預設)
        try:
            # 嘗試載入系統字型 (Windows: msjh.ttc, Mac: PingFang.ttc)
            # 這裡為了通用，先用預設，若要美觀建議放一個 .ttf 在專案資料夾
            font_title = ImageFont.truetype("arial.ttf", 40)
            font_text = ImageFont.truetype("arial.ttf", 20)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        # 版面邏輯
        img_h = int(ch * 0.6)
        each_h = int(img_h / 2)
        
        s_img = self.resize_cover(scene_img, cw, each_h)
        u_img = self.resize_cover(user_img, cw, each_h)
        
        canvas.paste(s_img, (0, 0))
        canvas.paste(u_img, (0, each_h))
        
        # 繪製文字區域
        info_y = img_h + 30
        draw.text((30, info_y), title, fill=text_color, font=font_title)
        draw.text((30, info_y + 60), f"Location: {location}", fill="#4B5563", font=font_text)
        draw.text((30, info_y + 90), f"Date: {date_str}", fill="#6B7280", font=font_text)
        
        # 繪製印章
        draw.ellipse([cw-150, ch-150, cw-30, ch-30], outline="red", width=5)
        draw.text((cw-130, ch-100), "VERIFIED", fill="red", font=font_text)

        return canvas