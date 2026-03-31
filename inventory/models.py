import re
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.utils.html import format_html
# ================== 账户 ==================
class Account(models.Model):
    """账户模型"""
    name = models.CharField(max_length=100, verbose_name="账户名称")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="余额")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_account'
        verbose_name = "账户"
        verbose_name_plural = "账户信息列表"

    def __str__(self):
        return self.name

# ================== 颜色验证器 ==================
def validate_color_hex(value: str) -> None:
    """验证颜色代码格式"""
    if value and not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
        raise ValidationError('颜色代码格式不正确，应为 #RRGGBB 或 #RGB 格式')
    

# ================== 商品分类 ==================
class ProductCategory(models.Model):
    """商品分类模型（支持无限级分类）"""
    name = models.CharField(max_length=100, verbose_name="分类名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="分类编码")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name="父级分类")
    level = models.IntegerField(default=1, verbose_name="层级")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_product_category'
        verbose_name = "商品分类"
        verbose_name_plural = "商品分类列表"
        ordering = ['level', 'sort_order', 'id']

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    def get_full_code(self):
        """获取完整编码（如：0001 > 00010001）"""
        if self.parent:
            return f"{self.parent.get_full_code()}{self.code}"
        return self.code

    def get_full_name(self):
        """获取完整名称"""
        if self.parent:
            return f"{self.parent.get_full_name()} > {self.name}"
        return self.name

    @property
    def productcategory_set(self):
        """兼容性属性，避免 Django admin 报错"""
        return self.children


# ================== 商品模型 ==================
class Product(models.Model):
    """商品模型"""

    class ColorChoices(models.TextChoices):
        """颜色选项枚举类"""
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
        CUSTOM = 'custom', '其他'

    # 字段定义
    code = models.CharField(
        max_length=50, unique=True, verbose_name="商品编号",
        blank=True, null=True, db_index=True,
        help_text="商品唯一编号，不填则自动生成"
    )
    brand = models.CharField(
        max_length=100, verbose_name="商品品牌",
        blank=True, default="", db_index=True
    )
    name = models.CharField(
        max_length=100, verbose_name="商品名称", db_index=True
    )
    color = models.CharField(
        max_length=20, choices=ColorChoices.choices,
        default=ColorChoices.NONE, blank=True, verbose_name="商品颜色"
    )
    color_hex = models.CharField(
        max_length=7, blank=True, default='',
        verbose_name="颜色代码(如:#FF0000)",
        validators=[validate_color_hex]
    )
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="商品分类",
        db_index=True, related_name='products'
    )
    supplier = models.ForeignKey(
        'Supplier', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="供应商",
        db_index=True, related_name='products'
    )
    unit = models.CharField(max_length=20, default="个", verbose_name="单位")
    stock = models.IntegerField(default=0, verbose_name="库存数量", db_index=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="成本价")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="售价")
    account = models.ForeignKey(
        "Account", on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="关联账户",
        db_index=True, related_name='products'
    )
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    

    def profit_rate(self):
        if self.cost_price:
            return (self.sell_price - self.cost_price) / self.cost_price * 100
        return 0


    class Meta:
        db_table = 'inventory_product'
        verbose_name = "商品"
        verbose_name_plural = "商品信息"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['brand', 'name'], name='product_brand_name_idx'),
            models.Index(fields=['category', 'code'], name='product_category_code_idx'),
        ]

    def __str__(self):
        """返回商品的字符串表示"""
        color_part = f" [{self.get_color_display()}]" if self.color else ""
        brand_part = f"{self.brand} " if self.brand else ""
        return f"[{self.code}] {brand_part}{self.name}{color_part}"

    
    def get_color_display_value(self):
        """获取颜色显示值（用于admin显示）"""
        if self.color_hex:
            # ✅ 正确：使用 format_html 安全地生成 HTML
            return format_html(
                '<span style="display:inline-block;width:20px;height:20px;background:{};border-radius:4px;"></span> {}',
                self.color_hex,
                self.get_color_display()
            )
        return self.get_color_display()
    get_color_display_value.allow_tags = True
    get_color_display_value.short_description = '颜色'

    def _generate_code_with_category(self):
        if not self.category:
            return None
        last_product = Product.objects.filter(
            category=self.category, code__isnull=False
        ).order_by('-code').first()
        if last_product and last_product.code:
            match = re.search(r'(\d{4})$', last_product.code)
            if match:
                try:
                    last_num = int(match.group(1))
                    new_num = last_num + 1
                    return f"{self.category.get_full_code()}{new_num:04d}"
                except (ValueError, TypeError):
                    pass
        return f"{self.category.get_full_code()}0001"

    def _generate_code_global(self):
        last_product = Product.objects.filter(code__isnull=False).order_by('-id').first()
        if last_product and last_product.code:
            match = re.search(r'(\d{8})$', last_product.code)
            if match:
                try:
                    last_num = int(match.group(1))
                    new_num = last_num + 1
                    return f"{new_num:08d}"
                except (ValueError, TypeError):
                    pass
        count = Product.objects.count()
        return f"{count + 1:08d}"

    def generate_code(self):
        if self.category:
            code = self._generate_code_with_category()
            if code:
                return code
        return self._generate_code_global()

    def clean(self):
        super().clean()
        if self.sell_price is not None and self.sell_price < self.cost_price:
            raise ValidationError({'sell_price': '售价不能低于成本价'})
        if self.stock < 0:
            raise ValidationError({'stock': '库存数量不能为负数'})
        if self.color_hex and not self.color:
            raise ValidationError({'color': '选择颜色后才可以填写颜色代码'})

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        self.full_clean()
        super().save(*args, **kwargs)

    def update_stock(self, quantity: int):
        new_stock = self.stock + quantity
        if new_stock < 0:
            raise ValueError(f"库存不足，当前库存: {self.stock}，无法减少 {abs(quantity)}")
        self.stock = new_stock
        self.save(update_fields=['stock', 'updated_at'])

    def is_available(self) -> bool:
        return self.is_active and self.stock > 0

    @classmethod
    def get_active_products(cls):
        return cls.objects.filter(is_active=True)

    @classmethod
    def get_products_with_low_stock(cls, threshold: int = 10):
        return cls.objects.filter(is_active=True, stock__lte=threshold)

    
# ================== 入库记录 ==================
class StockIn(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="入库数量")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="进货单价")
    supplier = models.CharField(max_length=100, null=True, blank=True, verbose_name="供应商")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    account = models.ForeignKey("Account", on_delete=models.CASCADE, null=True, blank=True, verbose_name="支付账户")

    class Meta:
        db_table = 'inventory_stockin'
        verbose_name = "采购记录"
        verbose_name_plural = "采购记录列表"

    def __str__(self):
        return f"{self.product.name} 入库 {self.quantity}"


# ================== 支出记录 ==================
class Expense(models.Model):
    account = models.ForeignKey("Account", on_delete=models.CASCADE, null=True, blank=True, verbose_name="支付账户")
    title = models.CharField(max_length=100, verbose_name="支出名称")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="金额")
    category = models.CharField(max_length=50, verbose_name="分类")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_expense'
        verbose_name = "支出记录"
        verbose_name_plural = "支出记录列表"

    def __str__(self):
        return self.title


# ================== 销售记录 ==================
class Sale(models.Model):
    customer = models.ForeignKey(
        'Supplier', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="客户", limit_choices_to={'type': 'customer'}
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="销售数量")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="销售单价")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="总金额")
    profit = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="利润")
    account = models.ForeignKey("Account", on_delete=models.CASCADE, null=True, blank=True, verbose_name="收款账户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_sale'
        verbose_name = "销售记录"
        verbose_name_plural = "销售记录列表"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.sell_price
        if self.product and self.product.cost_price:
            cost_total = self.quantity * self.product.cost_price
            self.profit = self.total_price - cost_total
        else:
            self.profit = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} 销售 {self.quantity}"


# ================== 交易流水 ==================
class Transaction(models.Model):
    TRANSACTION_TYPE = (('income', '收入'), ('expense', '支出'))

    account = models.ForeignKey("Account", on_delete=models.CASCADE, verbose_name="账户")
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE, verbose_name="类型")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="金额")
    description = models.CharField(max_length=255, null=True, blank=True, verbose_name="说明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_transaction'
        verbose_name = "交易流水"
        verbose_name_plural = "交易流水记录"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account.name} - {self.get_type_display()} {self.amount}元"


# ================== 维修记录 ==================
class Repair(models.Model):
    STATUS = (('pending', '待维修'), ('repairing', '维修中'), ('done', '已完成'))

    customer = models.ForeignKey(
        'Supplier', on_delete=models.CASCADE, verbose_name="客户",
        limit_choices_to={'type': 'customer'}
    )
    device_model = models.CharField(max_length=100, verbose_name="设备型号")
    issue = models.TextField(verbose_name="故障描述")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="维修费用")
    status = models.CharField(max_length=20, choices=STATUS, default='pending', verbose_name="维修状态")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    account = models.ForeignKey("Account", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="收款账户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_repair'
        verbose_name = "维修记录"
        verbose_name_plural = "维修记录列表"

    def __str__(self):
        return f"{self.device_model} - {self.get_status_display()}"


class RepairItem(models.Model):
    repair = models.ForeignKey(Repair, on_delete=models.CASCADE, verbose_name="维修记录")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="维修用料")
    quantity = models.IntegerField(verbose_name="使用数量")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_repairitem'
        verbose_name = "维修用料"
        verbose_name_plural = "维修用料记录"

    def __str__(self):
        return f"{self.repair.device_model} - {self.product.name} x{self.quantity}"


# ================== 基础资料 ==================
class Supplier(models.Model):
    SUPPLIER_TYPE = (('supplier', '供应商'), ('customer', '客户'), ('both', '既是供应商也是客户'))

    name = models.CharField(max_length=100, verbose_name="单位名称")
    type = models.CharField(max_length=20, choices=SUPPLIER_TYPE, default='customer', verbose_name="单位类型")
    contact_person = models.CharField(max_length=50, null=True, blank=True, verbose_name="联系人")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="联系电话")
    address = models.TextField(null=True, blank=True, verbose_name="地址")
    bank_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="开户银行")
    bank_account = models.CharField(max_length=50, null=True, blank=True, verbose_name="银行账号")
    tax_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="税号")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'inventory_supplier'
        verbose_name = "来往单位"
        verbose_name_plural = "来往单位列表"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Store(models.Model):
    name = models.CharField(max_length=100, verbose_name="门店名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="门店编码")
    manager = models.CharField(max_length=50, null=True, blank=True, verbose_name="负责人")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="联系电话")
    address = models.TextField(verbose_name="门店地址")
    business_hours = models.CharField(max_length=100, null=True, blank=True, verbose_name="营业时间")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_store'
        verbose_name = "门店信息"
        verbose_name_plural = "门店信息列表"

    def __str__(self):
        return self.name


class Staff(models.Model):
    POSITION = (
        ('manager', '经理'),
        ('cashier', '收银员'),
        ('salesman', '销售员'),
        ('technician', '技术员'),
        ('other', '其他'),
    )
    name = models.CharField(max_length=50, verbose_name="姓名")
    code = models.CharField(max_length=50, unique=True, verbose_name="工号")
    position = models.CharField(max_length=20, choices=POSITION, default='salesman', verbose_name="职位")
    phone = models.CharField(max_length=20, verbose_name="联系电话")
    id_card = models.CharField(max_length=18, null=True, blank=True, verbose_name="身份证号")
    hire_date = models.DateField(verbose_name="入职日期")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="基本工资")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="提成比例(%)")
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="所属门店")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否在职")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_staff'
        verbose_name = "职员信息"
        verbose_name_plural = "职员信息列表"

    def __str__(self):
        return f"{self.name} ({self.get_position_display()})"


class IncomeType(models.Model):
    name = models.CharField(max_length=50, verbose_name="收入类型名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="类型编码")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="父级类型")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_income_type'
        verbose_name = "收入类型"
        verbose_name_plural = "收入类型列表"
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class ExpenseType(models.Model):
    name = models.CharField(max_length=50, verbose_name="费用类型名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="类型编码")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="父级类型")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_expense_type'
        verbose_name = "费用类型"
        verbose_name_plural = "费用类型列表"
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class InitialAccounting(models.Model):
    account = models.ForeignKey("Account", on_delete=models.CASCADE, verbose_name="账户")
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="期初余额")
    initial_date = models.DateField(verbose_name="期初日期")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'inventory_initial_accounting'
        verbose_name = "初期建账"
        verbose_name_plural = "初期建立账户"
        unique_together = ['account', 'initial_date']

    def __str__(self):
        return f"{self.account.name} - 期初余额: {self.initial_balance} (日期: {self.initial_date})"


# ================== SKU 系统 ==================
class ProductAttribute(models.Model):
    name = models.CharField(max_length=50, verbose_name="属性名称")

    class Meta:
        db_table = 'inventory_product_attribute'
        verbose_name = "商品属性"
        verbose_name_plural = "商品属性列表"

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values', verbose_name="属性")
    value = models.CharField(max_length=50, verbose_name="属性值")

    class Meta:
        db_table = 'inventory_product_attribute_value'
        verbose_name = "商品属性值"
        verbose_name_plural = "商品属性值列表"

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductSKU(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='skus', verbose_name="商品")
    attributes = models.JSONField(verbose_name="属性组合")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="售价")
    stock = models.IntegerField(default=0, verbose_name="库存数量")
    code = models.CharField(max_length=50, unique=True, verbose_name="SKU编号")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'inventory_product_sku'
        verbose_name = "商品SKU"
        verbose_name_plural = "商品SKU列表"

    def __str__(self):
        return f"{self.product.name} - {self.attributes} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)