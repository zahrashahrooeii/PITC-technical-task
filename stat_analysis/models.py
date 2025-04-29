from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User

from execution.models import Order, Job, ServiceProvider, AccountManager


class Report(models.Model):
    """Model representing a statistical report.
    
    This model stores metadata about statistical reports, including their time period,
    creator, and optional PDF attachment.
    
    Attributes:
        title (str): The title of the report
        description (str): Optional description of the report contents
        start_date (datetime): Start of the reporting period
        end_date (datetime): End of the reporting period
        created_by (User): User who created the report
        pdf_file (FileField): Optional PDF file attachment
        created_at (datetime): When the report was created
        updated_at (datetime): When the report was last updated
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports'
    )
    pdf_file = models.FileField(
        upload_to='reports/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.start_date.date()} - {self.end_date.date()})"

    class Meta:
        ordering = ['-created_at']


class JobStatistics(models.Model):
    """Model representing job-related statistics.
    
    This model stores statistics about jobs for a specific service provider and job type
    within a reporting period.
    
    Attributes:
        report (Report): The report this statistic belongs to
        service_provider (ServiceProvider): The service provider these stats are for
        job_type (str): The type of job these stats are for
        total_jobs (int): Total number of jobs in the period
        completed_jobs (int): Number of completed jobs
        failed_jobs (int): Number of failed jobs
        average_completion_time (timedelta): Average time to complete a job
        created_at (datetime): When these stats were calculated
    """
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='job_statistics'
    )
    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='job_statistics'
    )
    job_type = models.CharField(max_length=20)
    total_jobs = models.PositiveIntegerField(default=0)
    completed_jobs = models.PositiveIntegerField(default=0)
    failed_jobs = models.PositiveIntegerField(default=0)
    average_completion_time = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_type} stats for {self.service_provider}"

    class Meta:
        unique_together = ['report', 'service_provider', 'job_type']


class OrderStatistics(models.Model):
    """Model representing order-related statistics.
    
    This model stores statistics about orders for a specific service provider
    within a reporting period.
    
    Attributes:
        report (Report): The report this statistic belongs to
        service_provider (ServiceProvider): The service provider these stats are for
        total_orders (int): Total number of orders in the period
        total_revenue (Decimal): Total revenue from completed orders
        average_order_value (Decimal): Average value per order
        completion_rate (Decimal): Percentage of orders completed successfully
        created_at (datetime): When these stats were calculated
    """
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='order_statistics'
    )
    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='order_statistics'
    )
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    average_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order stats for {self.service_provider}"

    class Meta:
        unique_together = ['report', 'service_provider']


class UserStatistics(models.Model):
    """Model representing user-related statistics.
    
    This model stores statistics about account managers and their customers
    within a reporting period.
    
    Attributes:
        report (Report): The report this statistic belongs to
        account_manager (AccountManager): The account manager these stats are for
        total_customers (int): Total number of customers managed
        total_orders (int): Total number of orders from their customers
        total_revenue (Decimal): Total revenue from completed orders
        average_customer_value (Decimal): Average revenue per customer
        created_at (datetime): When these stats were calculated
    """
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='user_statistics'
    )
    account_manager = models.ForeignKey(
        AccountManager,
        on_delete=models.CASCADE,
        related_name='statistics'
    )
    total_customers = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    average_customer_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User stats for {self.account_manager}"

    class Meta:
        unique_together = ['report', 'account_manager']


class CampaignStatistics(models.Model):
    """Model representing campaign-related statistics.
    
    This model stores statistics about marketing campaigns and their performance
    within a reporting period.
    
    Attributes:
        report (Report): The report this statistic belongs to
        campaign (Campaign): The campaign these stats are for
        total_orders (int): Total number of orders in the campaign
        completed_orders (int): Number of completed orders
        cancelled_orders (int): Number of cancelled orders
        total_revenue (Decimal): Total revenue from completed orders
        conversion_rate (Decimal): Percentage of orders completed successfully
        created_at (datetime): When these stats were calculated
    """
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='campaign_statistics'
    )
    campaign = models.ForeignKey(
        'execution.Campaign',
        on_delete=models.CASCADE,
        related_name='statistics'
    )
    total_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Campaign stats for {self.campaign}"

    class Meta:
        unique_together = ['report', 'campaign']
