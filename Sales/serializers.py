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