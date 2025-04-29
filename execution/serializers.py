from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Customer, Order, Job, ServiceProvider, Service, OrderService


class ServiceProviderSerializer(serializers.ModelSerializer):
    """Serializer for the ServiceProvider model."""
    class Meta:
        model = ServiceProvider
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for the Service model."""
    service_provider_name = serializers.ReadOnlyField(source='service_provider.name')
    class Meta:
        model = Service
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for the Customer model."""
    account_manager_email = serializers.ReadOnlyField(source='account_manager.user.email')
    class Meta:
        model = Customer
        fields = '__all__'


class OrderServiceSerializer(serializers.ModelSerializer):
    """Serializer for the OrderService model."""
    service_name = serializers.ReadOnlyField(source='service.name')
    class Meta:
        model = OrderService
        fields = ['id', 'service', 'service_name', 'quantity', 'price_at_time']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for the Order model."""
    customer_name = serializers.SerializerMethodField()
    services_detail = OrderServiceSerializer(source='orderservice_set', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_name', 'order_number', 'services_detail', 'total_amount', 'status', 'notes', 'created_at', 'updated_at']

    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"


class JobSerializer(serializers.ModelSerializer):
    """Serializer for the Job model."""
    order_numbers = serializers.SerializerMethodField()
    service_provider_name = serializers.ReadOnlyField(source='service_provider.name')
    job_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = '__all__'

    def get_order_numbers(self, obj):
        return [order.order_number for order in obj.orders.all()]

    def get_job_type_display(self, obj):
        return obj.get_job_type_display()

    def get_status_display(self, obj):
        return obj.get_status_display()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user 