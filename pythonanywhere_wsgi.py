import os
import sys

# 添加專案路徑到系統路徑
path = '/home/yourusername/my_test_project'
if path not in sys.path:
    sys.path.append(path)

# 設置環境變量
os.environ['DJANGO_SETTINGS_MODULE'] = 'my_test_project.settings'

# 生產環境標記
os.environ['PYTHONANYWHEREDEBUG'] = 'False'

# 導入Django的WSGI應用
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
