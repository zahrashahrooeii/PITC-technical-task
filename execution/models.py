from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class ServiceProvider(models.Model):
    """Model representing a service provider company."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Campaign(models.Model):
    """Model representing a marketing campaign."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    priority = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Campaign priority (1 being highest)",
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Priority: {self.priority})"

    class Meta:
        ordering = ["priority"]


class AccountManager(models.Model):
    """Model representing an account manager."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    service_providers = models.ManyToManyField(
        ServiceProvider,
        related_name='account_managers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.email})"

    class Meta:
        ordering = ['user__last_name', 'user__first_name']


class Customer(models.Model):
    """Model representing a customer."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    address = models.TextField(blank=True)
    account_manager = models.ForeignKey(
        AccountManager,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['account_manager', 'email']),
            models.Index(fields=['created_at']),
        ]


class Service(models.Model):
    """Model representing a service/product offered by a service provider."""
    name = models.CharField(max_length=200)
    description = models.TextField()
    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='services'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.service_provider.name})"

    class Meta:
        ordering = ['name']


class Order(models.Model):
    """Model representing a customer order."""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    order_number = models.CharField(max_length=50, unique=True)
    services = models.ManyToManyField(
        Service,
        through='OrderService',
        related_name='orders'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
            ('REFUNDED', 'Refunded')
        ],
        default='PENDING'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.customer}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['campaign', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]


class OrderService(models.Model):
    """Model representing a service in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1, message="Quantity must be greater than zero.")]
    )
    price_at_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service.name} in {self.order.order_number}"

    def clean(self):
        """Validate the OrderService instance."""
        super().clean()
        
        # Ensure price_at_time is set
        if not self.price_at_time and self.service:
            self.price_at_time = self.service.price
        
        # Validate order status
        if self.order and self.order.status not in ['PENDING']:
            raise ValidationError(
                f"Cannot add services to order in {self.order.status} status"
            )

    def save(self, *args, **kwargs):
        """Override save to ensure validation is called."""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['order', 'service']
        indexes = [
            models.Index(fields=['order', 'service']),
            models.Index(fields=['created_at']),
        ]


class Job(models.Model):
    """Enhanced Job model for tracking order execution."""

    JOB_TYPE_CHOICES = [
        ('VALIDATION', 'Validation'),
        ('PROCESSING', 'Processing'),
        ('SHIPPING', 'Shipping'),
        ('REPORTING', 'Reporting')
    ]
    STATE_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]

    VALID_STATE_TRANSITIONS = {
        'PENDING': ['IN_PROGRESS', 'FAILED'],
        'IN_PROGRESS': ['COMPLETED', 'FAILED'],
        'COMPLETED': [],  # Terminal state
        'FAILED': []  # Terminal state
    }

    job_id = models.CharField(max_length=10, unique=True)
    job_name = models.CharField(max_length=200)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='jobs')
    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='jobs',
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='PENDING'
    )
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Time in days which were spent to complete the job."
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'job_type']),
            models.Index(fields=['started_at', 'completed_at']),
        ]

    def __str__(self) -> str:
        return self.job_name

    def _validate_state_transition(self, new_state):
        """Validate if the state transition is allowed."""
        if new_state not in self.VALID_STATE_TRANSITIONS.get(self.status, []):
            raise ValidationError(
                f"Invalid state transition from {self.status} to {new_state}"
            )

    def start(self):
        """Mark the job as started."""
        self._validate_state_transition('IN_PROGRESS')
        self.started_at = timezone.now()
        self.status = 'IN_PROGRESS'
        self.save()

    def complete(self):
        """Mark the job as completed."""
        self._validate_state_transition('COMPLETED')
        self.completed_at = timezone.now()
        self.status = 'COMPLETED'
        self.calculate_completion_time()
        self.save()

    def fail(self, error_message):
        """Mark the job as failed with an error message."""
        self._validate_state_transition('FAILED')
        self.completed_at = timezone.now()
        self.status = 'FAILED'
        self.error_message = error_message
        self.save()

    def calculate_completion_time(self) -> None:
        """Calculate the completion time in days if job is completed."""
        if self.status == 'COMPLETED' and self.started_at and self.completed_at:
            time_diff = self.completed_at - self.started_at
            self.completion_time = time_diff.total_seconds() / (24 * 3600)  # Convert to days
