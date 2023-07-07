from rest_framework import serializers
from ..models import User, Connections
from django.contrib.auth import get_user_model
from ..models import Connections, Address
from django.contrib.auth.hashers import make_password
import uuid
from ADMIN.models import *
from ADMIN.api.serializers import PlanSerializer,SubscriptionSerializer

User = get_user_model()

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['street', 'city', 'state', 'zip_code']



class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['street', 'city', 'state', 'zip_code']

class UserSerializer(serializers.ModelSerializer):
    active_subscription = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'active_subscription', 'mob_number', 'user_address','is_active']

    def get_active_subscription(self, user):
        subscription = self.context.get('subscription')
        recharge_plan = self.context.get('recharge_plan')

       
        subscription_data = SubscriptionSerializer(subscription).data
        recharge_plan_data = PlanSerializer(recharge_plan).data
        subscription_data['plan'] = recharge_plan_data
        return subscription_data

        

class ConnectionSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    user = UserSerializer(read_only=True)

    class Meta:
        model = Connections
        fields = ['mob_number', 'connection_type', 'address', 'profile_name', 'id', 'user']

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        
        profile_name = validated_data.pop('profile_name')

        # Create a new user with a random username and default password
        username = f'new_connection_{uuid.uuid4().hex[:6]}'
        password = make_password(None)  # Generate a default password
        user = User.objects.create(username=username, password=password,is_active=False,)
        address = Address.objects.create(**address_data,user=user)

        # Create the connection instance and assign the user
        connection = Connections.objects.create(address=address, profile_name=profile_name, user=user, **validated_data)
        
        return connection
    
class GenerateOTPSerializer(serializers.Serializer):
    mob_number = serializers.CharField(max_length=20)
    
class VerifyOTPSerializer(serializers.Serializer):
    mob_number = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6)
    

