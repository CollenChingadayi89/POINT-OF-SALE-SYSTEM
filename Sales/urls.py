from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Your existing views
    ProductListAPIView, CustomerListAPIView, ProductCategoryListAPIView,
    exchange_rate_view, create_product, CreateTransactionView, CategoryList,
    low_stock_products, update_product, delete_product, transfer_stock,
    cashier_profile, list_categories, list_branches, CompanyDetailAPIView,
    get_suppliers, create_supplier, update_supplier, get_branches,  get_purchase_orders,
    create_purchase_order,
    get_purchase_order_detail,
    delete_purchase_order,
    generate_purchase_order_pdf,update_purchase_order,

    # Purchase Order views

    get_suppliers, get_products
)

# Create a router for the ViewSets


urlpatterns = [
    # Your existing URLs
    path('products/<str:firebase_user_id>/', ProductListAPIView.as_view()),
    path('fetch_customer/', CustomerListAPIView.as_view(), name='fetch_customer'),
    path('categories/', ProductCategoryListAPIView.as_view()),
    path('exchange_rate/<str:name>/', exchange_rate_view, name='exchange_rate'),
    path('Add_products/<str:firebase_id>/', create_product, name='product-create'),
    path('create_transaction/', CreateTransactionView.as_view(), name='create_transaction'),
    path('categories/', CategoryList.as_view(), name='category-list'),
    path('low_stock/<str:firebase_id>/', low_stock_products, name='low-stock-products'),
    path('update_products/<int:id>/', update_product, name='update-product'),
    path('products/<int:id>/delete/', delete_product, name='delete-product'),
    path('transfer_stock/<int:product_id>/', transfer_stock, name='transfer-stock'),
    path('update_profile/<str:firebase_id>/', cashier_profile, name='cashier-profile'),
    path('categories/', list_categories, name='list-categories'),
    path('branches/<str:firebase_user_id>/', list_branches, name='list-branches'),
    path('company/', CompanyDetailAPIView.as_view(), name='company-detail'),
    path('suppliers/<str:firebase_id>/', get_suppliers, name='get_suppliers'),
    path('suppliers/<str:firebase_id>/create/', create_supplier, name='create_supplier'),
    path('suppliers/<str:firebase_id>/<int:supplier_id>/update/', update_supplier, name='update_supplier'),
    path('getbranches/<str:firebase_id>/', get_branches, name='get_branches'),

    path('purchase-orders/<str:firebase_id>/', get_purchase_orders, name='get_purchase_orders'),
    path('purchase-orders/create/<str:firebase_id>/', create_purchase_order, name='create_purchase_order'),
    path('purchase-orders/detail/<int:pk>/<str:firebase_id>/', get_purchase_order_detail,
         name='get_purchase_order_detail'),
    path('purchase-orders/delete/<int:pk>/<str:firebase_id>/', delete_purchase_order, name='delete_purchase_order'),
    path('purchase-orders/pdf/<int:pk>/<str:firebase_id>/', generate_purchase_order_pdf,
         name='generate_purchase_order_pdf'),

    path(
        'purchase-orders/update/<int:po_id>/<str:firebase_id>/',
        update_purchase_order,
        name='update-purchase-order'
    ),
]