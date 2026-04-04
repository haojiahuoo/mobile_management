# inventory/admin/__init__.py
"""Admin 模块 - 按业务模块分组"""

from .base import BaseAdmin, fmt_money, fmt_status, fmt_stock
from .core import ProductAdmin, ProductCategoryAdmin, ProductSKUInline, ProductAttributeAdmin, ProductAttributeValueAdmin, ProductSKUAdmin
from .transaction import StockInAdmin, SaleAdmin, RepairAdmin, RepairItemAdmin, ExpenseAdmin
from .party import SupplierAdmin, StoreAdmin, StaffAdmin
from .finance import AccountAdmin, TransactionAdmin, IncomeTypeAdmin, ExpenseTypeAdmin, InitialAccountingAdmin
from .site import MyAdminSite, admin_site
from .purchase import (
    PurchaseOrderAdmin, PurchaseOrderItemInline,
    PurchaseReceiptAdmin, PurchaseReceiptItemInline,
    PurchaseReturnAdmin, PurchaseReturnItemInline
)
from .stock import StockAdmin, StockRecordAdmin, StockCheckAdmin, StockTransferAdmin

from .sale import (
    SaleOrderAdmin, SaleOrderItemInline,
    SaleDeliveryAdmin, SaleDeliveryItemInline,
    SaleReturnAdmin, SaleReturnItemInline
)

__all__ = [
    'BaseAdmin', 'fmt_money', 'fmt_status', 'fmt_stock',
    'ProductAdmin', 'ProductCategoryAdmin', 'ProductSKUInline',
    'ProductAttributeAdmin', 'ProductAttributeValueAdmin', 'ProductSKUAdmin',
    'StockInAdmin', 'SaleAdmin', 'RepairAdmin', 'RepairItemAdmin', 'ExpenseAdmin',
    'SupplierAdmin', 'StoreAdmin', 'StaffAdmin',
    'AccountAdmin', 'TransactionAdmin', 'IncomeTypeAdmin', 'ExpenseTypeAdmin',
    'InitialAccountingAdmin',
    'PurchaseOrderAdmin', 'PurchaseOrderItemInline',
    'PurchaseReceiptAdmin', 'PurchaseReceiptItemInline',
    'PurchaseReturnAdmin', 'PurchaseReturnItemInline',
    'StockAdmin', 'StockRecordAdmin', 'StockCheckAdmin', 'StockTransferAdmin',
    'MyAdminSite', 'admin_site',
]