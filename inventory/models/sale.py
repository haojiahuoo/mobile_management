# inventory/models/sale.py
from django.db import models
from django.db.models import Sum
from .core import Product
from .party import Supplier, Store, Staff 
from .finance import Account
from decimal import Decimal


class SaleOrder(models.Model):
    """销售订单"""
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('confirmed', '已确认'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    
    order_no = models.CharField(max_length=50, unique=True, verbose_name="订单编号")
    customer = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="客户", limit_choices_to={'type__in': ['customer', 'both']})
    store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name="销售门店")
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="销售人员")
    order_date = models.DateField(auto_now_add=True, verbose_name="下单日期")
    expected_date = models.DateField(null=True, blank=True, verbose_name="预计发货日期")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="订单状态")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="订单总额")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="已付金额")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="收款账户")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'inventory_sale_order'
        verbose_name = "销售订单"
        verbose_name_plural = "销售订单列表"
        ordering = ['-order_date', '-id']
    
    def __str__(self):
        return f"{self.order_no} - {self.customer.name}"
    
    def update_total_amount(self):
        total = self.items.aggregate(total=Sum('subtotal'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class SaleOrderItem(models.Model):
    """销售订单明细"""
    sale_order = models.ForeignKey(SaleOrder, on_delete=models.CASCADE, related_name='items', verbose_name="销售订单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="销售数量")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="销售单价")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="小计金额")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    
    class Meta:
        db_table = 'inventory_sale_order_item'
        verbose_name = "销售订单明细"
        verbose_name_plural = "销售订单明细列表"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.sale_order.update_total_amount()
    
    def __str__(self):
        return f"{self.sale_order.order_no} - {self.product.name}"


class SaleDelivery(models.Model):
    """销售出库单"""
    delivery_no = models.CharField(max_length=50, unique=True, verbose_name="出库单号")
    sale_order = models.ForeignKey(SaleOrder, on_delete=models.CASCADE, related_name='deliveries', verbose_name="销售订单")
    delivery_date = models.DateField(auto_now_add=True, verbose_name="出库日期")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="出库总额")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="出库人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    
    class Meta:
        db_table = 'inventory_sale_delivery'
        verbose_name = "销售出库单"
        verbose_name_plural = "销售出库单列表"
        ordering = ['-delivery_date', '-id']
    
    def __str__(self):
        if self.sale_order:
            return f"{self.delivery_no} - {self.sale_order.customer.name}"
        return f"{self.delivery_no} - 无关联订单"
    
    def update_total_amount(self):
        total = self.items.aggregate(total=Sum('subtotal'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class SaleDeliveryItem(models.Model):
    """销售出库单明细"""
    delivery = models.ForeignKey(SaleDelivery, on_delete=models.CASCADE, related_name='items', verbose_name="出库单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="出库数量")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="出库单价")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="小计金额")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    
    class Meta:
        db_table = 'inventory_sale_delivery_item'
        verbose_name = "销售出库单明细"
        verbose_name_plural = "销售出库单明细列表"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.delivery.update_total_amount()
    
    def __str__(self):
        return f"{self.delivery.delivery_no} - {self.product.name}"


class SaleReturn(models.Model):
    """销售退货单"""
    return_no = models.CharField(max_length=50, unique=True, verbose_name="退货单号")
    sale_order = models.ForeignKey(SaleOrder, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="销售订单")
    sale_delivery = models.ForeignKey(SaleDelivery, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="出库单号")
    return_date = models.DateField(auto_now_add=True, verbose_name="退货日期")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="退货总额")
    reason = models.TextField(null=True, blank=True, verbose_name="退货原因")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_by = models.CharField(max_length=100, null=True, blank=True, verbose_name="退货人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    _stock_updated = models.BooleanField(default=False, editable=False)
    
    class Meta:
        db_table = 'inventory_sale_return'
        verbose_name = "销售退货单"
        verbose_name_plural = "销售退货单列表"
        ordering = ['-return_date']
    
    def __str__(self):
        if self.sale_order:
            return f"{self.return_no} - {self.sale_order.customer.name}"
        return f"{self.return_no} - 无关联订单"
    
    def update_total_amount(self):
        total = self.items.aggregate(total=Sum('subtotal'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])
    
    def update_stock(self):
        """退货时增加库存"""
        from .stock import Stock, StockRecord
        
        for item in self.items.all():
            product = item.product
            
            stock, created = Stock.objects.get_or_create(
                product=product,
                defaults={'quantity': 0, 'min_quantity': 10, 'max_quantity': 1000}
            )
            
            before_quantity = stock.quantity
            stock.quantity += item.quantity
            stock.save()
            
            StockRecord.objects.create(
                product=product,
                record_type='sale_return',
                quantity=item.quantity,
                before_quantity=before_quantity,
                after_quantity=stock.quantity,
                reference_no=self.return_no,
                remark=f"销售退货单: {self.return_no}",
                created_by=self.created_by
            )
            
            product.stock = stock.quantity
            product.save(update_fields=['stock'])


class SaleReturnItem(models.Model):
    """销售退货单明细"""
    return_order = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items', verbose_name="退货单")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="退货数量")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="退货单价")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="小计金额")
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    
    class Meta:
        db_table = 'inventory_sale_return_item'
        verbose_name = "销售退货单明细"
        verbose_name_plural = "销售退货单明细列表"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.return_order.update_total_amount()
    
    def __str__(self):
        return f"{self.return_order.return_no} - {self.product.name}"