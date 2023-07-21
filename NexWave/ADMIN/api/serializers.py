from rest_framework import serializers
from ADMIN.models import RechargePlan, PlanCategory,Subscription,Chat_Option,Notifications

class PlanCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanCategory
        fields = '__all__'

    def create(self, validated_data):
        # Perform data validation here
        # For example, check if a category with the same name already exists
        category_name = validated_data.get('name')
        if PlanCategory.objects.filter(name=category_name).exists():
            raise serializers.ValidationError("A category with this name already exists.")

        # Create and save the RechargePlancategory
        plan_category = PlanCategory.objects.create(**validated_data)
        return plan_category

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargePlan
        fields = ['id', 'name', 'data_limit', 'voice_limit', 'sms_limit', 'price', 'category','validity']

    def create(self, validated_data):
        # Perform data validation here
        # For example, check if a RechargePlanwith the same name already exists
        plan_name = validated_data.get('name')
        if RechargePlan.objects.filter(name=plan_name).exists():
            raise serializers.ValidationError("A RechargePlanwith this name already exists.")
        
        # Get the category and remove it from validated_data
        category = validated_data.pop('category')
        
        # Find the corresponding PlanCategory instance by its ID
        category_id = PlanCategory.objects.get(id=category.id)
        
        # Create and save the plan
        Plan= RechargePlan.objects.create(category=category_id, **validated_data)
        return Plan

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer() 
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'start_date', 'end_date', 'is_active', 'billing_info']

class ChatOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat_Option
        fields = '__all__'
        
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = '__all__'