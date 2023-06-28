from django.http import JsonResponse

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


from ..models import Connections
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from ..models import OTP
from .twilio_utils import *
import random
from .serializers import *
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token
import paypalrestsdk
from paypalrestsdk import Payment

class TokenObtainPairWithMobNumberSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        connections_instance = user
        if connections_instance:
            token['mob_number'] = connections_instance.username
        return token


class TokenObtainPairWithMobNumberView(TokenObtainPairView):
    serializer_class = TokenObtainPairWithMobNumberSerializer


class ConnectionCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = ConnectionSerializer(data=request.data)
        if serializer.is_valid():
            connection = serializer.save()

        # Send a notification to the admin group
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'admin',  # Group name
                {
                    'type': 'notification',
                    'message': f"New connection created: {connection.id}",
                }
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def getRoutes(request):
    routes = [
        '/api/token',
        '/api/token/refresh',
        '/api/signup',
        '/api/connections/create/',
        '/admins/pending-connections/'
    ]
    return Response(routes)


class GenerateOTPView(APIView):
    def post(self, request, format=None):
        serializer = GenerateOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        mob_number = validated_data.get('mob_number')
        # Generate OTP
        try:
            user = User.objects.get(username=mob_number)
        except User.DoesNotExist:
            return JsonResponse({'message': 'User does not exist'})

        # Generate a random 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Save the OTP in the database
        otp_obj, created = OTP.objects.get_or_create(user=user)
        otp_obj.otp = otp
        otp_obj.save()

        # Send the OTP to the user's phone using Twilio
        body = f"Your OTP is: {otp}"
        message_handler = MessageHandler(
            mob_number, body).sent_activation_sms()

        return JsonResponse({'message': 'OTP sent successfully'})


class UserLoginView(APIView):
    def post(self, request, format=None):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        mob_number = validated_data.get('mob_number')
        entered_otp = validated_data.get('otp')

        try:
            user = User.objects.get(username=mob_number)
            username = user.username
        except User.DoesNotExist:
            return JsonResponse({'message': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = OTP.objects.get(user=user)
            databaseotp = otp_obj.otp
        except OTP.DoesNotExist:
            return JsonResponse({'message': 'OTP does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        if entered_otp == databaseotp:
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token.payload['username'] = mob_number
            access_token.payload['is_user'] = True
            response_data = {
            'access': str(access_token),
            'refresh': str(refresh),
            }
            return JsonResponse(response_data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({'message': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        




class UserDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)

        serializer = UserSerializer(user)
        return JsonResponse(serializer.data)
 
class UserDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)

        try:
            subscription = user.active_subscription
            recharge_plan = subscription.plan
        except Subscription.DoesNotExist:
            subscription = None
            recharge_plan = None

        serializer = UserSerializer(user, context={'request': request})  # Pass the request instead of individual objects
        data = serializer.data

        if subscription and recharge_plan:
            subscription_serializer = SubscriptionSerializer(subscription)
            recharge_plan_serializer = PlanSerializer(recharge_plan)
            data['active_subscription'] = subscription_serializer.data
            data['active_subscription']['plan'] = recharge_plan_serializer.data

        return Response(data)


    
class SubscriptionCreateAPIView(APIView):
    def post(self, request):
        # Retrieve the data from the request
        recharge_plan_id = request.data.get('recharge_plan_id')
        
        # Validate the data
        if not recharge_plan_id :
            return Response({'error': 'Recharge plan ID and Recharge ID are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the selected recharge plan
            recharge_plan = RechargePlan.objects.get(id=recharge_plan_id)

            # Calculate the start and end dates
            start_date = date.today()
            end_date = start_date + timedelta(days=recharge_plan.validity)

            # Create the subscription
            subscription = Subscription.objects.create(
                plan=recharge_plan,
                start_date=start_date,
                end_date=end_date,
                is_active=start_date <= date.today() <= end_date,
                billing_info='',
            )

            # Serialize the subscription data
            serializer = SubscriptionSerializer(subscription)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except RechargePlan.DoesNotExist:
            return Response({'error': 'Invalid recharge plan ID'}, status=status.HTTP_400_BAD_REQUEST)