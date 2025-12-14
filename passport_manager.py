import json
import os

class PassportManager:
    def __init__(self, save_file='visited.json'):
        self.save_file = save_file
        self.visited_ids = self.load_visited()

    def load_visited(self):
        """從 JSON 讀取已打卡的 ID 列表"""
        if not os.path.exists(self.save_file):
            return []
        try:
            with open(self.save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('visited', [])
        except Exception as e:
            print(f"讀取存檔失敗: {e}")
            return []

    def save_visited(self):
        """儲存打卡紀錄"""
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump({'visited': self.visited_ids}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"存檔失敗: {e}")

    def check_in(self, scene_id):
        """執行打卡"""
        if scene_id not in self.visited_ids:
            self.visited_ids.append(scene_id)
            self.save_visited()
            return True
        return False

    def is_visited(self, scene_id):
        return scene_id in self.visited_ids

    def get_visited_count(self):
        return len(self.visited_ids)
        
    def get_user_title(self):
        """根據數量回傳稱號 (移植自您的 Streamlit 邏輯)"""
        count = self.get_visited_count()
        if count >= 10: return "🏆 二次元的神"
        if count >= 5: return "🥇 聖地巡禮大師"
        if count >= 3: return "🥈 資深阿宅"
        if count >= 1: return "🥉 見習巡禮者"
        return "🌱 路人A"