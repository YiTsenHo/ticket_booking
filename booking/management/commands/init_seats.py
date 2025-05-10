from django.core.management.base import BaseCommand
from django.db import connection, transaction
from booking.models import Seat

class Command(BaseCommand):
    help = '初始化劇院座位'

    def handle(self, *args, **options):
        # 使用更強力的方法清除所有現有座位
        with transaction.atomic():
            # 完全清除所有座位
            Seat.objects.all().delete()
            
            # 重置 SQLite 自增 ID (如果使用 SQLite)
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='booking_seat'")
        
            self.stdout.write("已徹底清除所有現有座位")
            
            # 定義座位配置 - 完全符合指定的座位布局
            seating_chart = [
                ["A1", "A2", "A3", "stair", "A4", "A5", "A6", "A7", "A8", "A9", "stair", "A10", "A11", "A12", "A13", "A14", "A15", "stair", "A16", "A17", "A18", "A19"],
                ["B1", "B2", "B3", "stair", "B4", "B5", "B6", "B7", "B8", "B9", "stair", "B10", "B11", "B12", "B13", "B14", "B15", "stair", "B16", "B17", "B18", "B19"],
                ["C1", "C2", "C3", "stair", "C4", "C5", "C6", "C7", "C8", "C9", "stair", "C10", "C11", "C12", "C13", "C14", "C15", "stair", "C16", "C17", "C18", "C19"],
                ["empty", "empty", "empty", "stair", "D4", "D5", "D6", "D7", "D8", "D9", "stair", "D10", "D11", "D12", "D13", "D14", "D15", "stair", "empty", "empty", "empty", "empty"],
                ["empty", "empty", "empty", "stair", "E4", "E5", "E6", "E7", "E8", "E9", "stair", "E10", "E11", "E12", "E13", "E14", "E15", "stair", "empty", "empty", "empty", "empty"]
            ]
            
            # 場次列表
            dates = ['5/22', '5/23', '5/24']
            
            # 批量創建所有座位
            seats_to_create = []
            row_mapping = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
            
            for date in dates:
                self.stdout.write(f"準備 {date} 場次的座位...")
                
                for row_index, row in enumerate(seating_chart):
                    row_letter = chr(65 + row_index)  # A, B, C, D, E
                    row_number = row_mapping[row_letter]
                    
                    for col_index, seat_label in enumerate(row):
                        # 跳過走道和空位置
                        if seat_label == "stair" or seat_label == "empty":
                            continue
                            
                        # 從座位標籤中提取列號
                        col_number = int(''.join(filter(str.isdigit, seat_label)))
                        
                        # 創建座位
                        seats_to_create.append(
                            Seat(
                                seat_number=seat_label,   # 完整座位號 (例如 "A1")
                                row_number=row_number,    # 排號 (1-5)
                                column_number=col_number, # 列號 (根據座位標籤中的數字)
                                is_reserved=False,
                                date=date
                            )
                        )
            
            # 批量創建，提高效能
            Seat.objects.bulk_create(seats_to_create)
            seats_created = len(seats_to_create)
            
            # 詳細驗證創建的座位
            self.stdout.write(self.style.SUCCESS(f'成功創建 {seats_created} 個座位 (分為 {len(dates)} 個場次)'))
            
            # 檢查每個場次的座位數量，並確保它們被正確創建
            for date in dates:
                total_seats = Seat.objects.filter(date=date).count()
                self.stdout.write(f"{date} 場次座位數量: {total_seats}")
                
                # 檢查每排座位的情況
                for row_letter in ['A', 'B', 'C', 'D', 'E']:
                    row_seats = Seat.objects.filter(date=date, seat_number__startswith=row_letter)
                    seat_numbers = [seat.seat_number for seat in row_seats]
                    self.stdout.write(f"  {row_letter}排: {row_seats.count()}個座位 - {', '.join(sorted(seat_numbers))}")
