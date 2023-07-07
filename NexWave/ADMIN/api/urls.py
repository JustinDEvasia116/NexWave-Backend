from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('', views.RoutesAPIView.as_view(), name='available-routes'),
    path('pending-connections/', views.PendingConnectionsView.as_view(), name='pending-connections'),   
    path('pending-connections/<int:pk>/actions/',views.TakeActionView.as_view(), name='pending-connections-actions'),
    path('plan-categories/add/', views.PlanCategoryCreateAPIView.as_view(), name='plan-category-create'),
    path('admin-token/', views.MyTokenObtainPairView.as_view(), name='admin-token-obtain'),
    path('admin-token/refresh/', TokenRefreshView.as_view(), name='admin-token-refresh'),
    path('plans/create/', views.PlanCreateView.as_view(), name='plan-create'),
    path('subscriptions/create/', views.SubscriptionCreateView.as_view(), name='subscription-create'),
    path('recharge-plans/', views.RechargePlanListView.as_view(), name='recharge-plan-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription-list'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('chat-options/', views.OptionListAPIView.as_view(), name='option-list'),
    path('options/<int:parent_id>/child/', views.CreateOptionAPIView.as_view(), name='child-option'),
    path('options/menu/', views.OptionMenuAPIView.as_view(), name='option-menu'),
    
]
