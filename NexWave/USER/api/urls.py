from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import TokenObtainPairWithMobNumberView
from django.conf.urls.static import static
from django.conf import settings

from rest_framework_simplejwt.views import (
   
    TokenRefreshView,
)

urlpatterns = [
    path('',views.getRoutes),
    # path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('token/', TokenObtainPairWithMobNumberView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('connections/create/', views.ConnectionCreateView.as_view(), name='connection-create'),
    path('generate-otp/', views.GenerateOTPView.as_view(), name='generate-otp'),
    path('user-login/', views.UserLoginView.as_view() , name='user-login'),
    path('user-details/', views.UserDetailsAPIView.as_view(), name='user-details'),
    path('create-subscription/', views.SubscriptionCreateAPIView.as_view(), name='create-subscription'),
    path('recommended_plans/', views.recommended_plans, name='recommended_plans'),
        
]
