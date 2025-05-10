# 方形海演出訂票系統

一個基於 Django 的網頁訂票系統，為演出活動提供線上座位預訂功能。

## 功能特點

- 使用者可選擇演出日期和購票數量
- 互動式座位地圖，即時顯示可用/已訂座位
- 安全的訂票流程，防止超額訂票
- 管理員後台，方便管理訂單和座位

## 技術框架

- Django 4.x/5.x
- Bootstrap 5
- JavaScript
- SQLite 資料庫

## 安裝說明

1. 複製專案
```
git clone https://github.com/你的用戶名/ticket_booking.git
cd ticket_booking
```

2. 建立虛擬環境並安裝依賴
```
python -m venv env
source env/bin/activate  # 在 Windows 上使用 env\Scripts\activate
pip install -r requirements.txt
```

3. 執行資料庫遷移
```
python manage.py migrate
```

4. 創建座位數據
```
python manage.py create_seats
```

5. 啟動開發服務器
```
python manage.py runserver
```

6. 訪問 http://127.0.0.1:8000/ 開始使用系統
