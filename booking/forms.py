from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import escape
import json
from .models import Seat
import re

class PreBookingForm(forms.Form):
    reserver_name = forms.CharField(max_length=100, required=True)
    department = forms.CharField(max_length=100, required=True)
    date = forms.CharField(max_length=10, required=True)
    ticket_count = forms.IntegerField(min_value=1, max_value=5, initial=1, required=True)

class BookingForm(forms.ModelForm):
    date = forms.ChoiceField(
        choices=[
            ('5/22', '5月22日'),
            ('5/23', '5月23日'),
            ('5/24', '5月24日'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    selected_seats = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        selected_seats = json.loads(cleaned_data.get('selected_seats', '[]'))
        ticket_count = self.initial.get('ticket_count', 0)
        
        if len(selected_seats) != ticket_count:
            raise ValidationError(f'請選擇 {ticket_count} 個座位')
        
        return cleaned_data

    def clean_selected_seats(self):
        selected_seats = json.loads(self.cleaned_data.get('selected_seats', '[]'))
        ticket_count = self.initial.get('ticket_count', 0)
        
        if len(selected_seats) == 0:
            raise ValidationError('請至少選擇一個座位')
        
        if len(selected_seats) != ticket_count:
            raise ValidationError(f'請選擇 {ticket_count} 個座位（目前選擇了 {len(selected_seats)} 個）')
        
        return self.cleaned_data['selected_seats']

    # 增強數據驗證
    def clean_reserver_name(self):
        name = self.cleaned_data.get('reserver_name')
        if not name:
            raise ValidationError('姓名不能為空')
            
        # 清除雙重空格和前後空格
        name = re.sub(r'\s+', ' ', name).strip()
        
        # 清理特殊字符防止 XSS
        name = escape(name)
        
        # 驗證內容
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z\s]{2,50}$', name):
            raise ValidationError('姓名只能包含中文、英文字母和空格，長度在2-50個字符之間')

        # 檢查危險字符
        dangerous_patterns = [';', '&&', '||', '..', '/', '\\', '%']
        for pattern in dangerous_patterns:
            if pattern in name:
                raise ValidationError('姓名包含無效字符')
                
        return name

    def clean_department(self):
        # 同樣進行清理和驗證
        department = self.cleaned_data.get('department')
        if not department:
            raise ValidationError('系級不能為空')
            
        department = re.sub(r'\s+', ' ', department).strip()
        department = escape(department)
        
        if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5\s\(\)]{2,100}$', department):
            raise ValidationError('系級含無效字元')
            
        return department

    class Meta:
        model = Seat
        fields = ['reserver_name', 'department', 'date']  # 移除 'email' 欄位
        widgets = {
            'reserver_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入姓名',
                'required': True
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入系級',
                'required': True
            }),
        }