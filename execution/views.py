from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status

from .models import Customer, Order, Job, ServiceProvider, Service, OrderService
from .serializers import (
    CustomerSerializer,
    OrderSerializer,
    JobSerializer,
    ServiceProviderSerializer,
    ServiceSerializer,
    UserRegistrationSerializer
)
from .permissions import IsAdminOrReadOnly, IsAccountManagerOrAdmin

from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing service providers."""
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [IsAdminOrReadOnly]


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing services."""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrReadOnly]


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for managing customers."""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAccountManagerOrAdmin]

    def get_queryset(self):
        """Filter customers based on account manager."""
        if self.request.user.is_staff:
            return Customer.objects.all()
        return Customer.objects.filter(account_manager__user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing orders."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAccountManagerOrAdmin]

    def get_queryset(self):
        """Filter orders based on account manager."""
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(customer__account_manager__user=self.request.user)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process an order by creating necessary jobs."""
        order = self.get_object()
        
        # Check if order can be processed
        if order.status not in ['PENDING']:
            return Response(
                {'error': f'Cannot process order in {order.status} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update order status
            order.status = 'PROCESSING'
            order.save()
            
            # Create processing job
            processing_job = Job.objects.create(
                order=order,
                job_id=f"JOB-{order.id}-P",
                job_name=f"Processing job for Order {order.order_number}",
                job_type='PROCESSING',
                status='PENDING'
            )
            
            # Create shipping job
            shipping_job = Job.objects.create(
                order=order,
                job_id=f"JOB-{order.id}-S",
                job_name=f"Shipping job for Order {order.order_number}",
                job_type='SHIPPING',
                status='PENDING'
            )
            
            return Response({
                'status': 'Processing started',
                'order_status': order.status,
                'jobs_created': [
                    {'id': processing_job.job_id, 'type': 'processing'},
                    {'id': shipping_job.job_id, 'type': 'shipping'}
                ]
            })
            
        except Exception as e:
            # Rollback order status if job creation fails
            order.status = 'PENDING'
            order.save()
            return Response(
                {'error': f'Failed to create jobs: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobViewSet(viewsets.ModelViewSet):
    """ViewSet for managing jobs."""
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAccountManagerOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_queryset(self):
        """Filter jobs based on account manager."""
        if self.request.user.is_staff:
            return Job.objects.all()
        return Job.objects.filter(order__customer__account_manager__user=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a job."""
        job = self.get_object()
        job.start()
        return Response({'status': 'job started'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a job."""
        job = self.get_object()
        job.complete()
        return Response({'status': 'job completed'})

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Fail a job."""
        job = self.get_object()
        error_message = request.data.get('error_message', 'Job failed without specific error message')
        job.fail(error_message)
        return Response({'status': 'job failed', 'error_message': error_message})


class UserRegistrationView(generics.CreateAPIView):
    """View for user registration."""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer


def trigger_error(request):
    division_by_zero = 1 / 0
    return division_by_zero
