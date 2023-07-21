from rest_framework import generics, permissions
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from django.contrib.auth.decorators import login_required, permission_required
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAdminUser ,AllowAny, IsAuthenticated
from rest_framework.views import APIView

from django.utils.decorators import method_decorator
from rest_framework import status,viewsets
from rest_framework.response import Response
from USER.api.serializers import *
from ADMIN.api.serializers import *
from USER.models import *
from ADMIN.models import *
from .twilio_utils import MessageHandler
from django.contrib.auth import get_user_model



from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
User = get_user_model()
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        if user.is_superuser:
            token['is_admin'] = True

        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer




class PendingConnectionsView(generics.ListAPIView):
    serializer_class = ConnectionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Connections.objects.filter(user__is_active=False)
    
class TakeActionView(UpdateAPIView):
    serializer_class = ConnectionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self):
        pk = self.kwargs.get('pk')
        obj = Connections.objects.filter(pk=pk, user__is_active=False).first()
        return obj

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        approved = request.data.get('approved', None)
        if approved is not None:
            if approved == 'true':
                mob_number = instance.mob_number
                instance.user.username = instance.mob_number
                instance.user.mob_number = instance.mob_number
                instance.user.user_address = instance.address
                instance.user.is_active = True
                instance.user.save()                
                body = f"Your account with Nexwave is now active! Welcome aboard!"
                message_handler = MessageHandler(mob_number,body).sent_activation_sms()
                # send_sms(instance.mob_number, body)
                instance.delete()
                return Response({'detail': 'Connection request approved.'})
            elif approved == 'false':
                adress = Address.objects.filter(id=instance.address.id)
                instance.delete()
                adress.delete()
                return Response({'detail': 'Connection request rejected.'})
        return Response({'detail': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)

class PlanCategoryCreateAPIView(CreateAPIView):
    serializer_class = PlanCategorySerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        # Perform any additional logic or data validation here
        serializer.save()
from .serializers import PlanSerializer, SubscriptionSerializer

class PlanCreateView(APIView):
    def post(self, request, format=None):
        serializer = PlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SubscriptionCreateView(APIView):
    def post(self, request, format=None):
        serializer = SubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user  # Assuming you're using token-based authentication or session-based authentication
        existing_subscription = Subscription.objects.filter(user=user, is_active=True).first()

        if existing_subscription:
            serializer.save(user=user)
        else:
            serializer.save(user=user, is_active=True)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RoutesAPIView(APIView):
    def get(self, request):
        routes = [
            '/admins/pending-connections/',
            '/admins/pending-connections/<int:pk>/actions/',
            '/admins/plan-categories/add/',
            '/admins/plans/add/',
        ]
        return Response(routes)

class RechargePlanListView(generics.ListAPIView):
    # permission_classes = [IsAuthenticated]   # Authorization required
    queryset = RechargePlan.objects.all()
    serializer_class = PlanSerializer
   

class CategoryListView(generics.ListAPIView):
    # permission_classes = [IsAuthenticated]  # Authorization required
    queryset = PlanCategory.objects.all()
    serializer_class = PlanCategorySerializer
  

class SubscriptionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]  # Authorization required
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer    

class OptionListAPIView(APIView):
    def get(self, request):
        options = Chat_Option.objects.all()
        serializer = ChatOptionSerializer(options, many=True)
        return Response(serializer.data)

class CreateOptionAPIView(APIView):
    def post(self, request, parent_id):
        parent_option = Chat_Option.objects.get(pk=parent_id)
        serializer = ChatOptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(parent_option=parent_option)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OptionMenuAPIView(APIView):
    def get(self, request):
        option_id = request.query_params.get('option_id')
        try:
            parent_option = Chat_Option.objects.get(pk=option_id)
            sub_options = Chat_Option.objects.filter(parent_option=parent_option)
            serializer = ChatOptionSerializer(sub_options, many=True)
            return Response(serializer.data)
        except Chat_Option.DoesNotExist:
            return Response({'error': 'Option not found.'}, status=404)
        
class NotificationViewsets(viewsets.ModelViewSet):
    queryset= Notifications.objects.all()
    serializer_class = NotificationSerializer
    
    @action(methods =['POST'],detail= True)
    def send_notification(self,request,pk):
        notification = self.get_object()