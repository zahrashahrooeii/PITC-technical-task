from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from execution.models import ServiceProvider, AccountManager, Customer, Service, Order, OrderService

class Command(BaseCommand):
    help = 'Sets up demo data for project evaluation'

    def handle(self, *args, **kwargs):
        # 1. Create Service Provider
        jeppix, created = ServiceProvider.objects.get_or_create(
            name="JePPIX",
            defaults={
                "description": "Provider of photonic integrated circuit services",
                "website": "https://www.jeppix.eu",
                "contact_email": "contact@jeppix.eu",
                "contact_phone": "+31 20 123 4567"
            }
        )
        if created:
            self.stdout.write('Created Service Provider: JePPIX')
        else:
            self.stdout.write('Using existing Service Provider: JePPIX')

        # 2. Create Account Managers
        manager1, created = User.objects.get_or_create(
            username='manager1',
            defaults={
                'email': 'manager1@jeppix.eu',
                'password': 'demo123',
                'first_name': 'Manager',
                'last_name': 'One'
            }
        )
        if created:
            manager1.set_password('demo123')
            manager1.save()
            
        am1, created = AccountManager.objects.get_or_create(user=manager1)
        am1.service_providers.add(jeppix)
        
        manager2, created = User.objects.get_or_create(
            username='manager2',
            defaults={
                'email': 'manager2@jeppix.eu',
                'password': 'demo123',
                'first_name': 'Manager',
                'last_name': 'Two'
            }
        )
        if created:
            manager2.set_password('demo123')
            manager2.save()
            
        AccountManager.objects.get_or_create(user=manager2)
        
        self.stdout.write('Account managers setup completed')

        # 3. Create Services
        service1, created = Service.objects.get_or_create(
            name="PIC Design",
            service_provider=jeppix,
            defaults={
                "description": "Photonic Integrated Circuit Design Service",
                "price": 1000.00
            }
        )
        
        service2, created = Service.objects.get_or_create(
            name="PIC Manufacturing",
            service_provider=jeppix,
            defaults={
                "description": "PIC Manufacturing Service",
                "price": 5000.00
            }
        )
        
        self.stdout.write('Services setup completed')

        # 4. Create Customers and Orders
        customer1, created = Customer.objects.get_or_create(
            email="john.doe@example.com",
            defaults={
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "account_manager": am1
            }
        )
        
        order1, created = Order.objects.get_or_create(
            order_number="ORD-001",
            defaults={
                "customer": customer1,
                "total_amount": 6000.00,
                "status": 'PENDING'
            }
        )

        if created:
            # Only create OrderService instances if the order is new
            OrderService.objects.get_or_create(
                order=order1,
                service=service1,
                defaults={
                    "quantity": 1,
                    "price_at_time": service1.price
                }
            )
            
            OrderService.objects.get_or_create(
                order=order1,
                service=service2,
                defaults={
                    "quantity": 1,
                    "price_at_time": service2.price
                }
            )
        
        self.stdout.write('Customer and order setup completed')

        self.stdout.write(self.style.SUCCESS('''
        Demo setup completed successfully!
        
        You can now test the system with these credentials:
        
        Account Manager 1:
        - Username: manager1
        - Password: demo123
        - Has access to JePPIX services
        
        Account Manager 2:
        - Username: manager2
        - Password: demo123
        - No access to JePPIX services
        
        Visit http://127.0.0.1:8000/admin/ to see the system in action!
        ''')) 