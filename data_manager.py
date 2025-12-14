import pandas as pd
import os

class DataManager:
    def __init__(self, json_file='你的名字.json'):
        self.json_file = json_file
        self.df = self.load_data()

    def load_data(self):
        """讀取 JSON 資料並轉為 DataFrame"""
        if not os.path.exists(self.json_file):
            print(f"錯誤：找不到 {self.json_file}")
            # 回傳一個空的 DataFrame 結構以防出錯
            return pd.DataFrame(columns=['id', 'name', 'cn', 'series', 'geo', 's', 'image'])
        
        try:
            df = pd.read_json(self.json_file)
            # 確保有 series 欄位，若沒有則預設為 "你的名字"
            if 'series' not in df.columns:
                df['series'] = '你的名字。'
            return df
        except Exception as e:
            print(f"讀取資料失敗: {e}")
            return pd.DataFrame()

    def get_all_scenes(self):
        """回傳所有景點資料 (List of Dicts)"""
        if self.df.empty:
            return []
        return self.df.to_dict('records')

    def search_scenes(self, keyword):
        """根據關鍵字搜尋 (支援名稱、中文名稱、地區)"""
        if self.df.empty or not keyword:
            return self.get_all_scenes()
        
        # 使用 Pandas 的字串包含搜尋 (Case Insensitive)
        # 對應課程 Week 13: 資料篩選
        mask = (
            self.df['name'].str.contains(keyword, case=False, na=False) |
            self.df['cn'].str.contains(keyword, case=False, na=False)
        )
        result = self.df[mask]
        return result.to_dict('records')

    def format_time(self, seconds):
        """將秒數轉換為 mm:ss 格式"""
        if pd.isna(seconds) or seconds is None:
            return "N/A"
        try:
            sec = int(seconds)
            m = sec // 60
            s = sec % 60
            return f"{m:02d}:{s:02d}"
        except:
            return str(seconds)

    def get_coordinates(self, scene_data):
        """安全取得經緯度"""
        geo = scene_data.get('geo', [])
        if isinstance(geo, list) and len(geo) >= 2:
            return geo[0], geo[1]
        return None, None
    
    def get_image_path(self, scene_data):
        """取得圖片路徑"""
        return scene_data.get('image', '')
    
def main():
    dm = DataManager()
    all_scenes = dm.get_all_scenes()
    print(f"總共有 {len(all_scenes)} 個景點資料。")
    search_keyword = "東京"
    search_results = dm.search_scenes(search_keyword)
    print(f"搜尋關鍵字 '{search_keyword}'，找到 {len(search_results)} 個結果。")
    for scene in search_results:
        print(scene)

if __name__ == "__main__":
    main()