"""stat_analysis.models.py

This module implements models for storing and managing statistical analysis results
of job execution data.
"""

from django.db import models
from django.core.validators import MinValueValidator
from typing import Dict, Any


class Report(models.Model):
    """Model for storing report metadata and parameters."""

    QUARTER_CHOICES = [
        ("Q1", "Q1"),
        ("Q2", "Q2"),
        ("Q3", "Q3"),
        ("Q4", "Q4"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Report period
    quarter_from = models.CharField(max_length=2, choices=QUARTER_CHOICES)
    year_from = models.IntegerField(validators=[MinValueValidator(2000)])
    quarter_to = models.CharField(max_length=2, choices=QUARTER_CHOICES)
    year_to = models.IntegerField(validators=[MinValueValidator(2000)])

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100)

    class Meta:
        unique_together = ["quarter_from", "year_from", "quarter_to", "year_to"]
        indexes = [
            models.Index(fields=["year_from", "quarter_from"]),
            models.Index(fields=["year_to", "quarter_to"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.quarter_from}/{self.year_from} - {self.quarter_to}/{self.year_to})"


class JobReportResult(models.Model):
    """Model for storing detailed job statistics results."""

    report = models.OneToOneField(
        Report, on_delete=models.CASCADE, related_name="job_stats"
    )

    # Basic statistics
    total_jobs = models.IntegerField(default=0)
    completed_jobs = models.IntegerField(default=0)
    failed_jobs = models.IntegerField(default=0)

    # Time-based statistics
    avg_completion_time = models.FloatField(
        null=True, blank=True, help_text="Average completion time in days"
    )
    median_completion_time = models.FloatField(
        null=True, blank=True, help_text="Median completion time in days"
    )
    min_completion_time = models.FloatField(
        null=True, blank=True, help_text="Minimum completion time in days"
    )
    max_completion_time = models.FloatField(
        null=True, blank=True, help_text="Maximum completion time in days"
    )

    # Campaign statistics
    campaign_distribution = models.JSONField(
        default=dict, help_text="Distribution of jobs across campaigns"
    )

    # Customer statistics
    customer_distribution = models.JSONField(
        default=dict, help_text="Distribution of jobs across customers"
    )

    # Performance metrics
    success_rate = models.FloatField(
        null=True, blank=True, help_text="Percentage of successfully completed jobs"
    )

    class Meta:
        indexes = [
            models.Index(fields=["report"]),
        ]

    def __str__(self) -> str:
        return f"Stats for {self.report}"

    def update_success_rate(self) -> None:
        """Calculate and update the success rate."""
        if self.total_jobs > 0:
            self.success_rate = (self.completed_jobs / self.total_jobs) * 100

    def set_campaign_distribution(self, distribution: Dict[str, int]) -> None:
        """Update campaign distribution with validation."""
        self.campaign_distribution = {
            str(campaign): count for campaign, count in distribution.items()
        }

    def set_customer_distribution(self, distribution: Dict[str, int]) -> None:
        """Update customer distribution with validation."""
        self.customer_distribution = {
            str(customer): count for customer, count in distribution.items()
        }
