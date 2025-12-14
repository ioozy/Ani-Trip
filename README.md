### ⛩️ AniTrip - 君の名は。 (Your Name. ) ###
AniTrip 是一款專為動漫迷打造的沉浸式桌面應用程式。本專案以新海誠導演電影《你的名字。》為主題，整合了地圖導覽、打卡護照與拍立得卡片生成功能，讓使用者能紀錄並創造屬於自己的次元回憶。

## ✨ 核心功能 (Features) ##

    🔍 沉浸式探索 (Feed)：採用瀑布流卡片設計，瀏覽電影中的經典場景。
        ．非同步圖片加載 (Async Loader)：確保介面流暢，不會因為下載圖片而卡頓。
        ．智慧分群 (Clustering)：自動根據地理位置將景點分類（如：新宿站周邊、飛驒市等）。

    🗺️ 互動地圖 (Interactive Map)：
        ．整合 tkintermapview，在地圖上視覺化顯示所有聖地。
        ．動態標記：已打卡與未打卡的景點顯示不同顏色的圖釘。

    📸 拍立得卡片製作 (Scene Card Creator)：
        ．一鍵合成打卡圖：上傳照片後，自動與電影劇照合成。
        ．智慧排版：依照比例 (45:30:25) 自動生成包含地點、時間、片名的精美紀念卡。

    📘 打卡護照 (Passport System)：
        ．紀錄打卡進度與收集成就。
        ．視覺化展示已收集的拍立得回憶牆。
    
## 🏗️ 系統架構與流程 (Architecture Pipeline) ##
本專案採用模組化設計，各組件職責分明。下圖展示了系統的數據流向與處理邏輯：

```mermaid
   graph TD
    %% 定義樣式
    classDef ui fill:#2563EB,stroke:#fff,stroke-width:2px,color:#fff;
    classDef logic fill:#475569,stroke:#fff,stroke-width:2px,color:#fff;
    classDef data fill:#10B981,stroke:#fff,stroke-width:2px,color:#fff;

    subgraph User_Interaction [使用者互動層]
        UI[“🖥️ AnitabiApp (GUI Main)”]:::ui
    end

    subgraph Core_Logic [核心邏輯層]
        direction TB
        AL[“🚀 AsyncImageLoader”]:::logic
        IG[“🎨 ImageGenerator”]:::logic
        MapWidget[“🗺️ Map View”]:::logic
    end

    subgraph Data_Management [資料管理層]
        DM[“📊 DataManager”]:::data
        PM[“💾 PassportManager”]:::data
    end

    subgraph Storage [持久化儲存]
        JSON_S[“(你的名字.json)”]
        JSON_U[“(visited.json)”]
        IMG_Dir[“📂 my_trip_memories/”]
    end

    %% 關係連線
    UI -->|1. 初始化載入| DM
    DM <-->|讀取場景資料| JSON_S
    
    UI -->|2. 檢查打卡狀態| PM
    PM <-->|讀寫使用者紀錄| JSON_U
    
    UI -->|3. 顯示圖片| AL
    AL -->|非同步下載| Web((“🌐 Internet”))
    
    UI -->|4. 開啟地圖| MapWidget
    MapWidget -.->|取得座標| DM
    
    UI -->|5. 製作卡片| IG
    IG -->|合成圖片| IMG_Dir
    IG -->|更新狀態| PM

## 📂 專案結構 ##

    Ani-Trip/
    ├── main.py              # 程式進入點 (Entry Point)
    ├── gui_app.py           # 主要 GUI 介面邏輯 (CustomTkinter)
    ├── data_manager.py      # 資料處理 (Pandas)
    ├── passport_manager.py  # 使用者存檔管理 (JSON)
    ├── image_generator.py   # 圖片合成核心 (Pillow)
    ├── requirements.txt     # 依賴套件清單
    ├── 你的名字.json         # 原始景點資料庫
    └── visited.json         # 使用者打卡紀錄 (自動生成)

## 🚀 快速開始 ##

    1. 安裝依賴確保你的電腦已安裝 Python 3.10 以上版本，並執行：pip install -r requirements.txt
    2. 啟動程式在終端機輸入：python main.py

## 🛠️ Tech Stack ##

    ．Language: PythonGUI 
    ．Framework: CustomTkinter (現代化 UI 風格)
    ．Data Processing: Pandas (高效資料篩選與處理)
    ．Image Processing: Pillow (PIL) (影像濾鏡、裁切、合成)
    ．Map Integration: TkinterMapView (Tile-based 地圖顯示)
    ．Concurrency: concurrent.futures (多執行緒圖片載入)

## 📊 資料來源 ##
本專案之聖地巡禮數據與地圖資訊參考自以下開源專案：
    ．核心 API 資料：Anitabi.cn Document（https://github.com/anitabi/anitabi.cn-document/blob/main/api.md）使用其提供之電影《你的名字。》取景地資料庫。
    ．地圖參考：Anitabi 聖地巡禮地圖（https://www.anitabi.cn/map）

## 🤝 貢獻與版權 ##

    ．本專案僅作學習與交流使用。
    ．電影《你的名字。》相關圖片版權歸屬 CoMix Wave Films 所有。
    ．地圖資料來源：OpenStreetMap。