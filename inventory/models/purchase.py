# inventory/models/purchase.py
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from .core import Product
from .party import Supplier
from .finance import Account


class PurchaseOrder(models.Model):
    """采购订单"""
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('confirmed', '已确认'),
        ('delivered', '已发货'),
        ('received', '已收货'),
        ('cancelled', '已取消'),
    )
    
    order_no = models.CharField(max_length=50, unique=True, verbose_name="订单编号")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="供应商")
    order_date = models.DateField(auto_now_add=True, verbose_name="下单日期")
    expected_date = models.DateField(null=True, blank=True, verbose_name="预计到货日期")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="订单状态")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="订单总额")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="已付金额")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="付款账户")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'inventory_purchase_order'
        verbose_name = "采购订单"
        verbose_name_plural = "采购订单列表"
        ordering = ['-order_date', '-id']
    
    def __str__(self):
        return f"{self.order_no} - {self.supplier.name}"
    
    def update_total_amount(self):
        """更新订单总额"""
        total = self.items.aggregate(total=Sum('subtotal'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class PurchaseOrderItem(models.Model):
    """采购订单明细"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items', verbose_name="采购订单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="采购数量")
    received_quantity = models.IntegerField(default=0, verbose_name="已收货数量")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="采购单价")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="小计金额")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    
    class Meta:
        db_table = 'inventory_purchase_order_item'
        verbose_name = "采购订单明细"
        verbose_name_plural = "采购订单明细列表"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.purchase_order.update_total_amount()
    
    def __str__(self):
        return f"{self.purchase_order.order_no} - {self.product.name}"


class PurchaseReceipt(models.Model):
    """采购入库单"""
    receipt_no = models.CharField(max_length=50, unique=True, verbose_name="入库单号")
    purchase_order = models.ForeignKey(
        'PurchaseOrder', 
        on_delete=models.SET_NULL,  # 改为 SET_NULL
        null=True, blank=True,  # 允许为空
        related_name='receipts', 
        verbose_name="采购订单"
    )
    receipt_date = models.DateField(auto_now_add=True, verbose_name="入库日期")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="入库总额")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="入库人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    is_stock_updated = models.BooleanField(default=False, verbose_name="库存是否已更新")
    
    class Meta:
        db_table = 'inventory_purchase_receipt'
        verbose_name = "采购入库单"
        verbose_name_plural = "采购入库单列表"
        ordering = ['-receipt_date', '-id']
    
    def __str__(self):
        # 修复：当 purchase_order 为 None 时，不访问 supplier
        if self.purchase_order:
            return f"{self.receipt_no} - {self.purchase_order.supplier.name}"
        return f"{self.receipt_no} - 无关联订单"
    
    def update_total_amount(self):
        """更新入库单总额"""
        total = self.items.aggregate(total=Sum('subtotal'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])
    
    def update_stock(self):
        """更新商品库存"""
        from .stock import Stock, StockRecord
        
        for item in self.items.all():
            product = item.product
            if not product:
                continue
            
            # 获取或创建库存记录
            stock, created = Stock.objects.get_or_create(
                product=product,
                defaults={
                    'quantity': 0,
                    'min_quantity': 10,
                    'max_quantity': 1000
                }
            )
            
            # 记录入库前的数量
            before_quantity = stock.quantity
            
            # 更新库存
            stock.quantity += item.quantity
            stock.last_inbound_date = self.receipt_date
            stock.save()
            
            # 记录库存流水
            StockRecord.objects.create(
                product=product,
                record_type='inbound',
                quantity=item.quantity,
                before_quantity=before_quantity,
                after_quantity=stock.quantity,
                reference_no=self.receipt_no,
                remark=f"采购入库单: {self.receipt_no}",
                created_by=self.created_by
            )
            
            # 更新商品主表中的库存
            product.stock = stock.quantity
            product.save(update_fields=['stock'])


class PurchaseReceiptItem(models.Model):
    """采购入库单明细"""
    receipt = models.ForeignKey(PurchaseReceipt, on_delete=models.CASCADE, related_name='items', verbose_name="入库单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="入库数量")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="入库单价")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="小计金额")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    
    class Meta:
        db_table = 'inventory_purchase_receipt_item'
        verbose_name = "采购入库单明细"
        verbose_name_plural = "采购入库单明细列表"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.receipt.update_total_amount()
    
    def __str__(self):
        return f"{self.receipt.receipt_no} - {self.product.name}"


# inventory/models/purchase.py

class PurchaseReturn(models.Model):
    """采购退货单"""
    return_no = models.CharField(max_length=50, unique=True, verbose_name="退货单号")
    purchase_order = models.ForeignKey(
        'PurchaseOrder', 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="采购订单"
    )
    purchase_receipt = models.ForeignKey(
        'PurchaseReceipt',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="入库单号"
    )
    return_date = models.DateField(auto_now_add=True, verbose_name="退货日期")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="退货总额")
    reason = models.TextField(null=True, blank=True, verbose_name="退货原因")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="退货人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    _stock_updated = models.BooleanField(default=False, editable=False)  # 添加这个字段
    
    class Meta:
        db_table = 'inventory_purchase_return'
        verbose_name = "采购退货单"
        verbose_name_plural = "采购退货单列表"
        ordering = ['-return_date']
    
    # ... 其他方法 ...
    
    def __str__(self):
        if self.purchase_order:
            return f"{self.return_no} - {self.purchase_order.supplier.name}"
        return f"{self.return_no} - 无关联订单"
    
    def update_total_amount(self):
        """更新退货单总额"""
        total = self.items.aggregate(total=models.Sum('subtotal'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])
    
    def update_stock(self):
        """退货时扣减库存"""
        from .stock import Stock, StockRecord
        
        for item in self.items.all():
            product = item.product
            
            try:
                stock = Stock.objects.get(product=product)
            except Stock.DoesNotExist:
                continue
            
            before_quantity = stock.quantity
            stock.quantity -= item.quantity
            if stock.quantity < 0:
                stock.quantity = 0
            stock.save()
            
            StockRecord.objects.create(
                product=product,
                record_type='return',
                quantity=item.quantity,
                before_quantity=before_quantity,
                after_quantity=stock.quantity,
                reference_no=self.return_no,
                remark=f"采购退货单: {self.return_no}",
                created_by=self.created_by
            )
            
            product.stock = stock.quantity
            product.save(update_fields=['stock'])


class PurchaseReturnItem(models.Model):
    """采购退货单明细"""
    return_order = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='items', verbose_name="退货单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="退货数量")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="退货单价")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="小计金额")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    
    class Meta:
        db_table = 'inventory_purchase_return_item'
        verbose_name = "采购退货单明细"
        verbose_name_plural = "采购退货单明细列表"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        if self.return_order:
            self.return_order.update_total_amount()
    
    def __str__(self):
        return f"{self.return_order.return_no} - {self.product.name}"


