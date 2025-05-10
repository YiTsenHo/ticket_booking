"""
URL configuration for seatbooking project.
"""
from django.contrib import admin
from django.urls import path
from booking.views import seat_list, book_seat, home, reset_booking
from django.conf import settings
from django.conf.urls.static import static

# Customize admin site
admin.site.site_header = "方形海訂票系統管理"
admin.site.site_title = "訂票系統管理"
admin.site.index_title = "管理功能"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('booking/', seat_list, name='seat_list'),
    path('book/<int:seat_id>/', book_seat, name='book_seat'),
    path('booking/reset/', reset_booking, name='reset_booking'),
]

# 在開發環境中添加靜態文件的URL
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
