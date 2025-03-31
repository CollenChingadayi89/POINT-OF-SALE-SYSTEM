from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.contrib.auth.models import User
from .serializers import CustomUserSerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import CustomUser
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view,permission_classes
from .models import AdminProfile, CashierProfile, CustomerProfile, CustomUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes



class RegisterUserAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        print(data)
        try:
            with transaction.atomic():
                email = data.get('email')
                password = data.get('password')  # Ensure password is in the request data
                role = data.get('role')
                firebase_user_id=data.get('firebase_user_id')
                full_name=data.get('first_name'),


                # Validate role
                if role not in ["admin", "cashier", "manager", "customer"]:
                    return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

                # Create the user
                user_serializer = CustomUserSerializer(data=data)
                user_serializer.is_valid(raise_exception=True)
                user = user_serializer.save()  # Password is hashed in the serializer

                user.set_password(password)
                user.save()

                # Create the profile based on role
                if role == "admin":
                    AdminProfile.objects.create(user=user)
                elif role == "cashier":
                    CashierProfile.objects.create(user=user,
                                                  firebase_user=firebase_user_id,
                                                  full_name=full_name
                                                  
                                                  )
                # elif role == "manager":
                #     ManagerProfile.objects.create(user=user)
                elif role == "customer":
                    CustomerProfile.objects.create(user=user)

                # Generate token for the user
                token, _ = Token.objects.get_or_create(user=user)

                return Response({
                    "message": "User created successfully!",
                    "token": token.key,
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
def get_user_role(request, firebase_user_id):
    try:
        # Fetch the user object
        user = CustomUser.objects.get(firebase_user_id=firebase_user_id)

        # Get or create the token for the user
        token, created = Token.objects.get_or_create(user=user)

        # Return the user data and token without serializer
        response_data = {
            'id': user.id,
            'firebase_user_id': user.firebase_user_id,
            'email': user.email,
            'first_name':user.first_name,
            'role': user.role,
            'phone_number': user.phone_number,
            'token': token.key  # Returning the token
        }

        return Response(response_data, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_my_role(request, firebase_user_id):
    try:
        # Fetch the user object
        user = CustomerProfile.objects.get(firebase_user_id=firebase_user_id)

        # Get or create the token for the user
        token, created = Token.objects.get_or_create(user=user)

        # Return the user data and token without serializer
        response_data = {
            'id': user.id,
            'firebase_user_id': user.firebase_user_id,
            'email': user.email,
            'first_name':user.first_name,
            'role': user.role,
            'phone_number': user.phone_number,
            'token': token.key  # Returning the token
        }

        return Response(response_data, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)