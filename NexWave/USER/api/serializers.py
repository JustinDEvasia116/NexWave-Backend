from rest_framework import serializers
from ..models import User, Connections
from django.contrib.auth import get_user_model
from ..models import Connections, Address
from django.contrib.auth.hashers import make_password
import uuid
from ADMIN.models import *
from ADMIN.api.serializers import PlanSerializer,SubscriptionSerializer
from django.utils import timezone
from django.db import transaction

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
    subscription_history = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'mob_number', 'user_address','is_active','active_subscription','subscription_history']

   
    def get_active_subscription(self, user):
        now = timezone.now()
        active_subscription = Subscription.objects.filter(user=user, start_date__lte=now, end_date__gte=now).first()

        if active_subscription:
            user.active_subscription = active_subscription
            user.save()

        serializer = SubscriptionSerializer(active_subscription)
        return serializer.data if active_subscription else None

    def get_subscription_history(self, user):
        subscriptions = Subscription.objects.filter(user=user)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return serializer.data
        

class ConnectionSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    user = UserSerializer(read_only=True)
    document_file_url = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Connections
        fields = ['mob_number', 'connection_type', 'address', 'profile_name', 'id', 'user', 'document_file', 'photo', 'document_file_url', 'photo_url']
        

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        profile_name = validated_data.pop('profile_name')
        document_file = validated_data.pop('document_file', None)
        photo = validated_data.pop('photo', None)

        # Create a new user with a random username and default password
        username = f'new_connection_{uuid.uuid4().hex[:6]}'
        password = make_password(None)  # Generate a default password
        user = User.objects.create(username=username, password=password, is_active=False)
        address = Address.objects.create(**address_data,user=user)
        # Create the connection instance and assign the user
        connection = Connections.objects.create(address=address, profile_name=profile_name, user=user, **validated_data)

       
        

        # Store the document_file and photo if provided
        if document_file:
            connection.document_file.save(document_file.name, document_file, save=True)
        if photo:
            connection.photo.save(photo.name, photo, save=True)

        return connection
    
    def get_document_file_url(self, obj):
        if obj.document_file:
            return obj.document_file.url
        return None
    
    def get_photo_url(self, obj):
        if obj.photo:
            return obj.photo.url
        return None
    
class GenerateOTPSerializer(serializers.Serializer):
    mob_number = serializers.CharField(max_length=20)
    
class VerifyOTPSerializer(serializers.Serializer):
    mob_number = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6)
    

