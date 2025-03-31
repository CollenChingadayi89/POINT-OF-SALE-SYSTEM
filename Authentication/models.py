from django.db import models
from django.conf import settings
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import User
from django.db import models
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File
from django.utils import timezone
import random

from django.core.files.storage import FileSystemStorage



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email=email)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    firebase_user_id = models.CharField(max_length=255, unique=True)  # Firebase user ID
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    branch = models.CharField(max_length=50, null=True, blank=True)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('cashier', 'Cashier'), ('manager', 'Manager')])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Add related_name to avoid clashes with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="customuser_groups",  # Unique related_name
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_permissions",  # Unique related_name
        related_query_name="customuser",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

class Supplier(models.Model):
    """Model to track product suppliers"""
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    payment_terms = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'


class Shop(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=255)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="shop")
    address = models.TextField()
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.shop.name})"

# Customer Profile
class CustomerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="customer_profile")
    address = models.TextField(null=True, blank=True)
    loyalty_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Customer: {self.user.email}"



# Admin Profile
class AdminProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="admin_profile")
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    employee_id = models.CharField(max_length=255, null=True)
    full_name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Admin: {self.user.email}"

def profile_pic_upload_path(instance, filename):
    # This will create paths like: profile_pics/user123.jpg
    ext = filename.split('.')[-1]
    return f'profile_pics/{instance.firebase_user}.{ext}'

# Optional: Custom storage location for profile pictures
profile_pic_storage = FileSystemStorage(location='/media/profile_pics/')

class CashierProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="cashier_profile")
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    assigned_section = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    employee_id = models.CharField(max_length=255, null=True)
    full_name = models.CharField(max_length=50, null=True, blank=True)
    cashier_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)  
    firebase_user = models.CharField(max_length=50, null=False)
    is_manager = models.BooleanField(default=False)
    is_executive = models.BooleanField(default=False)
    profile_pic = models.ImageField(
        upload_to='profile_pics/',
        storage=profile_pic_storage,  # Optional
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.full_name}'s Profile"
    
    @property
    def profile_pic_url(self):
        if self.profile_pic and hasattr(self.profile_pic, 'url'):
            return self.profile_pic.url
        return None

# Currency Model
class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)  # e.g., USD, EUR
    name = models.CharField(max_length=50)  # e.g., United States Dollar
    symbol = models.CharField(max_length=10)  # e.g., $, €

    def __str__(self):
        return f"{self.name} ({self.code})"

# Exchange Rate Model
class ExchangeRate(models.Model):
    base_currency = models.ForeignKey(Currency, related_name='base_currency_rates', on_delete=models.CASCADE)
    target_currency = models.ForeignKey(Currency, related_name='target_currency_rates', on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    name=models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('base_currency', 'target_currency')

    def __str__(self):
        return f"1 {self.base_currency.code} = {self.rate} {self.target_currency.code}"

# Product Category Model
class ProductCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# Product Model
# class Product(models.Model):
#     name = models.CharField(max_length=255)
#     barcode = models.CharField(max_length=255, unique=True)
#     description = models.TextField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     product_code = models.CharField(max_length=255, unique=True)
#     stock_quantity = models.IntegerField(default=0)
#     category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
#     image = models.ImageField(upload_to='products/', blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     Branch=models.ForeignKey(Branch , on_delete=models.CASCADE)

#     def __str__(self):
#         return self.name



class Product(models.Model):
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_code = models.CharField(max_length=255, unique=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Cost price per unit"
    )
    last_purchase_date = models.DateField(blank=True, null=True)
    last_purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Last purchase price per unit"
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Primary supplier for this product"
    )
    min_stock_level = models.PositiveIntegerField(
        default=0,
        help_text="Minimum stock level before reordering"
    )
    reorder_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Quantity to reorder when stock reaches min level"
    )

    # Add this property to calculate profit margin
    @property
    def profit_margin(self):
        if self.cost_price and self.price and self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 0

    @property
    def profit_per_unit(self):
        if self.cost_price and self.price:
            return self.price - self.cost_price
        return 0

    # Add this method to get current stock value
    def get_stock_value(self):
        return self.stock_quantity * self.cost_price if self.cost_price else 0

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.barcode:
            # Generate 12-digit barcode
            self.barcode = self.generate_barcode()
            # Set product code as last 4 digits
            self.product_code = self.barcode[-4:]
            # Generate barcode image
            self.generate_barcode_image()
        super().save(*args, **kwargs)

    def generate_barcode(self):
        """Generate a 12-digit barcode with branch prefix"""
        branch_prefix = str(self.branch.id).zfill(3)  # 3-digit branch ID
        random_digits = str(random.randint(100000000, 999999999))[-9:]  # 9 random digits
        return f"{branch_prefix}{random_digits}"

    def generate_barcode_image(self):
        """Generate barcode image using python-barcode"""
        barcode_class = barcode.get_barcode_class('ean13')
        ean = barcode_class(self.barcode, writer=ImageWriter())
        buffer = BytesIO()
        ean.write(buffer)
        self.barcode_image.save(f'barcode_{self.name}.png', File(buffer), save=False)

    def update_stock(self, quantity_change):
        """Helper method to update stock quantity"""
        self.stock_quantity += quantity_change
        self.save()
        return self.stock_quantity

# Order Model
class Order(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True)
    sales_person = models.ForeignKey(CashierProfile, on_delete=models.SET_NULL, related_name='sales', null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    customer_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Order {self.id}"

# Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

# Payment Model
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    # currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    currency=models.CharField(max_length=20)
    payment_method = models.CharField(max_length=50, choices=[('credit_card', 'Credit Card'), ('cash', 'Cash'), ('mobile_money', 'Mobile Money')])
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')
    change =models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payment for Order {self.order.id}"



# Receipt Model
class Receipt(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=255, unique=True)
    receipt_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    change_returned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Receipt {self.receipt_number} for Order {self.order.id}"



class InventoryChange(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_change = models.IntegerField()  # Positive for additions, negative for removals
    reason = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='inventory_changes')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Inventory Change'
        verbose_name_plural = 'Inventory Changes'

    def __str__(self):
        return f"{self.product.name}: {self.quantity_change:+} ({self.reason})"

    def save(self, *args, **kwargs):
        """
        Override save method to automatically update product stock quantity
        """
        # Calculate difference if this is an update
        if self.pk:
            old_record = InventoryChange.objects.get(pk=self.pk)
            difference = self.quantity_change - old_record.quantity_change
        else:
            difference = self.quantity_change

        # Update product stock
        self.product.stock_quantity += difference
        self.product.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete method to reverse the inventory change
        """
        self.product.stock_quantity -= self.quantity_change
        self.product.save()
        super().delete(*args, **kwargs)

# Discount Model
class Discount(models.Model):
    name = models.CharField(max_length=255)
    discount_type = models.CharField(max_length=20, choices=[('percentage', 'Percentage'), ('amount', 'Amount')])
    value = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Transaction Log Model
class TransactionLog(models.Model):
    action = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.action} by {self.user.email} at {self.timestamp}"



from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class ProductTransfer(models.Model):
    TRANSFER_TYPES = (
        ('INTERNAL', 'Between Branches'),
        ('SUPPLIER', 'From Supplier'),
        ('CUSTOMER', 'To Customer'),
        ('ADJUSTMENT', 'Inventory Adjustment'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    )

    # Core Fields (Horizontal Layout)
    reference = models.CharField(max_length=20, unique=True, editable=False)
    product = models.ForeignKey('Product', on_delete=models.PROTECT, related_name='transfers')
    from_location = models.ForeignKey('Branch', on_delete=models.PROTECT, related_name='outgoing_transfers', null=True, blank=True)
    to_location = models.ForeignKey('Branch', on_delete=models.PROTECT, related_name='incoming_transfers', null=True, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, default='INTERNAL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey('CashierProfile', on_delete=models.PROTECT, related_name='created_transfers')
    approved_by = models.ForeignKey('CashierProfile', on_delete=models.PROTECT, related_name='approved_transfers', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product Transfer'
        verbose_name_plural = 'Product Transfers'
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['product']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.reference} - {self.product.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def generate_reference(self):
        date_part = timezone.now().strftime('%Y%m%d')
        last_transfer = ProductTransfer.objects.filter(
            reference__startswith=date_part
        ).order_by('-reference').first()
        
        seq = int(last_transfer.reference[-4:]) + 1 if last_transfer else 1
        return f"TR{date_part}{seq:04d}"

    @property
    def source_barcode(self):
        return self.product.barcode if self.product else None

    @property
    def destination_barcode(self):
        if self.transfer_type == 'INTERNAL' and self.to_location:
            # Generate new barcode for internal transfers
            return f"{self.product.barcode}-{self.to_location.code}"
        return self.product.barcode




class PurchaseOrder(models.Model):
    """Model to track orders placed with suppliers"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('partial', 'Partially Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='orders')
    order_date = models.DateField()
    expected_delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='created_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PO-{self.po_number} ({self.supplier.name})"

    def save(self, *args, **kwargs):
        if not self.po_number:
            # Generate PO number if not provided
            last_po = PurchaseOrder.objects.order_by('-id').first()
            last_id = last_po.id if last_po else 0
            self.po_number = f"PO-{timezone.now().strftime('%Y%m')}-{last_id + 1:04d}"
        super().save(*args, **kwargs)

    @property
    def total_cost(self):
        return sum(item.total_cost for item in self.items.all())

    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'


class PurchaseOrderItem(models.Model):
    """Items included in a purchase order"""
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Per unit cost price")
    received_quantity = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_cost(self):
        return self.quantity * self.cost_price

    @property
    def remaining_quantity(self):
        return self.quantity - self.received_quantity

    class Meta:
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'


class Delivery(models.Model):
    """Model to track deliveries from suppliers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Received'),
        ('received', 'Received'),
        ('checked', 'Checked'),
        ('cancelled', 'Cancelled'),
    ]

    delivery_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='deliveries')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    delivery_date = models.DateField()
    received_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    received_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery-{self.delivery_number}"

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            # Generate delivery number if not provided
            last_delivery = Delivery.objects.order_by('-id').first()
            last_id = last_delivery.id if last_delivery else 0
            self.delivery_number = f"DEL-{timezone.now().strftime('%Y%m')}-{last_id + 1:04d}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-delivery_date']
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'


class DeliveryItem(models.Model):
    """Items received in a delivery"""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Actual received cost price")
    expiry_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Update the received quantity in the purchase order item
        if not self.pk:  # Only on creation
            self.order_item.received_quantity += self.quantity
            self.order_item.save()

            # Update product cost price if this is the first delivery
            if self.order_item.received_quantity == self.quantity:
                self.product.cost_price = self.cost_price
                self.product.save()

            # Update product stock
            self.product.stock_quantity += self.quantity
            self.product.save()

            # Create inventory change record
            InventoryChange.objects.create(
                product=self.product,
                quantity_change=self.quantity,
                reason=f"Delivery from supplier: {self.delivery.delivery_number}",
                user=self.delivery.received_by
            )

        super().save(*args, **kwargs)

    @property
    def total_cost(self):
        return self.quantity * self.cost_price

    class Meta:
        verbose_name = 'Delivery Item'
        verbose_name_plural = 'Delivery Items'

