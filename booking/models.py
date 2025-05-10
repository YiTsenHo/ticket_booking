from django.db import models
from django.utils import timezone

class Seat(models.Model):
    seat_number = models.CharField(max_length=10, verbose_name='座位號碼')  # 確保沒有唯一性約束
    row_number = models.PositiveIntegerField(verbose_name='排數')
    column_number = models.PositiveIntegerField(verbose_name='列數')
    is_reserved = models.BooleanField(default=False, verbose_name='是否已預訂')
    reserver_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='預訂者姓名')
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name='系級')
    date = models.CharField(max_length=10, blank=True, null=True, verbose_name='預訂日期')
    email = models.EmailField(blank=True, null=True, verbose_name='電子郵件')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='創建時間')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='更新時間')

    class Meta:
        verbose_name = '座位'
        verbose_name_plural = '座位'
        ordering = ['row_number', 'column_number']
        # 移除所有唯一性約束，讓我們可以重建資料庫

    def __str__(self):
        return f"{self.row_number}排{self.column_number}號 ({self.seat_number})"