from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction, models
from django.core.cache import cache
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.html import escape
from django.http import HttpResponseServerError
from django.conf import settings
import json
import re
from .models import Seat
from .forms import BookingForm, PreBookingForm
import logging

# 初始化日誌
logger = logging.getLogger(__name__)

def validate_reserver_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('姓名不能為空')
    
    # 清除前後空白
    name = name.strip()
    
    if not re.match(r'^[\u4e00-\u9fa5a-zA-Z\s]{2,50}$', name):
        raise ValidationError('姓名只能包含中文、英文字母和空格，長度在2-50個字符之間')
    
    # 檢查危險字符
    dangerous_patterns = [';', '&&', '||', '..', '/', '\\', '%']
    for pattern in dangerous_patterns:
        if pattern in name:
            logger.warning(f"檢測到可能的注入嘗試: {name}")
            raise ValidationError('姓名包含無效字符')
    
    return name

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def seat_list(request):
    booking_info = request.session.get('booking_info', None)
    success_message = None

    if request.method == 'POST':
        if 'step' in request.POST and request.POST['step'] == '1':
            # Create form instance with POST data
            try:
                # Extract and validate form data manually
                reserver_name = validate_reserver_name(request.POST.get('reserver_name', ''))
                department = escape(request.POST.get('department', '').strip())
                date = request.POST.get('date', '')
                ticket_count = int(request.POST.get('ticket_count', 1))
                
                # Validate ticket count
                if (ticket_count < 1 or ticket_count > 5):
                    messages.error(request, '購票張數必須在1-5張之間')
                    return redirect('seat_list')
                
                # Set session data
                request.session['booking_info'] = {
                    'reserver_name': reserver_name,
                    'department': department,
                    'date': date,
                    'ticket_count': ticket_count,
                    'token': get_random_string(32)  # Add CSRF protection token
                }
                # Explicitly save the session
                request.session.modified = True
                return redirect('seat_list')
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('seat_list')
        elif 'reset' in request.POST:
            # 返回上一步，清除session中的booking_info
            if 'booking_info' in request.session:
                del request.session['booking_info']
            return redirect('seat_list')
        else:
            if not booking_info:
                messages.error(request, '請先填寫基本資料')
                return redirect('seat_list')

            # 驗證 session token 防止重放攻擊
            if 'token' not in booking_info:
                logger.warning("缺少防偽令牌，可能的 session 劫持")
                messages.error(request, '安全驗證失敗，請重新填寫')
                if 'booking_info' in request.session:
                    del request.session['booking_info']
                return redirect('seat_list')

            try:
                # 安全處理 JSON 輸入
                try:
                    selected_seats = json.loads(request.POST.get('selected_seats', '[]'))
                    if not isinstance(selected_seats, list):
                        raise ValueError("座位數據格式無效")
                except (json.JSONDecodeError, ValueError):
                    logger.warning("JSON 解析錯誤")
                    messages.error(request, '座位數據格式無效')
                    return redirect('seat_list')
                
                ticket_count = booking_info['ticket_count']

                if len(selected_seats) != ticket_count:
                    messages.error(request, f"請選擇 {ticket_count} 個座位")
                    return redirect('seat_list')

                with transaction.atomic():
                    selected_seat_numbers = []  # 用於收集已選座位的編號
                    for seat_id in selected_seats:
                        seat = Seat.objects.select_for_update().get(id=seat_id, date=booking_info['date'])
                        if seat.is_reserved:
                            messages.error(request, f'座位 {seat.seat_number} 已被預訂')
                            return redirect('seat_list')

                        seat.is_reserved = True
                        seat.reserver_name = booking_info['reserver_name']
                        seat.department = booking_info['department']
                        seat.date = booking_info['date']
                        seat.save()
                        
                        selected_seat_numbers.append(seat.seat_number)

                # 清除 session 並記錄成功
                token = booking_info.pop('token', None)  # 移除 token 避免記錄在日誌中
                logger.info(f"成功預訂: {booking_info['reserver_name']}, 座位: {', '.join(selected_seat_numbers)}")
                del request.session['booking_info']
                success_message = f'成功預訂 {ticket_count} 個座位！'

            except Seat.DoesNotExist:
                messages.error(request, '選擇的座位不存在或不符合條件')
                return redirect('seat_list')
            except Exception as e:
                logger.error(f"預訂過程發生錯誤: {str(e)}")
                messages.error(request, '預訂過程中發生錯誤，請稍後再試')
                return redirect('seat_list')

    # 座位配置定義（A-E排，包含走道）
    seating_chart = [
        ["A1", "A2", "A3", "stair", "A4", "A5", "A6", "A7", "A8", "A9", "stair", "A10", "A11", "A12", "A13", "A14", "A15", "stair", "A16", "A17", "A18", "A19"],
        ["B1", "B2", "B3", "stair", "B4", "B5", "B6", "B7", "B8", "B9", "stair", "B10", "B11", "B12", "B13", "B14", "B15", "stair", "B16", "B17", "B18", "B19"],
        ["C1", "C2", "C3", "stair", "C4", "C5", "C6", "C7", "C8", "C9", "stair", "C10", "C11", "C12", "C13", "C14", "C15", "stair", "C16", "C17", "C18", "C19"],
        ["empty", "empty", "empty", "stair", "D4", "D5", "D6", "D7", "D8", "D9", "stair", "D10", "D11", "D12", "D13", "D14", "D15", "stair", "empty", "empty", "empty", "empty"],
        ["empty", "empty", "empty", "stair", "E4", "E5", "E6", "E7", "E8", "E9", "stair", "E10", "E11", "E12", "E13", "E14", "E15", "stair", "empty", "empty", "empty", "empty"]
    ]

    # 獲取當前選擇的日期
    selected_date = booking_info['date'] if booking_info else None
    
    # 檢查該日期的座位數量
    if selected_date:
        total_seats = Seat.objects.filter(date=selected_date).count()
        logger.debug(f"當前選擇場次 {selected_date} 的座位總數: {total_seats}")
    
    # 只獲取對應日期的座位資料
    seats = {}
    if selected_date:
        seats = {seat.seat_number: seat for seat in Seat.objects.filter(date=selected_date)}
        
        # 檢查每排座位的數量
        row_counts = {}
        for seat in Seat.objects.filter(date=selected_date):
            row_letter = seat.seat_number[0]
            if row_letter not in row_counts:
                row_counts[row_letter] = 0
            row_counts[row_letter] += 1
        logger.debug(f"各排座位數量: {row_counts}")

    # 生成座位矩陣
    seat_matrix = []
    for row in seating_chart:
        current_row = []
        for seat_label in row:
            if seat_label == "stair":
                current_row.append("stair")
            elif seat_label == "empty":
                current_row.append("empty")
            else:
                current_row.append(seats.get(seat_label, None))  # 如果座位不存在，返回 None
        seat_matrix.append(current_row)

    form = PreBookingForm() if not booking_info else None

    return render(request, 'booking/seat_list.html', {
        'form': form,
        'booking_info': booking_info,
        'seat_matrix': seat_matrix if booking_info else None,
        'success_message': success_message,
    })

@never_cache
def reset_booking(request):
    if 'booking_info' in request.session:
        del request.session['booking_info']
    return redirect('seat_list')

def book_seat(request, seat_id):
    seat = get_object_or_404(Seat, id=seat_id)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=seat)
        if form.is_valid() and not seat.is_reserved:
            booking = form.save(commit=False)
            booking.is_reserved = True
            booking.save()
            return redirect('seat_list')
    return redirect('seat_list')

def home(request):
    return render(request, 'booking/home.html')