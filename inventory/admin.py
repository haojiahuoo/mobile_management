# inventory/admin.py
"""Admin 入口 - 导入所有 Admin 类（自动注册）"""

# 导入所有 Admin 类（@admin.register 会自动注册）
from .admin.core import (
    ProductAdmin, ProductCategoryAdmin,
    ProductAttributeAdmin, ProductAttributeValueAdmin, ProductSKUAdmin
)
from .admin.transaction import (
    StockInAdmin, SaleAdmin, RepairAdmin, RepairItemAdmin, ExpenseAdmin
)
from .admin.party import (
    SupplierAdmin, StoreAdmin, StaffAdmin
)
from .admin.finance import (
    AccountAdmin, TransactionAdmin, IncomeTypeAdmin, ExpenseTypeAdmin, InitialAccountingAdmin
)
from .admin.site import MyAdminSite, admin_site

