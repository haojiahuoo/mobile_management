# inventory/validators.py
from django.core.exceptions import ValidationError
import re


def validate_color_hex(value):
    """验证颜色代码格式"""
    if value:
        pattern = r'^#([0-9A-Fa-f]{3}){1,2}$'
        if not re.match(pattern, value):
            raise ValidationError('颜色代码格式不正确，请使用如 #FF0000 或 #F00 的格式')
    return value