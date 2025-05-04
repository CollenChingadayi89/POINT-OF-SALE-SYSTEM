from rest_framework import serializers
from Authentication.models import *

# class ProductSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = '__all__'

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['id', 'user', 'address', 'loyalty_points', 'created_at', 'full_name']  # Add other fields if needed

class ExchangeRateSerializer(serializers.ModelSerializer):
    base_currency_name = serializers.CharField(source='base_currency.name', read_only=True)
    target_currency_name = serializers.CharField(source='target_currency.name', read_only=True)
    base_currency_code = serializers.CharField(source='base_currency.code', read_only=True)
    target_currency_code = serializers.CharField(source='target_currency.code', read_only=True)
    name = serializers.CharField(read_only=True)  # Removed source='name'

    class Meta:
        model = ExchangeRate
        fields = [
            'base_currency_code',
            'base_currency_name',
            'target_currency_code',
            'target_currency_name',
            'name',
            'rate',
            'updated_at'
        ]


class CashierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile  # Assuming cashier is also a CustomerProfile
        fields = ['id', 'role', 'first_name', 'phone_number']  # Adjust fields as necessary

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        # fields = ['product_id', 'quantity', 'price']  # Adjust fields as necessary

class TransactionSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=3)
    date = serializers.DateTimeField()
    currency = serializers.CharField(max_length=10)
    change = serializers.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)

class CreateTransactionSerializer(serializers.Serializer):
    customer = CustomerSerializer()
    cashier = CashierSerializer()
    order_items = OrderItemSerializer(many=True)
    transaction = TransactionSerializer()




class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'barcode', 'product_code',
            'description', 'price', 'stock_quantity', 'category', 'category_name',
            'barcode_image', 'branch'
        ]
        read_only_fields = [
            'id', 'barcode', 'product_code', 'barcode_image', 'category_name'
        ]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


# -----------------------------------------------------------------------



class BranchSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    
    class Meta:
        model = Branch
        fields = ['id', 'name', 'shop', 'shop_name', 'address', 'phone_number']

class CashierProfileSerializer(serializers.ModelSerializer):
    cashier_branch = BranchSerializer(read_only=True)
    profile_pic_url = serializers.SerializerMethodField()

    class Meta:
        model = CashierProfile
        fields = [
            'id',
            'firebase_user',
            'full_name',
            'phone_number',
            'assigned_section',
            'employee_id',
            'cashier_branch',  # Now includes nested branch data
            'profile_pic',
            'profile_pic_url',
            'created_at',
        ]
    
    def get_profile_pic_url(self, obj):
        if obj.profile_pic and hasattr(obj.profile_pic, 'url'):
            return obj.profile_pic.url
        return None


class CompanySerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'address',
            'city',
            'country',
            'website',
            'logo_url'
        ]

    def get_logo_url(self, obj):
        if obj.logo:
            return self.context['request'].build_absolute_uri(obj.logo.url)
        return None


class SupplierSerializer(serializers.ModelSerializer):
    branch = BranchSerializer(read_only=True)
    branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        source='branch',
        write_only=True,
        required=False
    )

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_person', 'email', 'phone',
            'address', 'tax_id', 'payment_terms', 'notes',
            'is_active', 'created_at', 'updated_at', 'branch', 'branch_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        """
        Validate that supplier name is unique within a branch
        """
        branch = self.initial_data.get('branch_id')
        if not branch:
            return value

        queryset = Supplier.objects.filter(name=value, branch_id=branch)
        if self.instance:  # If updating, exclude current instance
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A supplier with this name already exists in this branch."
            )
        return value

    def validate_phone(self, value):
        """
        Basic phone number validation
        """
        if not value:
            raise serializers.ValidationError("Phone number is required")
        if not value.isdigit():
            raise serializers.ValidationError("Phone number should contain only digits")
        return value


    # puchase orders


#
# class PurchaseOrderItemSerializer(serializers.ModelSerializer):
#     product_name = serializers.CharField(source='product.name', read_only=True)
#     product_code = serializers.CharField(source='product.product_code', read_only=True)
#
#     class Meta:
#         model = PurchaseOrderItem
#         fields = ['id', 'order', 'product', 'product_name', 'product_code',
#                   'quantity', 'cost_price', 'received_quantity', 'notes']
#         read_only_fields = ['received_quantity']
#
#
# class PurchaseOrderSerializer(serializers.ModelSerializer):
#     items = PurchaseOrderItemSerializer(many=True, read_only=True)
#     supplier_name = serializers.CharField(source='supplier.name', read_only=True)
#     branch_name = serializers.CharField(source='branch.name', read_only=True)
#     created_by_name = serializers.CharField(source='created_by.email', read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     pdf_url = serializers.SerializerMethodField()
#
#     class Meta:
#         model = PurchaseOrder
#         fields = ['id', 'po_number', 'supplier', 'supplier_name', 'branch', 'branch_name',
#                   'order_date', 'expected_delivery_date', 'status', 'status_display',
#                   'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at',
#                   'items', 'total_cost', 'pdf_url']
#         read_only_fields = ['po_number', 'created_by', 'created_at', 'updated_at', 'total_cost']
#
#     def get_pdf_url(self, obj):
#         if obj.pdf_path:
#             return self.context['request'].build_absolute_uri(obj.pdf_path.url)
#         return None


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Make ID optional for new items
    product_id = serializers.IntegerField(write_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product_id', 'product_name', 'product_code',
            'quantity', 'cost_price', 'received_quantity', 'notes'
        ]
        read_only_fields = ['received_quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive")
        return value

    def validate_cost_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Cost price must be positive")
        return value


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True)
    supplier_id = serializers.IntegerField(write_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier_id', 'supplier_name', 'branch_id',
            'order_date', 'expected_delivery_date', 'status', 'status_display',
            'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'po_number', 'status', 'created_at', 'updated_at', 'branch_id'
        ]

    def validate(self, data):
        # Ensure at least one item
        if not data.get('items') or len(data['items']) == 0:
            raise serializers.ValidationError({"items": "At least one item is required"})

        # Validate delivery date
        if (data.get('expected_delivery_date') and
                data['expected_delivery_date'] < data.get('order_date')):
            raise serializers.ValidationError(
                {"expected_delivery_date": "Must be after order date"}
            )

        return data

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        branch = self.context.get('branch')

        with transaction.atomic():
            # Update order fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Handle items
            self._update_order_items(instance, items_data, branch)

        return instance

    def _update_order_items(self, order, items_data, branch):
        existing_items = {item.id: item for item in order.items.all()}
        updated_ids = set()

        for item_data in items_data:
            item_id = item_data.get('id')

            if item_id and item_id in existing_items:
                # Update existing item
                item = existing_items[item_id]
                for attr, value in item_data.items():
                    setattr(item, attr, value)
                item.save()
                updated_ids.add(item_id)
            else:
                # Create new item
                PurchaseOrderItem.objects.create(
                    order=order,
                    branch=branch,
                    **item_data
                )

        # Delete items not in the update
        to_delete = set(existing_items.keys()) - updated_ids
        if to_delete:
            order.items.filter(id__in=to_delete).delete()