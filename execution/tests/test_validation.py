from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from execution.models import (
    ServiceProvider,
    AccountManager,
    Customer,
    Service,
    Order,
    OrderService
)

class CustomerValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testmanager')
        self.account_manager = AccountManager.objects.create(user=self.user)

    def test_email_validation(self):
        # Test invalid email
        with self.assertRaises(ValidationError):
            customer = Customer(
                first_name='John',
                last_name='Doe',
                email='invalid-email',
                account_manager=self.account_manager
            )
            customer.full_clean()

    def test_phone_validation(self):
        # Test invalid phone number
        with self.assertRaises(ValidationError):
            customer = Customer(
                first_name='John',
                last_name='Doe',
                email='john@example.com',
                phone='123',  # Too short
                account_manager=self.account_manager
            )
            customer.full_clean()

class OrderValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testmanager')
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

    def test_negative_total_amount(self):
        with self.assertRaises(ValidationError):
            order = Order(
                customer=self.customer,
                order_number='ORD-001',
                total_amount=Decimal('-100.00'),
                status='PENDING'
            )
            order.full_clean()

    def test_invalid_status(self):
        with self.assertRaises(ValidationError):
            order = Order(
                customer=self.customer,
                order_number='ORD-001',
                total_amount=Decimal('100.00'),
                status='INVALID_STATUS'
            )
            order.full_clean()

    def test_duplicate_order_number(self):
        Order.objects.create(
            customer=self.customer,
            order_number='ORD-001',
            total_amount=Decimal('100.00'),
            status='PENDING'
        )
        with self.assertRaises(ValidationError):
            order = Order(
                customer=self.customer,
                order_number='ORD-001',  # Duplicate
                total_amount=Decimal('200.00'),
                status='PENDING'
            )
            order.full_clean()

class ServiceValidationTests(TestCase):
    def setUp(self):
        self.service_provider = ServiceProvider.objects.create(
            name="Test Provider",
            contact_email="test@provider.com"
        )

    def test_negative_price(self):
        service = Service(
            name="Test Service",
            description="Test Description",
            service_provider=self.service_provider,
            price=Decimal("-10.00")
        )
        with self.assertRaises(ValidationError):
            service.full_clean()

    def test_zero_price(self):
        service = Service(
            name="Free Service",
            description="A free service for testing",
            service_provider=self.service_provider,
            price=Decimal("0.00")
        )
        service.full_clean()  # Should not raise ValidationError

class OrderServiceValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testmanager')
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
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='ORD-001',
            total_amount=Decimal('100.00'),
            status='PENDING'
        )

    def test_negative_quantity(self):
        with self.assertRaises(ValidationError):
            order_service = OrderService(
                order=self.order,
                service=self.service,
                quantity=-1,
                price_at_time=Decimal('100.00')
            )
            order_service.full_clean()

    def test_zero_quantity(self):
        with self.assertRaises(ValidationError):
            order_service = OrderService(
                order=self.order,
                service=self.service,
                quantity=0,
                price_at_time=Decimal('100.00')
            )
            order_service.full_clean()

    def test_negative_price_at_time(self):
        with self.assertRaises(ValidationError):
            order_service = OrderService(
                order=self.order,
                service=self.service,
                quantity=1,
                price_at_time=Decimal('-100.00')
            )
            order_service.full_clean() 