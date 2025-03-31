from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterUserAPIView , get_user_role

urlpatterns = [
    # User registration
    path('register/', RegisterUserAPIView.as_view(), name='register'),

    # Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('get_user_role/<str:firebase_user_id>/', get_user_role, name='get_user_role'),
]
