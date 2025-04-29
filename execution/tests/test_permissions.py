from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from execution.models import (
    ServiceProvider,
    AccountManager,
    Customer,
    Order,
    Service
)

class OrderPermissionTests(APITestCase):
    def setUp(self):
        # Create two account managers
        self.manager1 = User.objects.create_user(
            username='manager1',
            password='testpass123'
        )
        self.manager2 = User.objects.create_user(
            username='manager2',
            password='testpass123'
        )
        self.account_manager1 = AccountManager.objects.create(user=self.manager1)
        self.account_manager2 = AccountManager.objects.create(user=self.manager2)

        # Create service provider and associate with manager1
        self.service_provider = ServiceProvider.objects.create(
            name='Test Provider',
            contact_email='test@provider.com'
        )
        self.account_manager1.service_providers.add(self.service_provider)

        # Create customers for each manager
        self.customer1 = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            account_manager=self.account_manager1
        )
        self.customer2 = Customer.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            account_manager=self.account_manager2
        )

    def test_manager_can_only_see_own_customer_orders(self):
        # Create orders for both customers
        order1 = Order.objects.create(
            customer=self.customer1,
            order_number='ORD-001',
            total_amount=100.00,
            status='PENDING'
        )
        order2 = Order.objects.create(
            customer=self.customer2,
            order_number='ORD-002',
            total_amount=200.00,
            status='PENDING'
        )

        # Test manager1's access
        self.client.force_authenticate(user=self.manager1)
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['order_number'], 'ORD-001')

        # Test manager2's access
        self.client.force_authenticate(user=self.manager2)
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['order_number'], 'ORD-002')

    def test_manager_cannot_access_other_customers(self):
        self.client.force_authenticate(user=self.manager1)
        response = self.client.get(f'/api/customers/{self.customer2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_can_only_use_own_service_providers(self):
        # Create a service from the service provider
        service = Service.objects.create(
            name='Test Service',
            service_provider=self.service_provider,
            price=100.00
        )

        # Try to create order with service for customer2 (different manager)
        self.client.force_authenticate(user=self.manager2)
        order_data = {
            'customer': self.customer2.id,
            'services': [{'service': service.id, 'quantity': 1}],
            'total_amount': 100.00
        }
        response = self.client.post('/api/orders/', order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class AnonymousUserTests(APITestCase):
    def test_anonymous_user_access(self):
        # Try accessing endpoints without authentication
        endpoints = [
            '/api/customers/',
            '/api/orders/',
            '/api/service-providers/',
            '/api/services/'
        ]
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ServiceProviderPermissionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='manager',
            password='testpass123',
            is_staff=False
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )

    def test_only_admin_can_create_service_provider(self):
        data = {
            'name': 'New Provider',
            'contact_email': 'new@provider.com'
        }

        # Test regular user access
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/service-providers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test admin access
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/service-providers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) 