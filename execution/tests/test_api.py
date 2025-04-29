from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from decimal import Decimal

from execution.models import (
    ServiceProvider,
    AccountManager,
    Customer,
    Service,
    Order
)

class ServiceProviderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.service_provider_data = {
            'name': 'Test Provider',
            'description': 'Test Description',
            'contact_email': 'test@provider.com',
            'contact_phone': '+1234567890'
        }

    def test_create_service_provider(self):
        url = reverse('serviceprovider-list')
        response = self.client.post(url, self.service_provider_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceProvider.objects.count(), 1)
        self.assertEqual(ServiceProvider.objects.get().name, 'Test Provider')

    def test_get_service_providers(self):
        ServiceProvider.objects.create(**self.service_provider_data)
        url = reverse('serviceprovider-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class CustomerAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.account_manager = AccountManager.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.customer_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'account_manager': self.account_manager.id
        }

    def test_create_customer(self):
        url = reverse('customer-list')
        response = self.client.post(url, self.customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(Customer.objects.get().email, 'john@example.com')

    def test_get_customers(self):
        Customer.objects.create(**self.customer_data)
        url = reverse('customer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class OrderAPITests(APITestCase):
    def setUp(self):
        # Create user and authenticate
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.account_manager = AccountManager.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

        # Create customer
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            account_manager=self.account_manager
        )

        # Create service provider and service
        self.service_provider = ServiceProvider.objects.create(
            name='Test Provider',
            contact_email='test@provider.com'
        )
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Description',
            service_provider=self.service_provider,
            price=Decimal('99.99')
        )

        self.order_data = {
            'customer': self.customer.id,
            'order_number': 'ORD-001',
            'total_amount': '99.99',
            'status': 'PENDING',
            'services': [{'service': self.service.id, 'quantity': 1}]
        }

    def test_create_order(self):
        url = reverse('order-list')
        response = self.client.post(url, self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().order_number, 'ORD-001')

    def test_get_orders(self):
        order = Order.objects.create(
            customer=self.customer,
            order_number='ORD-001',
            total_amount=Decimal('99.99'),
            status='PENDING'
        )
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_order_process_endpoint(self):
        order = Order.objects.create(
            customer=self.customer,
            order_number='ORD-001',
            total_amount=Decimal('99.99'),
            status='PENDING'
        )
        url = reverse('order-process', kwargs={'pk': order.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Processing started') 