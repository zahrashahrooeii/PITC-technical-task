"""execution.models.py

This module implements a comprehensive workflow system for managing customer orders
with campaign-based prioritization and execution tracking.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from typing import Any


class Campaign(models.Model):
    """Campaign model representing different types of order campaigns."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    priority = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Campaign priority (1 being highest)",
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority"]

    def __str__(self) -> str:
        return f"{self.name} (Priority: {self.priority})"


class Customer(models.Model):
    """Customer model for managing order ownership."""

    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    """Order model representing customer requests."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="orders"
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.PROTECT, related_name="orders"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_for = models.DateTimeField(
        null=True, blank=True, help_text="When this order is scheduled to be processed"
    )

    class Meta:
        ordering = ["campaign__priority", "created_at"]
        indexes = [
            models.Index(fields=["status", "scheduled_for"]),
            models.Index(fields=["campaign", "status"]),
        ]

    def __str__(self) -> str:
        return f"Order {self.id} - {self.customer.name} ({self.campaign.name})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.scheduled_for:
            self.scheduled_for = timezone.now()
        super().save(*args, **kwargs)


class Job(models.Model):
    """Enhanced Job model for tracking order execution."""

    JOB_TYPE_CHOICES = [
        ("regular", "Regular"),
        ("wafer_run", "Wafer Run"),
    ]
    STATE_CHOICES = [
        ("created", "Created"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    job_id = models.CharField(max_length=10, unique=True)
    job_name = models.CharField(max_length=200)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="jobs")
    state = models.CharField(max_length=100, choices=STATE_CHOICES, default="created")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    starting_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    completion_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Time in days which were spent to complete the job.",
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["state", "job_type"]),
            models.Index(fields=["starting_date", "end_date"]),
        ]

    def __str__(self) -> str:
        return self.job_name

    def calculate_completion_time(self) -> None:
        """Calculate the completion time in days if job is completed."""
        if self.state == "completed" and self.starting_date and self.end_date:
            time_diff = self.end_date - self.starting_date
            self.completion_time = time_diff.total_seconds() / (
                24 * 3600
            )  # Convert to days
