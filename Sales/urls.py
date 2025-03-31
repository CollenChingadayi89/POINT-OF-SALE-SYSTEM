from django.urls import path
from .views import *
from .views import CreateTransactionView
urlpatterns = [
    path('products/<str:firebase_user_id>/', ProductListAPIView.as_view()),

    path('fetch_customer/', CustomerListAPIView.as_view(), name='fetch_customer'),
    path('categories/', ProductCategoryListAPIView.as_view()),
    path('exchange_rate/<str:name>/', exchange_rate_view, name='exchange_rate'),

    path('Add_products/<str:firebase_id>/', create_product, name='product-create'),

    # path("create_transaction/", CreateTransactionView.as_view(), name="create-transaction"),

    # path('create_transaction/', create_transaction, name='create_transaction'),

    path('create_transaction/', CreateTransactionView.as_view(), name='create_transaction'),

    path('categories/', CategoryList.as_view(), name='category-list'),

    path('low_stock/<str:firebase_id>/', low_stock_products, name='low-stock-products'),

    # ----------------------------------------------

    path('update_products/<int:id>/', update_product, name='update-product'),
    path('products/<int:id>/delete/', delete_product, name='delete-product'),
    
    # Stock transfer
    path('transfer_stock/<int:product_id>/', transfer_stock, name='transfer-stock'),

   path('update_profile/<str:firebase_id>/', cashier_profile, name='cashier-profile'),
    
    # Lists
    path('categories/', list_categories, name='list-categories'),
    path('branches/<str:firebase_user_id>/', list_branches, name='list-branches'),
]


