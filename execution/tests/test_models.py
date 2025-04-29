from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

from execution.models import (
    ServiceProvider,
    AccountManager,
    Customer,
    Service,
    Order,
    OrderService,
    Job
)

class ServiceProviderTests(TestCase):
    def setUp(self):
        self.service_provider = ServiceProvider.objects.create(
            name="Test Provider",
            description="Test Description",
            contact_email="test@provider.com",
            contact_phone="+1234567890"
        )

    def test_service_provider_creation(self):
        self.assertEqual(self.service_provider.name, "Test Provider")
        self.assertEqual(self.service_provider.contact_email, "test@provider.com")

    def test_str_representation(self):
        self.assertEqual(str(self.service_provider), "Test Provider")

class AccountManagerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testmanager",
            email="manager@test.com",
            password="testpass123"
        )
        self.service_provider = ServiceProvider.objects.create(
            name="Test Provider",
            contact_email="test@provider.com",
            contact_phone="+1234567890"
        )
        self.account_manager = AccountManager.objects.create(user=self.user)
        self.account_manager.service_providers.add(self.service_provider)

    def test_account_manager_creation(self):
        self.assertEqual(self.account_manager.user.username, "testmanager")
        self.assertEqual(self.account_manager.service_providers.count(), 1)

    def test_service_provider_association(self):
        self.assertIn(self.service_provider, self.account_manager.service_providers.all())

class CustomerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testmanager")
        self.account_manager = AccountManager.objects.create(user=self.user)
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            account_manager=self.account_manager
        )

    def test_customer_creation(self):
        self.assertEqual(self.customer.first_name, "John")
        self.assertEqual(self.customer.last_name, "Doe")
        self.assertEqual(self.customer.email, "john@example.com")

    def test_customer_account_manager_relationship(self):
        self.assertEqual(self.customer.account_manager, self.account_manager)

class OrderTests(TestCase):
    def setUp(self):
        # Create necessary related objects
        self.user = User.objects.create_user(username="testmanager")
        self.account_manager = AccountManager.objects.create(user=self.user)
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            account_manager=self.account_manager
        )
        self.service_provider = ServiceProvider.objects.create(
            name="Test Provider",
            contact_email="test@provider.com"
        )
        self.service = Service.objects.create(
            name="Test Service",
            description="Test Description",
            service_provider=self.service_provider,
            price=Decimal("99.99")
        )
        self.order = Order.objects.create(
            customer=self.customer,
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="PENDING"
        )

    def test_order_creation(self):
        self.assertEqual(self.order.order_number, "ORD-001")
        self.assertEqual(self.order.status, "PENDING")
        self.assertEqual(self.order.total_amount, Decimal("99.99"))

    def test_order_service_relationship(self):
        OrderService.objects.create(
            order=self.order,
            service=self.service,
            quantity=1,
            price_at_time=self.service.price
        )
        self.assertEqual(self.order.services.count(), 1)
        self.assertEqual(self.order.services.first(), self.service)

class JobTests(TestCase):
    def setUp(self):
        # Create necessary related objects
        self.user = User.objects.create_user(username="testmanager")
        self.account_manager = AccountManager.objects.create(user=self.user)
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            account_manager=self.account_manager
        )
        self.service_provider = ServiceProvider.objects.create(
            name="Test Provider",
            contact_email="test@provider.com"
        )
        self.order = Order.objects.create(
            customer=self.customer,
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="PENDING"
        )
        self.job = Job.objects.create(
            order=self.order,
            job_id="JOB-001",
            job_name="Test Job",
            service_provider=self.service_provider,
            job_type="PROCESSING",
            status="PENDING"
        )

    def test_job_creation(self):
        self.assertEqual(self.job.job_type, "PROCESSING")
        self.assertEqual(self.job.status, "PENDING")
        self.assertEqual(self.job.job_id, "JOB-001")
        self.assertEqual(self.job.job_name, "Test Job")
        self.assertIsNone(self.job.started_at)
        self.assertIsNone(self.job.completed_at)

    def test_job_workflow(self):
        # Test start
        self.job.start()
        self.assertEqual(self.job.status, "IN_PROGRESS")
        self.assertIsNotNone(self.job.started_at)

        # Test complete
        self.job.complete()
        self.assertEqual(self.job.status, "COMPLETED")
        self.assertIsNotNone(self.job.completed_at)
        self.assertIsNotNone(self.job.completion_time)

        # Test fail
        error_message = "Test error"
        self.job.fail(error_message)
        self.assertEqual(self.job.status, "FAILED")
        self.assertEqual(self.job.error_message, error_message) 