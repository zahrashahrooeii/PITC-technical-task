"""stat_analysis.stat_utils.py

This module provides advanced statistical analysis utilities for analyzing job execution data.
"""

import datetime
from typing import Tuple, Dict, List, Optional
from collections import defaultdict

import pandas as pd
import numpy as np
from django.db.models import Q, Avg, Min, Max, Count
from django.apps import apps
from django.utils import timezone
from execution.models import Job, Campaign, Customer, Order


# Get models dynamically to avoid circular imports
job_stats_model = apps.get_model("stat_analysis", "JobReportResult")
report_model = apps.get_model("stat_analysis", "Report")


def get_quarter_dates(quarter: str, year: int) -> Tuple[datetime.date, datetime.date]:
    """Get start and end dates for a given quarter and year.

    Args:
        quarter: Quarter identifier (Q1-Q4)
        year: Year for the quarter

    Returns:
        Tuple of start_date and end_date

    Raises:
        ValueError: If invalid quarter provided
    """
    if quarter == "Q1":
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 3, 31)
    elif quarter == "Q2":
        start_date = datetime.date(year, 4, 1)
        end_date = datetime.date(year, 6, 30)
    elif quarter == "Q3":
        start_date = datetime.date(year, 7, 1)
        end_date = datetime.date(year, 9, 30)
    elif quarter == "Q4":
        start_date = datetime.date(year, 10, 1)
        end_date = datetime.date(year, 12, 31)
    else:
        raise ValueError("Invalid quarter. Please use 'Q1', 'Q2', 'Q3', or 'Q4'.")
    return start_date, end_date


def calculate_job_stats(
    quarter_from: str, year_from: int, quarter_to: str, year_to: int
) -> "job_stats_model":
    """Calculate comprehensive statistics for jobs in a given period.

    Args:
        quarter_from: Starting quarter
        year_from: Starting year
        quarter_to: Ending quarter
        year_to: Ending year

    Returns:
        JobReportResult instance with calculated statistics
    """
    start_date_from, end_date_from = get_quarter_dates(quarter_from, year_from)
    start_date_to, end_date_to = get_quarter_dates(quarter_to, year_to)

    start_date = min(start_date_from, start_date_to)
    end_date = max(end_date_from, end_date_to)

    # Get jobs for the period
    jobs = Job.objects.filter(
        starting_date__gte=start_date, end_date__lte=end_date
    ).select_related("order__campaign", "order__customer")

    # Basic counts
    total_jobs = jobs.count()
    completed_jobs = jobs.filter(state="completed").count()
    failed_jobs = jobs.filter(state="failed").count()

    # Time-based statistics for completed jobs
    completion_times = jobs.filter(
        state="completed", completion_time__isnull=False
    ).values_list("completion_time", flat=True)

    completion_times_list = list(completion_times)
    avg_completion_time = (
        np.mean(completion_times_list) if completion_times_list else None
    )
    median_completion_time = (
        np.median(completion_times_list) if completion_times_list else None
    )
    min_completion_time = (
        np.min(completion_times_list) if completion_times_list else None
    )
    max_completion_time = (
        np.max(completion_times_list) if completion_times_list else None
    )

    # Campaign distribution
    campaign_stats = defaultdict(int)
    for job in jobs:
        campaign_stats[job.order.campaign.name] += 1

    # Customer distribution
    customer_stats = defaultdict(int)
    for job in jobs:
        customer_stats[job.order.customer.name] += 1

    # Create or update report
    report, _ = report_model.objects.get_or_create(
        quarter_from=quarter_from,
        year_from=year_from,
        quarter_to=quarter_to,
        year_to=year_to,
        defaults={
            "title": f"Job Analysis Report {quarter_from}/{year_from}-{quarter_to}/{year_to}",
            "created_at": timezone.now(),
            "created_by": "system",
        },
    )

    # Create or update job statistics
    job_stats, created = job_stats_model.objects.update_or_create(
        report=report,
        defaults={
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "avg_completion_time": avg_completion_time,
            "median_completion_time": median_completion_time,
            "min_completion_time": min_completion_time,
            "max_completion_time": max_completion_time,
            # Add other fields to update if needed
            # "campaign_distribution": campaign_stats, # Assuming JSONField or similar
            # "customer_distribution": customer_stats, # Assuming JSONField or similar
            # "success_rate": calculate_success_rate(completed_jobs, total_jobs) # Assuming a helper function
        },
    )

    # # Update statistics # These lines are now redundant due to update_or_create
    # job_stats.total_jobs = total_jobs
    # job_stats.completed_jobs = completed_jobs
    # job_stats.failed_jobs = failed_jobs
    # job_stats.avg_completion_time = avg_completion_time
    # job_stats.median_completion_time = median_completion_time
    # job_stats.min_completion_time = min_completion_time
    # job_stats.max_completion_time = max_completion_time

    # # Update distributions - These methods likely don't exist on the model
    # job_stats.set_campaign_distribution(campaign_stats)
    # job_stats.set_customer_distribution(customer_stats)

    # # Calculate success rate - This method likely doesn't exist on the model
    # job_stats.update_success_rate()

    # job_stats.save() # Not needed after update_or_create
    return job_stats


def analyze_campaign_performance(
    start_date: datetime.date, end_date: datetime.date
) -> Dict[str, Dict[str, float]]:
    """Analyze campaign performance metrics.

    Args:
        start_date: Analysis period start date
        end_date: Analysis period end date

    Returns:
        Dictionary with campaign performance metrics
    """
    campaigns = Campaign.objects.all()
    performance_metrics = {}

    for campaign in campaigns:
        campaign_jobs = Job.objects.filter(
            order__campaign=campaign,
            starting_date__gte=start_date,
            end_date__lte=end_date,
        )

        total = campaign_jobs.count()
        if total == 0:
            continue

        completed = campaign_jobs.filter(state="completed").count()
        avg_completion_time = campaign_jobs.filter(state="completed").aggregate(
            avg=Avg("completion_time")
        )["avg"]

        performance_metrics[campaign.name] = {
            "total_jobs": total,
            "success_rate": (completed / total) * 100 if total > 0 else 0,
            "avg_completion_time": avg_completion_time or 0,
            "priority": campaign.priority,
        }

    return performance_metrics


def analyze_customer_patterns(
    start_date: datetime.date, end_date: datetime.date
) -> Dict[str, Dict[str, any]]:
    """Analyze customer ordering patterns.

    Args:
        start_date: Analysis period start date
        end_date: Analysis period end date

    Returns:
        Dictionary with customer pattern metrics
    """
    customers = Customer.objects.all()
    pattern_metrics = {}

    for customer in customers:
        customer_orders = Order.objects.filter(
            customer=customer, created_at__gte=start_date, created_at__lte=end_date
        )

        if not customer_orders.exists():
            continue

        # Analyze campaign preferences
        campaign_usage = (
            customer_orders.values("campaign__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Analyze order timing
        order_hours = customer_orders.values_list("created_at__hour", flat=True)

        pattern_metrics[customer.name] = {
            "total_orders": customer_orders.count(),
            "preferred_campaigns": [
                {"campaign": item["campaign__name"], "usage_count": item["count"]}
                for item in campaign_usage[:3]  # Top 3 campaigns
            ],
            "peak_order_hour": (
                pd.Series(order_hours).mode()[0] if len(order_hours) > 0 else None
            ),
        }

    return pattern_metrics
