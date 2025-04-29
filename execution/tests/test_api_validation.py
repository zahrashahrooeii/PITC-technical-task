from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from execution.models import (
    ServiceProvider,
    AccountManager,
    Customer,
    Service,
    Order
)

class CustomerAPIValidationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testmanager', password='testpass')
        self.account_manager = AccountManager.objects.create(user=self.user)
        self.client.login(username='testmanager', password='testpass')

    def test_create_customer_invalid_data(self):
        # Missing required fields
        response = self.client.post('/api/customers/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        self.assertIn('email', response.data)

        # Invalid email
        response = self.client.post('/api/customers/', {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

class OrderAPIValidationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testmanager', password='testpass')
        self.account_manager = AccountManager.objects.create(user=self.user)
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            account_manager=self.account_manager
        )
        self.service_provider = ServiceProvider.objects.create(
            name='Test Provider',
            contact_email='test@provider.com'
        )
        self.service = Service.objects.create(
            name='Test Service',
            service_provider=self.service_provider,
            price=Decimal('100.00')
        )
        self.client.login(username='testmanager', password='testpass')

    def test_create_order_invalid_data(self):
        # Missing required fields
        response = self.client.post('/api/orders/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer', response.data)
        self.assertIn('order_number', response.data)

        # Invalid customer ID
        response = self.client.post('/api/orders/', {
            'customer': 999,  # Non-existent customer
            'order_number': 'ORD-001',
            'total_amount': '100.00',
            'status': 'PENDING'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('customer', response.data)

        # Invalid status
        response = self.client.post('/api/orders/', {
            'customer': self.customer.id,
            'order_number': 'ORD-001',
            'total_amount': '100.00',
            'status': 'INVALID_STATUS'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

class ServiceAPIValidationTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )
        self.service_provider = ServiceProvider.objects.create(
            name='Test Provider',
            contact_email='test@provider.com'
        )
        self.client.login(username='admin', password='adminpass')

    def test_create_service_invalid_data(self):
        # Missing required fields
        response = self.client.post('/api/services/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('service_provider', response.data)
        self.assertIn('price', response.data)

        # Invalid price format
        response = self.client.post('/api/services/', {
            'name': 'Test Service',
            'service_provider': self.service_provider.id,
            'price': 'invalid_price'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)

        # Negative price
        response = self.client.post('/api/services/', {
            'name': 'Test Service',
            'service_provider': self.service_provider.id,
            'price': '-100.00'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data) 