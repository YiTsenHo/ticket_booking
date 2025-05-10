# 方形海演出訂票系統 PythonAnywhere 部署指南

本指南將幫助您將座位預訂系統成功部署到 PythonAnywhere 平台，即使沒有 Git 儲存庫也能完成部署。

## 目錄
1. [前置準備](#前置準備)
2. [上傳代碼](#上傳代碼)
3. [設置環境](#設置環境)
4. [配置 Web 應用](#配置-web-應用)
5. [初始化數據](#初始化數據)
6. [常見問題排解](#常見問題排解)

## 前置準備

1. 在 [PythonAnywhere](https://www.pythonanywhere.com/) 註冊一個免費帳戶
2. 整理您的本地代碼（確保沒有不必要的文件如 `.pyc` 等）
3. 確保 `settings.py` 中的 `ALLOWED_HOSTS` 已包含 `yourusername.pythonanywhere.com`

## 上傳代碼

在 PythonAnywhere 上創建目錄並上傳您的代碼：

### 步驟 1: 建立專案目錄
登入 PythonAnywhere 後，開啟 Bash console：
```bash
mkdir -p ~/seatbooking
```

### 步驟 2: 上傳代碼（選擇一種方法）

#### 方法 A: 直接上傳關鍵文件
1. 在 PythonAnywhere 的 "Files" 頁面創建必要的目錄結構
2. 上傳以下重要文件：
   - `manage.py` → `~/seatbooking/`
   - `my_test_project/` 目錄下的所有 Python 文件
   - `booking/` 目錄及其內容

#### 方法 B: 使用 tar 命令（推薦）
1. 在本地壓縮您的項目：
   ```bash
   # 在本地執行
   cd 專案目錄
   tar -czf seatbooking.tar.gz .
   ```
2. 在 PythonAnywhere Files 頁面上傳 `seatbooking.tar.gz`
3. 在 PythonAnywhere Bash console 中解壓：
   ```bash
   cd ~/seatbooking
   tar -xzf ../seatbooking.tar.gz
   ```

## 設置環境

### 步驟 1: 創建並激活虛擬環境
```bash
mkvirtualenv --python=python3.11 seatbooking_env
```

當您看到 `(seatbooking_env)` 前綴時，表示虛擬環境已激活。

### 步驟 2: 安裝依賴
```bash
cd ~/seatbooking
pip install django==5.2 python-dotenv xlwt whitenoise
```

## 配置 Web 應用

### 步驟 1: 添加 Web 應用
1. 前往 PythonAnywhere 控制面板的 "Web" 頁籤
2. 點擊 "Add a new web app"
3. 選擇您的域名（如 `yourusername.pythonanywhere.com`）
4. 選擇 "Manual configuration"
5. 選擇 Python 版本 3.11

### 步驟 2: 配置 Web 應用設置

確認您的目錄結構後，適當配置路徑：

#### 如果 manage.py 位於 ~/seatbooking/my_test_project/
- **Source code**: `/home/yourusername/seatbooking/my_test_project`
- **Working directory**: `/home/yourusername/seatbooking/my_test_project`

#### 如果 manage.py 位於 ~/seatbooking/
- **Source code**: `/home/yourusername/seatbooking`
- **Working directory**: `/home/yourusername/seatbooking`

### 步驟 3: 設置虛擬環境路徑
- **Virtualenv**: `/home/yourusername/.virtualenvs/seatbooking_env`

### 步驟 4: 配置 WSGI 文件
點擊 "WSGI configuration file" 鏈接，替換內容為：

```python
import os
import sys

# 設置正確的項目路徑（包含 manage.py 的目錄）
path = '/home/yourusername/seatbooking/my_test_project'  # 調整為實際路徑
if path not in sys.path:
    sys.path.append(path)

# 調整為您的設置模組名稱（通常是 '[項目名].settings'）
os.environ['DJANGO_SETTINGS_MODULE'] = 'my_test_project.settings'
os.environ['PYTHONANYWHEREDEBUG'] = 'False'  # 標記為生產環境

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 步驟 5: 設置靜態文件
在 "Static files" 部分添加：
- **URL**: `/static/`
- **Directory**: `/home/yourusername/seatbooking/my_test_project/staticfiles`

## 初始化數據

### 步驟 1: 收集靜態文件和遷移數據庫
```bash
cd ~/seatbooking/my_test_project  # 調整為實際路徑
python manage.py migrate
python manage.py collectstatic --noinput
```

### 步驟 2: 創建超級用戶和初始化座位
```bash
python manage.py createsuperuser
python manage.py init_seats
```

### 步驟 3: 重新載入應用
在 Web 頁籤中點擊 "Reload" 按鈕。

## 常見問題排解

### 1. 400 Bad Request 錯誤
常見原因是 CSRF 設置問題：
1. 確保 `settings.py` 中添加了：
   ```python
   CSRF_TRUSTED_ORIGINS = [
       'https://yourusername.pythonanywhere.com',
       'http://yourusername.pythonanywhere.com'
   ]
   ```
2. 清除瀏覽器緩存或使用隱私模式訪問
3. 檢查所有表單是否包含 `{% csrf_token %}`

### 2. 500 Server Error
1. 在 Web 頁面中查看 "Error log"
2. 常見原因：
   - 路徑配置錯誤
   - 缺少依賴包
   - 模組導入問題（檢查 ROOT_URLCONF 和 WSGI_APPLICATION 設置）

### 3. 静态文件不显示
1. 確認已運行 `collectstatic`
2. 檢查 `STATIC_URL` 和 `STATIC_ROOT` 設置
3. 確保靜態文件路徑指向正確目錄

### 4. 目錄結構問題
如果您的目錄結構與預期不符（例如嵌套多層），可以使用符號鏈接：
```bash
# 例如，將 my_test_project 模組鏈接為 seatbooking
cd ~/seatbooking
ln -s my_test_project seatbooking
```

### 5. 模塊名稱問題
如果 `settings.py` 中的模組名（如 ROOT_URLCONF, WSGI_APPLICATION）與實際模組不符：
```bash
# 方法1: 編輯 settings.py 修改名稱
# 將 'seatbooking.urls' 改為 'my_test_project.urls'

# 方法2: 創建符號鏈接使兩者相互匹配
cd ~/seatbooking
ln -s my_test_project seatbooking
```

## 維護提示

1. **定期備份數據庫**：使用 `python manage.py dumpdata > backup.json`
2. **監控錯誤日誌**：在 Web 頁籤定期查看 Error log
3. **更新依賴**：根據需要定期更新依賴包版本

## 資源限制

請注意 PythonAnywhere 免費帳戶有以下限制：
- 網站閒置 3 個月後可能會被暫停
- CPU 和內存資源有限
- 外部網絡訪問受限

## 完成部署
成功完成上述步驟後，您應當可以通過 `yourusername.pythonanywhere.com` 訪問您的座位預訂系統。