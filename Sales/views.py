from locale import currency
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from Authentication.models import *
from rest_framework.decorators import api_view
from rest_framework import status
from django.db import transaction
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction as db_transaction
import json
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import DatabaseError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser, FormParser
import random
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File
from rest_framework.generics import ListAPIView
from .barcode_utils import generate_barcode_base, generate_barcode_image

class CategoryList(ListAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategorySerializer

# views.py
@api_view(['POST'])
def create_product(request, firebase_id):
    try:
        logger.info(f"Product creation started for firebase_id: {firebase_id}")
        
        # 1. Validate cashier exists with branch
        try:
            cashier = CashierProfile.objects.get(firebase_user=firebase_id)
            if not cashier.cashier_branch:
                return Response(
                    {"error": "Cashier is not assigned to any branch"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except CashierProfile.DoesNotExist:
            return Response(
                {"error": "Cashier profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Validate required fields
        if 'name' not in request.data or 'price' not in request.data:
            return Response(
                {"error": "Product name and price are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Check for duplicate product (name + description + price + branch)
        duplicate = Product.objects.filter(
            name__iexact=request.data['name'],
            description__iexact=request.data.get('description', ''),
            price=Decimal(request.data['price']),
            branch=cashier.cashier_branch
        ).first()

        if duplicate:
            return Response(
                {
                    "status": "error",
                    "code": "product_exists",
                    "message": "Product already exists in system",
                    "existing_product": {
                        "id": duplicate.id,
                        "name": duplicate.name,
                        "barcode": duplicate.barcode,
                        "barcode_image_url": request.build_absolute_uri(duplicate.barcode_image.url) if duplicate.barcode_image else None
                    }
                },
                status=status.HTTP_409_CONFLICT
            )

        # 4. Generate barcode
        barcode_base = generate_barcode_base(cashier.cashier_branch.id)
        product_code = barcode_base[-4:]

        # 5. Create product
        product_data = {
            'name': request.data['name'],
            'price': request.data['price'],
            'description': request.data.get('description', ''),
            'stock_quantity': request.data.get('stock_quantity', 0),
            'category': request.data.get('category'),
            'barcode': barcode_base,
            'product_code': product_code,
            'branch': cashier.cashier_branch.id
        }

        serializer = ProductSerializer(data=product_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.save()

        # 6. Generate and save barcode image
        barcode_img = generate_barcode_image(barcode_base)
        filename = f"barcode_{product.id}_{barcode_base}.png"
        product.barcode_image.save(filename, barcode_img)
        product.save()

        return Response({
            "status": "success",
            "product": serializer.data,
            "barcode_image_url": request.build_absolute_uri(product.barcode_image.url),
            "message": "Product created successfully"
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Product creation error: {str(e)}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class ProductListAPIView(APIView):
  
    def get(self, request, firebase_user_id, format=None):

        try:
            cashier = CashierProfile.objects.get(firebase_user=firebase_user_id)
            print(cashier.cashier_branch)
            if not cashier.cashier_branch:
                return Response({"error": "Cashier has no assigned branch"}, status=400)
                
            products = Product.objects.filter(branch=cashier.cashier_branch)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
            
        except CashierProfile.DoesNotExist:
            return Response({"error": "Cashier not found"}, status=404)
    


class ProductCreateAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, format=None):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            # Set the branch automatically based on the cashier
            firebase_user_id = request.headers.get('Authorization', '').split('Bearer ')[-1]
            try:
                cashier = CashierProfile.objects.get(firebase_user_id=firebase_user_id)
                if not cashier.cashier_branch:
                    return Response({"error": "Cashier has no assigned branch"}, status=status.HTTP_400_BAD_REQUEST)
                
                product = serializer.save(branch=cashier.cashier_branch)
                return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
            
            except CashierProfile.DoesNotExist:
                return Response({"error": "Cashier not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET'])
# def get_pharmacy_medicines(request, firebase_user_id):
#     try:
#         cashier = CashierProfile.objects.get(user__firebase_user_id=firebase_user_id)
#         cashier_branch = cashier.cashier_branch
#         products = Product.objects.filter(Branch=cashier_branch)
#         data = [{"name": med.name,"price": med.price ,"stock": med.stock ,"description": med.description } for med in medicines]
#         print(data)
#         return Response(data, status=200)
#     except Phamarcist.DoesNotExist:
#         return Response({"error": "Pharmacist not found"}, status=404)
#     except Exception as e:
#         return Response({"error": str(e)}, status=500)

class ProductCategoryListAPIView(APIView):
    def get(self, request, format=None):
        categories = ProductCategory.objects.all()
        serializer = ProductCategorySerializer(categories, many=True)
        return Response(serializer.data)


class CustomerListAPIView(APIView):
    def get(self, request, format=None):
        customers = CustomerProfile.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def exchange_rate_view(request, name):
    try:
        # Filter exchange rate by 'name'
        print(request.data)
        exchange_rate = ExchangeRate.objects.get(name=name)
        print("collen")
        serializer = ExchangeRateSerializer(exchange_rate)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except ExchangeRate.DoesNotExist:
        return Response(
            {"error": "Exchange rate not found for the given name."},
            status=status.HTTP_404_NOT_FOUND
        )


logger = logging.getLogger(__name__)



@method_decorator(csrf_exempt, name='dispatch')
class CreateTransactionView(View):
    @transaction.atomic  # Ensures atomicity for the entire operation
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            transaction_data = data.get('transaction', {})
            customer_data = data.get('customer', {})
            cashier_data = data.get('cashier', {})
            order_items_data = data.get('order_items', [])

            # Create a savepoint to rollback to if needed
            sid = transaction.savepoint()

            # Get profiles with select_for_update() for isolation
            customer_profile = CustomerProfile.objects.select_for_update().get(
                id=customer_data.get('id')
            )
            cashier_profile = CashierProfile.objects.select_for_update().get(
                user=cashier_data.get('id')
            )


            # Create order
            order = Order.objects.create(
                customer=customer_profile,
                sales_person=cashier_profile,
                total_amount=transaction_data.get('total_amount'),
                currency=transaction_data.get('currency'),
                status='completed'
            )

            # Process items with inventory locking
            for item_data in order_items_data:
                # Lock the product row until transaction completes
                product = Product.objects.select_for_update().get(
                    id=item_data.get('product_id')
                )
                quantity = item_data.get('quantity')

                # Verify stock is sufficient
                if product.stock_quantity < quantity:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse(
                        {'status': 'error', 'message': f'Insufficient stock for {product.name}'},
                        status=400
                    )

                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_per_item=item_data.get('price'),
                    total_price=item_data.get('price') * quantity
                )

                # Record inventory change
                InventoryChange.objects.create(
                    product=product,
                    quantity_change=-quantity,
                    reason='purchase',
                    user=cashier_profile.user,
                    order=order
                )

                # Update product stock
                # product.stock_quantity -= quantity
                # product.save()

            # Create payment
            payment = Payment.objects.create(
                order=order,
                amount_paid=transaction_data.get('amount_paid'),
                total_amount=transaction_data.get('total_amount'),
                currency=transaction_data.get('currency'),
                payment_method='cash',
                change=transaction_data.get('change'),
                status='completed'
            )

            # Success - commit all changes
            transaction.savepoint_commit(sid)
            return JsonResponse({
                'status': 'success',
                'order_id': order.id,
                'message': 'Transaction completed successfully'
            }, status=201)

        except CustomerProfile.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'message': 'Customer profile not found'},
                status=400
            )
        except CashierProfile.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'message': 'Cashier profile not found'},
                status=400
            )
        except Product.DoesNotExist as e:
            return JsonResponse(
                {'status': 'error', 'message': f'Product not found: {str(e)}'},
                status=400
            )
        except DatabaseError as e:
            transaction.savepoint_rollback(sid)
            return JsonResponse(
                {'status': 'error', 'message': f'Database error: {str(e)}'},
                status=500
            )
        except Exception as e:
            transaction.savepoint_rollback(sid)
            return JsonResponse(
                {'status': 'error', 'message': f'Unexpected error: {str(e)}'},
                status=500
            )


@api_view(['POST'])
@transaction.atomic
def transfer_stock(request, product_id):
    try:
        # Validate required parameters
        target_branch_id = request.data.get('target_branch')
        quantity = int(request.data.get('quantity', 0))
        firebase_id = request.data.get('firebaseId')
        
        if not target_branch_id or quantity <= 0 or not firebase_id:
            return Response({"error": "Missing or invalid parameters"}, status=400)

        # Get objects with necessary relationships
        product = Product.objects.select_for_update().get(id=product_id)
        cashier = CashierProfile.objects.select_related('user').get(firebase_user=firebase_id)
        from_branch = cashier.cashier_branch
        to_branch = Branch.objects.get(id=target_branch_id)

        # Verify product belongs to cashier's branch
        if product.branch != from_branch:
            return Response({"error": "Product not available in your branch"}, status=403)

        # Check stock availability
        if product.stock_quantity < quantity:
            return Response({
                "error": "Insufficient stock",
                "available": product.stock_quantity,
                "requested": quantity
            }, status=400)

        # Generate unique barcode for the new product instance
        # new_barcode = generate_unique_barcode()
        # while Product.objects.filter(barcode=new_barcode).exists():
        #     new_barcode = generate_unique_barcode()

        # Create target product
        target_product = Product.objects.create(
            barcode='78886554',
            branch=to_branch,
            name=product.name,
            price=product.price,
            description=product.description,
            category=product.category,
            stock_quantity=quantity,
            # cost_price=product.cost_price,
            # supplier=product.supplier
        )

        # Update source stock and create inventory changes
        product.stock_quantity -= quantity
        product.save()

        # Create inventory change for source product (outbound)
        InventoryChange.objects.create(
            product=product,
            quantity_change=-quantity,
            reason=f"Transfer to {to_branch.name} (ID: {to_branch.id})",
            user=cashier.user
        )

        # Create inventory change for target product (inbound)
        InventoryChange.objects.create(
            product=target_product,
            quantity_change=quantity,
            reason=f"Transfer from {from_branch.name} (ID: {from_branch.id})",
            user=cashier.user
        )

        # Create transfer record
        transfer = ProductTransfer.objects.create(
            product=product,
            from_location=from_branch,
            to_location=to_branch,
            quantity=quantity,
            created_by=cashier,
            status='COMPLETED'
        )

        return Response({
            "message": "Stock transferred successfully",
            "transfer_reference": transfer.reference,
            "source_stock": product.stock_quantity,
            "target_stock": target_product.stock_quantity,
            "new_barcode": target_product.barcode,
            "inventory_changes": {
                "outbound": {
                    "product_id": product.id,
                    "new_quantity": product.stock_quantity
                },
                "inbound": {
                    "product_id": target_product.id,
                    "new_quantity": target_product.stock_quantity
                }
            }
        })

    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)
    except CashierProfile.DoesNotExist:
        return Response({"error": "Cashier not found"}, status=404)
    except Branch.DoesNotExist:
        return Response({"error": "Branch not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
# @api_view(['POST'])
# def transfer_stock(request, product_id):
#     try:
#         product = Product.objects.get(id=product_id)
#         target_branch_id = request.data.get('target_branch')
#         quantity = int(request.data.get('quantity', 0))
#         firebase_id = request.data.get('firebaseId')

#         cashier = CashierProfile.objects.get(firebase_user = firebase_id)
#         from_branch = cashier.cashier_branch
        
#         from_branch_stock = Product.objects.get(branch = from_branch )

#         from_trans_product = Product.objects.get(id=product_id)
#         from_trans_product.stock_quantity -= quantity

#         if quantity <= 0:
#             return Response({"error": "Invalid quantity"}, status=400)
            
#         if product.stock_quantity < quantity:
#             return Response({"error": "Not enough stock available"}, status=400)
            
#         # Find or create the product in target branch
#         target_product, created = Product.objects.get_or_create(
#             barcode=product.barcode,
#             branch_id=target_branch_id,
#             defaults={
#                 'name': product.name,
#                 'price': product.price,
#                 'description': product.description,
#                 'category': product.category,
#                 'stock_quantity': 0
#             }
#         )
        
#         # Update quantities
#         product.stock_quantity -= quantity
#         target_product.stock_quantity += quantity
        
#         product.save()
#         target_product.save()
        
#         return Response({
#             "message": "Stock transferred successfully",
#             "source_stock": product.stock_quantity,
#             "target_stock": target_product.stock_quantity
#         })
        
#     except Product.DoesNotExist:
#         return Response({"error": "Product not found"}, status=404)
#     except Exception as e:
#         return Response({"error": str(e)}, status=500)
    


# -----------------------------------------------------------------------------------

# views.py
# views.py
@api_view(['PUT'])
def update_product(request, id):
    try:
        product = get_object_or_404(Product, id=id)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['DELETE'])
def delete_product(request, id):
    try:
        product = get_object_or_404(Product, id=id)
        product_name = product.name  # Get the name before deletion
        product.delete()
        return Response({
            "message": "Product deleted successfully",
            "deleted_product": {
                "id": id,
                "name": product_name
            }
        }, status=status.HTTP_200_OK)  # Changed to 200 OK to include response body
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def transfer_stock(request, product_id):
    print(request.data)
    try:
        source_product = get_object_or_404(Product, id=product_id)
        target_branch_id = request.data.get('target_branch')
        quantity = int(request.data.get('quantity', 0))
        
        if quantity <= 0:
            return Response({"error": "Quantity must be positive"}, status=status.HTTP_400_BAD_REQUEST)
            
        if source_product.stock_quantity < quantity:
            return Response({"error": "Not enough stock available"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Find or create product in target branch
        target_product, created = Product.objects.get_or_create(
            barcode=source_product.barcode,
            branch_id=target_branch_id,
            defaults={
                'name': source_product.name,
                'price': source_product.price,
                'description': source_product.description,
                'category': source_product.category,
                'stock_quantity': 0,
                'product_code': source_product.product_code
            }
        )
        
        # Update quantities
        source_product.stock_quantity -= quantity
        target_product.stock_quantity += quantity
        
        source_product.save()
        target_product.save()
        
        return Response({
            "message": "Stock transferred successfully",
            "source_stock": source_product.stock_quantity,
            "target_stock": target_product.stock_quantity
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def list_categories(request):
    try:
        categories = ProductCategory.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def list_branches(request, firebase_user_id):
    try:
        # Get the cashier profile
        cashier = CashierProfile.objects.get(firebase_user=firebase_user_id)
        
        # If cashier has no branch assigned, return empty list
        if not cashier.cashier_branch:
            return Response([], status=status.HTTP_200_OK)
            
        # Get all branches from the same shop as the cashier's branch
        branches = Branch.objects.filter(shop=cashier.cashier_branch.shop)
        
        serializer = BranchSerializer(branches, many=True)
        return Response(serializer.data)
        
    except CashierProfile.DoesNotExist:
        return Response({"error": "Cashier not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET', 'PATCH'])
def cashier_profile(request, firebase_id):
    try:
        profile = get_object_or_404(CashierProfile, firebase_user=firebase_id)
        
        if request.method == 'GET':
            serializer = CashierProfileSerializer(profile)
            return Response(serializer.data)
            
        elif request.method == 'PATCH':
            serializer = CashierProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                # Handle file upload
                if 'profile_pic' in request.FILES:
                    # Delete old image if exists
                    if profile.profile_pic:
                        profile.profile_pic.delete()
                    # Save new image
                    profile.profile_pic = request.FILES['profile_pic']
                    profile.save()
                
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def low_stock_products(request, firebase_id):
    try:
        # Get cashier's branch
        cashier = CashierProfile.objects.get(firebase_user=firebase_id)
        branch = cashier.cashier_branch

        # Get products with stock < 10 for this branch
        products = Product.objects.filter(
            branch=branch,
            stock_quantity__lt=10
        ).order_by('stock_quantity')

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    except CashierProfile.DoesNotExist:
        return Response({'error': 'Cashier not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)