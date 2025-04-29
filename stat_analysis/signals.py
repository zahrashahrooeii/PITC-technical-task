from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Report
from .stat_utils import (
    calculate_job_statistics,
    calculate_order_statistics,
    calculate_user_statistics
)


@receiver(post_save, sender=Report)
def calculate_report_statistics(sender, instance, created, **kwargs):
    """Calculate statistics when a report is created or updated."""
    if created or instance._state.adding:
        # Calculate all statistics for the new report
        calculate_job_statistics(instance)
        calculate_order_statistics(instance)
        calculate_user_statistics(instance)
    else:
        # Update existing statistics
        calculate_job_statistics(instance)
        calculate_order_statistics(instance)
        calculate_user_statistics(instance) 