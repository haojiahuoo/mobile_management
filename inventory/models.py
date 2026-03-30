# inventory/models.py
from django.db import models

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


class ProductCategory(models.Model):
    """商品分类模型（支持无限级分类）"""
    name = models.CharField(max_length=100, verbose_name="分类名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="分类编码")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="父级分类")
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


class Product(models.Model):
    """商品模型"""
    code = models.CharField(max_length=50, unique=True, verbose_name="商品编号", blank=True, null=True)
    brand = models.CharField(max_length=100, verbose_name="商品品牌", blank=True, default="")
    name = models.CharField(max_length=100, verbose_name="商品名称")
    category = models.ForeignKey(
        'ProductCategory', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        verbose_name="商品分类"
    )
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="供应商")
    unit = models.CharField(max_length=20, default="个", verbose_name="单位")
    stock = models.IntegerField(default=0, verbose_name="库存数量")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="成本价")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="售价")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联账户")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'inventory_product'
        verbose_name = "商品"
        verbose_name_plural = "商品信息"
        
    def __str__(self):
        return f"[{self.code}] {self.brand} {self.name}" if self.brand else f"[{self.code}] {self.name}"
    
    def save(self, *args, **kwargs):
        # 如果没有商品编号，自动生成
        if not self.code:
            if self.category:
                last_product = Product.objects.filter(category=self.category).order_by('-code').first()
                if last_product and last_product.code:
                    try:
                        last_num = int(last_product.code[-4:])
                        new_num = last_num + 1
                        self.code = f"{self.category.get_full_code()}{new_num:04d}"
                    except:
                        self.code = f"{self.category.get_full_code()}0001"
                else:
                    self.code = f"{self.category.get_full_code()}0001"
            else:
                last_product = Product.objects.all().order_by('-id').first()
                if last_product and last_product.code:
                    try:
                        last_num = int(last_product.code[-4:])
                        new_num = last_num + 1
                        self.code = f"0000{new_num:04d}"
                    except:
                        self.code = f"0000{Product.objects.count() + 1:04d}"
                else:
                    self.code = "00000001"
        super().save(*args, **kwargs)
    
    def generate_code(self):
        """自动生成商品编号"""
        last_product = Product.objects.filter(category=self.category).order_by('-code').first()
        if last_product and last_product.code:
            try:
                last_num = int(last_product.code[-4:])
                new_num = last_num + 1
                return f"{self.category.get_full_code()}{new_num:04d}"
            except:
                pass
        return f"{self.category.get_full_code()}0001"


class StockIn(models.Model):
    """采购记录模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="入库数量")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="进货单价")
    supplier = models.CharField(max_length=100, null=True, blank=True, verbose_name="供应商")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, verbose_name="支付账户")
    
    class Meta:
        db_table = 'inventory_stockin'
        verbose_name = "采购记录"
        verbose_name_plural = "采购记录列表"
        
    def __str__(self):
        return f"{self.product.name} 入库 {self.quantity}"


class Expense(models.Model):
    """支出记录模型"""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, verbose_name="支付账户")
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


class Sale(models.Model):
    """销售记录模型"""
    # 客户字段关联到 Supplier，并限制只显示客户类型的来往单位
    customer = models.ForeignKey(
        'Supplier', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="客户",
        limit_choices_to={'type': 'customer'}  # 只显示客户类型的来往单位
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="销售数量")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="销售单价")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="总金额")
    profit = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="利润")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, verbose_name="收款账户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_sale'
        verbose_name = "销售记录"
        verbose_name_plural = "销售记录列表"
        
    def save(self, *args, **kwargs):
        """保存时自动计算总金额和利润"""
        self.total_price = self.quantity * self.sell_price
        if self.product and self.product.cost_price:
            cost_total = self.quantity * self.product.cost_price
            self.profit = self.total_price - cost_total
        else:
            self.profit = 0
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.product.name} 销售 {self.quantity}"


class Transaction(models.Model):
    """交易流水模型"""
    TRANSACTION_TYPE = (
        ('income', '收入'),
        ('expense', '支出'),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="账户")
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


class Repair(models.Model):
    """维修记录模型"""
    STATUS = (
        ('pending', '待维修'),
        ('repairing', '维修中'),
        ('done', '已完成'),
    )

    # 客户字段关联到 Supplier，并限制只显示客户类型的来往单位
    customer = models.ForeignKey(
        'Supplier', 
        on_delete=models.CASCADE, 
        verbose_name="客户",
        limit_choices_to={'type': 'customer'}  # 只显示客户类型的来往单位
    )
    device_model = models.CharField(max_length=100, verbose_name="设备型号")
    issue = models.TextField(verbose_name="故障描述")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="维修费用")
    status = models.CharField(max_length=20, choices=STATUS, default='pending', verbose_name="维修状态")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="收款账户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 'inventory_repair'
        verbose_name = "维修记录"
        verbose_name_plural = "维修记录列表"
        
    def __str__(self):
        return f"{self.device_model} - {self.get_status_display()}"


class RepairItem(models.Model):
    """维修用料模型"""
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


# ================== 基础资料模块 ==================

class Supplier(models.Model):
    """来往单位（供应商/客户）"""
    SUPPLIER_TYPE = (
        ('supplier', '供应商'),
        ('customer', '客户'),
        ('both', '既是供应商也是客户'),
    )
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
    """门店信息"""
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
    """职员信息"""
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
    """收入类型"""
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
    """费用类型"""
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
    """初期建账"""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="账户")
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