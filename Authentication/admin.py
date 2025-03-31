from django.contrib import admin
from .models import *
# Register your models here.
from django.contrib import admin
from .models import (
    CustomUser, AdminProfile, CashierProfile,  CustomerProfile

)

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name',  'address', 'phone_number', 'created_at')
    search_fields = ('name',  'address')
    list_filter = ('created_at',)
    ordering = ('name',)
    readonly_fields = ('created_at',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'address', 'phone_number', 'created_at')
    search_fields = ('name', 'shop__name', 'manager__email', 'address')
    list_filter = ('created_at', 'shop')
    ordering = ('name',)
    readonly_fields = ('created_at',)

# Register CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'firebase_user_id', 'role', 'phone_number', )
    search_fields = ('email', 'firebase_user_id', 'role')
    list_filter = ('role',)

# Register AdminProfile
@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address', 'employee_id', 'full_name', 'created_at')
    search_fields = ('user__email', 'full_name', 'employee_id')

# Register CashierProfile
@admin.register(CashierProfile)
class CashierProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'assigned_section', 'employee_id', 'full_name', 'created_at')
    search_fields = ('user__email', 'full_name', 'employee_id')

# Register ManagerProfile
# @admin.register(ManagerProfile)
# class ManagerProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'phone_number', 'employee_id', 'assigned_section', 'full_name', 'created_at')
#     search_fields = ('user__email', 'full_name', 'employee_id')

# # Register CustomerProfile
@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'loyalty_points', 'full_name', 'created_at')
    search_fields = ('user__email', 'full_name')


# Register your models here.
admin.site.register(ProductCategory)


# Register Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock_quantity', 'created_at','description')
    search_fields = ('name',)
    list_filter = ('created_at','branch')

# Register Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'total_amount', 'status', 'created_at', 'updated_at')
    search_fields = ('customer__user__email',)
    list_filter = ('status', 'created_at')

# Register OrderItem
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_per_item')
    search_fields = ('order__id', 'product__name')

# Register Payment
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'total_amount', 'amount_paid','change', 'payment_date', 'status')
    search_fields = ('order__id',)
    list_filter = ('payment_method', 'status', 'payment_date')

# Register TransactionLog
@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'timestamp')
    search_fields = ('action', 'user__email')
    list_filter = ('timestamp',)

# Register Receipt
@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('order', 'receipt_number', 'receipt_date', 'total_amount', 'paid_amount', 'change_returned')
    search_fields = ('receipt_number', 'order__id')
    list_filter = ('receipt_date',)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'target_currency')
    search_fields = ('base_currency', 'target_currency')

@admin.register(InventoryChange)
class InventoryChangeAdmin(admin.ModelAdmin):
    list_display = ('product', 'user','quantity_change')
    search_fields = ('product', 'user')

@admin.register(ProductTransfer)
class ProductTransferAdmin(admin.ModelAdmin):
    # Just show the most important fields
    list_display = ['reference', 'product', 'quantity', 'status', 'created_at']
    
    # Add basic filtering
    list_filter = ['status', 'created_at']
    
    # Enable search by reference
    search_fields = ['reference']



class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ('product', 'quantity', 'cost_price', 'received_quantity', 'notes')
    readonly_fields = ('received_quantity',)


class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'order_date', 'expected_delivery_date', 'status', 'total_cost')
    list_filter = ('status', 'supplier', 'order_date')
    search_fields = ('po_number', 'supplier__name')
    inlines = [PurchaseOrderItemInline]
    date_hierarchy = 'order_date'

    def total_cost(self, obj):
        return sum(item.total_cost for item in obj.items.all())

    total_cost.short_description = 'Total Cost'


class DeliveryItemInline(admin.TabularInline):
    model = DeliveryItem
    extra = 1
    fields = ('order_item', 'product', 'quantity', 'cost_price', 'expiry_date', 'batch_number')


class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('delivery_number', 'purchase_order', 'supplier', 'delivery_date', 'received_date', 'status')
    list_filter = ('status', 'supplier', 'delivery_date')
    search_fields = ('delivery_number', 'purchase_order__po_number')
    inlines = [DeliveryItemInline]
    date_hierarchy = 'delivery_date'


class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'product', 'cost_price', 'quantity', 'expiry_date', 'supplier')
    list_filter = ('product', 'supplier', 'expiry_date')
    search_fields = ('batch_number', 'product__name')
    readonly_fields = ('received_date',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'supplier')


class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_item', 'batch', 'quantity', 'sold_price', 'cost_price', 'profit', 'profit_margin')
    list_select_related = ('order_item__order', 'batch')
    readonly_fields = ('profit', 'profit_margin')

    def profit(self, obj):
        return obj.profit

    profit.short_description = 'Total Profit'

    def profit_margin(self, obj):
        return f"{obj.profit_margin:.2f}%"

    profit_margin.short_description = 'Margin %'


# # Register all models
admin.site.register(Supplier)
# admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
# admin.site.register(Delivery, DeliveryAdmin)
# admin.site.register(ProductBatch, ProductBatchAdmin)
# admin.site.register(SaleItem, SaleItemAdmin)


# Optional: If you want to access PurchaseOrderItem and DeliveryItem separately
@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'cost_price', 'remaining_quantity')
    list_select_related = ('order', 'product')


@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'delivery', 'product', 'quantity', 'cost_price', 'batch_number')
    list_select_related = ('delivery', 'product')