# inventory/choices.py
from django.db import models


class ColorChoices(models.TextChoices):
    """颜色选项"""
    NONE = '', '无'
    BLACK = 'black', '黑色'
    WHITE = 'white', '白色'
    RED = 'red', '红色'
    BLUE = 'blue', '蓝色'
    GREEN = 'green', '绿色'
    YELLOW = 'yellow', '黄色'
    PURPLE = 'purple', '紫色'
    PINK = 'pink', '粉色'
    GOLD = 'gold', '金色'
    SILVER = 'silver', '银色'
    GRAY = 'gray', '灰色'
    ORANGE = 'orange', '橙色'
    BROWN = 'brown', '棕色'