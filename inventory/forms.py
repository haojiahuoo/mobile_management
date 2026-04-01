# E:\Git_code\mobile_management\inventory\forms.py

from django import forms
from .models.core import Stock, StockCategory


class StockForm(forms.ModelForm):
    """库存表单"""
    
    class Meta:
        model = Stock
        fields = '__all__'
        widgets = {
            'remark': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
            'specification': forms.TextInput(attrs={'placeholder': '例如: 红色, 128GB'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_quantity = cleaned_data.get('min_quantity', 0)
        max_quantity = cleaned_data.get('max_quantity', 0)
        quantity = cleaned_data.get('quantity', 0)
        cost_price = cleaned_data.get('cost_price', 0)
        sell_price = cleaned_data.get('sell_price', 0)
        
        # 检查预警值
        if min_quantity > 0 and max_quantity > 0:
            if min_quantity >= max_quantity:
                raise forms.ValidationError('最低预警值必须小于最高预警值')
        
        # 检查售价
        if sell_price and cost_price and sell_price < cost_price:
            raise forms.ValidationError({'sell_price': '售价不能低于成本价'})
        
        # 检查库存数量
        if quantity < 0:
            raise forms.ValidationError({'quantity': '库存数量不能为负数'})
        
        return cleaned_data


class StockCategoryForm(forms.ModelForm):
    """库存分类表单"""
    
    class Meta:
        model = StockCategory
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        obj_id = self.instance.id if self.instance else None
        
        # 检查循环引用
        if parent and parent.id == obj_id:
            raise forms.ValidationError({'parent': '不能将自身设为上级分类'})
        
        # 检查层级深度
        if parent:
            if parent.level >= 5:
                raise forms.ValidationError({'parent': '分类层级不能超过5级'})
        
        return cleaned_data


class StockInboundForm(forms.Form):
    """入库表单"""
    quantity = forms.IntegerField(
        label='入库数量',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'vTextField', 'style': 'width: 200px;'})
    )
    remark = forms.CharField(
        label='备注',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'vTextField'})
    )


class StockOutboundForm(forms.Form):
    """出库表单"""
    quantity = forms.IntegerField(
        label='出库数量',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'vTextField', 'style': 'width: 200px;'})
    )
    remark = forms.CharField(
        label='备注',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'vTextField'})
    )
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        # 这里可以在视图中验证库存是否充足
        return quantity


class BatchStockOperationForm(forms.Form):
    """批量库存操作表单"""
    stock_ids = forms.MultipleChoiceField(
        label='选择库存',
        widget=forms.SelectMultiple(attrs={'size': 10, 'class': 'vTextField'})
    )
    quantity = forms.IntegerField(
        label='操作数量',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'vTextField', 'style': 'width: 200px;'})
    )
    remark = forms.CharField(
        label='备注',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'vTextField'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models.core import Stock
        stocks = Stock.objects.filter(is_active=True)
        self.fields['stock_ids'].choices = [(s.id, f'{s.code} - {s.name}') for s in stocks]