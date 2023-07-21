from django.http import JsonResponse
from rest_framework.exceptions import NotFound
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
from django.db.models import Count


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
        




# class UserDetailsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user_id = request.user.id
#         user = User.objects.get(id=user_id)

#         serializer = UserSerializer(user)
#         return JsonResponse(serializer.data)
 
class UserDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            serializer = UserSerializer(user, context={'request': request})
            data = serializer.data

            active_subscription = serializer.get_active_subscription(user)
            

            if active_subscription:
                recharge_plan_id = active_subscription['plan']
                # recharge_plan = RechargePlan.objects.get(id=recharge_plan_id)
                plan_serializer = recharge_plan_id
                data['active_subscription'] = active_subscription
                data['active_subscription']['plan'] = plan_serializer

            # data['recharge_history'] = recharge_history

            return Response(data)
        
        except User.DoesNotExist:
            return Response({'error': 'User does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    
class SubscriptionCreateAPIView(APIView):
    def post(self, request):
        # Retrieve the data from the request
        recharge_plan_id = request.data.get('recharge_plan_id')
        user_id = request.data.get('user')

        # Validate the data
        if not recharge_plan_id:
            return Response({'error': 'Recharge plan ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the selected recharge plan
            recharge_plan = RechargePlan.objects.get(id=recharge_plan_id)

            # Calculate the start and end dates
            start_date = date.today()
            end_date = start_date + timedelta(days=recharge_plan.validity)

            # Retrieve the current user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise NotFound("User not found")

            # Check if the user has an active subscription
            existing_subscription = Subscription.objects.filter(user=user, is_active=True).first()

            # Create the subscription
            if existing_subscription:
                is_active = False
            else:
                is_active = start_date <= date.today() <= end_date

            subscription = Subscription.objects.create(
                user=user,
                plan=recharge_plan,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                billing_info='',
            )
            # Serialize the subscription data
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except RechargePlan.DoesNotExist:
            raise NotFound("Invalid recharge plan ID")

@api_view(['GET'])
def recommended_plans(request):
    user = request.user.id

    # Group subscriptions by plan ID and count how many times each plan appears
    subscribed_plans_count = Subscription.objects.filter(user=user) \
        .values('plan') \
        .annotate(subscription_count=Count('plan'))

    # Sort the plans in descending order of subscription count
    sorted_plans = sorted(subscribed_plans_count, key=lambda x: x['subscription_count'], reverse=True)

    # Retrieve the top two most subscribed plans
    top_two_plans = sorted_plans[:2]

    # Get the plan IDs of the top two plans
    top_two_plan_ids = [plan['plan'] for plan in top_two_plans]

    # Fetch the RechargePlan objects corresponding to the top two plan IDs
    recommended_plans = RechargePlan.objects.filter(id__in=top_two_plan_ids)

    # Serialize the data
    serializer = PlanSerializer(recommended_plans, many=True)

    return Response(serializer.data)
