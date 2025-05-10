from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.db.models import Count, Q
from django.template.response import TemplateResponse
from django.urls import path
import json
from .models import Seat

# 修改 admin 站點標題
admin.site.site_header = '方形海演出訂票系統管理後台'
admin.site.site_title = '訂票系統管理'
admin.site.index_title = '管理功能'
admin.site.site_footer = '© 2025 方形海'

class DateFilter(admin.SimpleListFilter):
    title = '演出場次'
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return [
            ('5/22', '5月22日'),
            ('5/23', '5月23日'),
            ('5/24', '5月24日'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(date=self.value())
        return queryset

class RowFilter(admin.SimpleListFilter):
    title = '座位排數'
    parameter_name = 'row_letter'

    def lookups(self, request, model_admin):
        return [
            ('A', 'A排'),
            ('B', 'B排'),
            ('C', 'C排'),
            ('D', 'D排'),
            ('E', 'E排'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(seat_number__startswith=self.value())
        return queryset

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['seat_info', 'status_tag', 'booking_info', 'show_date']
    list_filter = [DateFilter, RowFilter, 'is_reserved']  # 保留基本篩選
    search_fields = ['seat_number', 'reserver_name', 'department', 'email']
    ordering = ['date', 'row_number', 'column_number']
    list_per_page = 50
    readonly_fields = ['created_at', 'updated_at']
    change_list_template = 'admin/booking/seat/change_list.html'
    
    def seat_info(self, obj):
        seat_class = 'occupied' if obj.is_reserved else 'available'
        return format_html(
            '<div class="seat-info"><span class="seat-tag {}">{}</span> <span class="seat-position">{}排{}號</span></div>',
            seat_class, obj.seat_number, obj.row_number, obj.column_number
        )
    seat_info.short_description = '座位'
    seat_info.admin_order_field = 'seat_number'

    def status_tag(self, obj):
        if obj.is_reserved:
            return format_html('<span class="status-tag reserved">已預訂</span>')
        return format_html('<span class="status-tag available">可預訂</span>')
    status_tag.short_description = '狀態'
    status_tag.admin_order_field = 'is_reserved'

    def booking_info(self, obj):
        if obj.is_reserved:
            return format_html('<strong>{}</strong> <span class="dept-tag">{}</span>', 
                             obj.reserver_name or '-', obj.department or '-')
        return '-'
    booking_info.short_description = '預訂資訊'

    def show_date(self, obj):
        dates = {
            '5/22': '5月22日',
            '5/23': '5月23日',
            '5/24': '5月24日'
        }
        return format_html('<span class="date-tag">{}</span>', dates.get(obj.date, obj.date))
    show_date.short_description = '演出場次'
    show_date.admin_order_field = 'date'

    fieldsets = (
        ('座位資訊', {
            'fields': ('seat_number', 'row_number', 'column_number', 'date'),
            'classes': ('wide', 'extrapretty',),
        }),
        ('預訂狀態', {
            'fields': ('is_reserved', 'reserver_name', 'department', 'email'),
            'classes': ('wide',),
        }),
        ('時間資訊', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display_links = ['seat_info']
    actions = ['clear_reservations', 'export_to_csv', 'export_to_excel']

    def clear_reservations(self, request, queryset):
        if 'apply' in request.POST:
            updated = queryset.update(
                is_reserved=False,
                reserver_name=None,
                department=None,
                email=None
            )
            self.message_user(request, f'成功清除 {updated} 個座位的預訂', messages.SUCCESS)
            return None
        
        # 顯示確認頁面
        context = {
            'title': '確認清除座位預訂',
            'queryset': queryset,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
            'opts': self.model._meta,
            'seats_count': queryset.count(),
            'reserved_count': queryset.filter(is_reserved=True).count(),
        }
        return TemplateResponse(request, 'admin/booking/seat/clear_reservations_confirmation.html', context)
    clear_reservations.short_description = '清除所選座位的預訂'

    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from datetime import datetime

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="seats_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['場次', '座位號', '排', '列', '預訂狀態', '預訂人', '系級', '電子郵件', '預訂時間'])
        
        for seat in queryset:
            writer.writerow([
                seat.date,
                seat.seat_number,
                seat.row_number,
                seat.column_number,
                '已預訂' if seat.is_reserved else '未預訂',
                seat.reserver_name or '',
                seat.department or '',
                seat.email or '',
                seat.created_at.strftime("%Y-%m-%d %H:%M:%S") if seat.is_reserved else ''
            ])
        
        self.message_user(request, f'已匯出 {queryset.count()} 個座位的資料', messages.SUCCESS)
        return response
    export_to_csv.short_description = '匯出所選座位資料(CSV)'

    def export_to_excel(self, request, queryset):
        try:
            # 嘗試導入 xlwt
            try:
                import xlwt
            except ImportError:
                self.message_user(request, 'Excel匯出需要安裝xlwt套件: pip install xlwt', messages.ERROR)
                return None

            from django.http import HttpResponse
            from datetime import datetime

            response = HttpResponse(content_type='application/ms-excel')
            response['Content-Disposition'] = f'attachment; filename="seats_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls"'
            
            wb = xlwt.Workbook(encoding='utf-8')
            ws = wb.add_sheet('座位資料')
            
            # 設定樣式
            font_style = xlwt.XFStyle()
            font_style.font.bold = True
            
            # 寫入標題行
            columns = ['場次', '座位號', '排', '列', '預訂狀態', '預訂人', '系級', '電子郵件', '預訂時間']
            for col_num, column_title in enumerate(columns):
                ws.write(0, col_num, column_title, font_style)
            
            # 寫入數據行
            font_style = xlwt.XFStyle()
            rows = queryset.values_list('date', 'seat_number', 'row_number', 'column_number', 
                                        'is_reserved', 'reserver_name', 'department', 'email', 'created_at')
            for row_num, row in enumerate(rows, 1):
                for col_num, cell_value in enumerate(row):
                    if col_num == 4:  # is_reserved 欄位
                        ws.write(row_num, col_num, '已預訂' if cell_value else '未預訂', font_style)
                    elif col_num == 8:  # created_at 欄位
                        if cell_value and row[4]:  # 如果有日期且已預訂
                            ws.write(row_num, col_num, cell_value.strftime("%Y-%m-%d %H:%M:%S"), font_style)
                        else:
                            ws.write(row_num, col_num, '', font_style)
                    else:
                        ws.write(row_num, col_num, cell_value if cell_value else '', font_style)
            
            wb.save(response)
            self.message_user(request, f'已匯出 {queryset.count()} 個座位的資料至Excel', messages.SUCCESS)
            return response
        except Exception as e:
            self.message_user(request, f'匯出失敗: {str(e)}', messages.ERROR)
            return None
    export_to_excel.short_description = '匯出所選座位資料(Excel)'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('stats/', self.admin_site.admin_view(self.reservation_stats_view), name='seat-reservation-stats'),
        ]
        return custom_urls + urls
    
    def reservation_stats_view(self, request):
        # 準備統計數據 - 確保正確計算
        total_seats = Seat.objects.count()
        total_reserved = Seat.objects.filter(is_reserved=True).count()
        
        # 安全計算百分比，避免除以零錯誤
        reserved_percentage = round((total_reserved / total_seats) * 100, 1) if total_seats > 0 else 0
        
        # 按日期統計 - 使用正確的 Django ORM
        stats_by_date = []
        for date in ['5/22', '5/23', '5/24']:
            date_seats = Seat.objects.filter(date=date)
            total = date_seats.count()
            reserved = date_seats.filter(is_reserved=True).count()
            
            # 計算可用座位數和預訂百分比
            available = total - reserved
            reserved_percentage = round((reserved / total) * 100, 1) if total > 0 else 0
            
            stats_by_date.append({
                'date': date,
                'total': total,
                'reserved': reserved,
                'available': available,
                'reserved_percentage': reserved_percentage
            })
        
        # 按排統計 - 確保每個統計項正確關聯日期
        stats_by_row = []
        for row_letter in ['A', 'B', 'C', 'D', 'E']:
            for date in ['5/22', '5/23', '5/24']:
                seats_in_row = Seat.objects.filter(seat_number__startswith=row_letter, date=date)
                total = seats_in_row.count()
                reserved = seats_in_row.filter(is_reserved=True).count()
                
                # 確保總座位數不為零時才計算百分比
                if total > 0:
                    reserved_percentage = round((reserved / total) * 100, 1)
                else:
                    reserved_percentage = 0
                    
                stats_by_row.append({
                    'row': row_letter,
                    'date': date,
                    'total': total,
                    'reserved': reserved,
                    'available': total - reserved,
                    'reserved_percentage': reserved_percentage,
                    'id': f"{date}-{row_letter}" # 添加唯一ID用於CSS選擇器
                })
        
        context = dict(
            self.admin_site.each_context(request),
            title='座位預訂統計',
            total_seats=total_seats,
            total_reserved=total_reserved,
            reserved_percentage=reserved_percentage,
            stats_by_date=stats_by_date,
            stats_by_row=stats_by_row,
        )
        return TemplateResponse(request, 'admin/booking/seat/stats.html', context)
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def changelist_view(self, request, extra_context=None):
        # 確保完全移除快速篩選，不添加任何額外的內容到 extra_context
        return super().changelist_view(request, None)
    
    class Media:
        css = {
            'all': ('css/admin-custom.css',)
        }
        js = ('js/admin-custom.js',)
