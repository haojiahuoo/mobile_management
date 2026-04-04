# inventory/models/stock.py
from django.db import models
from django.core.exceptions import ValidationError
from .core import Product
from .party import Store, Supplier
from .base import BaseModel


class Stock(models.Model):
    """库存表"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock_info', verbose_name="商品")
    quantity = models.IntegerField(default=0, verbose_name="当前库存")
    min_quantity = models.IntegerField(default=10, verbose_name="最低库存预警")
    max_quantity = models.IntegerField(default=1000, verbose_name="最高库存预警")
    last_inbound_date = models.DateField(null=True, blank=True, verbose_name="最后入库日期")
    last_outbound_date = models.DateField(null=True, blank=True, verbose_name="最后出库日期")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'inventory_stock'
        verbose_name = "库存"
        verbose_name_plural = "库存列表"
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
    def is_low_stock(self):
        """是否低库存"""
        return self.quantity <= self.min_quantity
    
    def is_high_stock(self):
        """是否高库存"""
        return self.quantity >= self.max_quantity
    
    def update_quantity(self, delta, remark=""):
        """更新库存数量"""
        new_quantity = self.quantity + delta
        if new_quantity < 0:
            raise ValidationError(f"库存不足！当前库存: {self.quantity}")
        self.quantity = new_quantity
        self.save()
        return new_quantity


class StockRecord(models.Model):
    """库存流水记录"""
    RECORD_TYPE = (
        ('inbound', '入库'),
        ('outbound', '出库'),
        ('transfer_in', '调拨入库'),
        ('transfer_out', '调拨出库'),
        ('adjust', '盘点调整'),
        ('return', '退货'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_records', verbose_name="商品")
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE, verbose_name="记录类型")
    quantity = models.IntegerField(verbose_name="数量")
    before_quantity = models.IntegerField(verbose_name="变动前数量")
    after_quantity = models.IntegerField(verbose_name="变动后数量")
    reference_no = models.CharField(max_length=100, null=True, blank=True, verbose_name="关联单号")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="操作人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'inventory_stock_record'
        verbose_name = "库存流水"
        verbose_name_plural = "库存流水记录"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_record_type_display()} {self.quantity}"


class StockCheck(models.Model):
    """库存盘点"""
    check_no = models.CharField(max_length=50, unique=True, verbose_name="盘点单号")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name="盘点门店")
    check_date = models.DateField(auto_now_add=True, verbose_name="盘点日期")
    status = models.CharField(max_length=20, default='draft', verbose_name="状态")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="盘点人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'inventory_stock_check'
        verbose_name = "库存盘点"
        verbose_name_plural = "库存盘点列表"
        ordering = ['-check_date']
    
    def __str__(self):
        return f"{self.check_no} - {self.store.name}"


class StockCheckItem(models.Model):
    """库存盘点明细"""
    stock_check = models.ForeignKey(StockCheck, on_delete=models.CASCADE, related_name='items', verbose_name="盘点单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    system_quantity = models.IntegerField(verbose_name="系统库存")
    actual_quantity = models.IntegerField(verbose_name="实际库存")
    difference = models.IntegerField(default=0, verbose_name="差异数量")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    
    class Meta:
        db_table = 'inventory_stock_check_item'
        verbose_name = "库存盘点明细"
        verbose_name_plural = "库存盘点明细列表"
    
    def save(self, *args, **kwargs):
        self.difference = self.actual_quantity - self.system_quantity
        super().save(*args, **kwargs)


class StockTransfer(models.Model):
    """库存调拨"""
    transfer_no = models.CharField(max_length=50, unique=True, verbose_name="调拨单号")
    from_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='transfer_out', verbose_name="调出门店")
    to_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='transfer_in', verbose_name="调入门店")
    transfer_date = models.DateField(auto_now_add=True, verbose_name="调拨日期")
    status = models.CharField(max_length=20, default='pending', verbose_name="状态")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'inventory_stock_transfer'
        verbose_name = "库存调拨"
        verbose_name_plural = "库存调拨列表"
        ordering = ['-transfer_date']
    
    def __str__(self):
        return f"{self.transfer_no} - {self.from_store.name} → {self.to_store.name}"


class StockTransferItem(models.Model):
    """库存调拨明细"""
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items', verbose_name="调拨单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="调拨数量")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    
    class Meta:
        db_table = 'inventory_stock_transfer_item'
        verbose_name = "库存调拨明细"
        verbose_name_plural = "库存调拨明细列表"