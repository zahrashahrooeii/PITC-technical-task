"""execution.tasks.py

This module implements Celery tasks for asynchronous job processing.
"""

import logging
from typing import Optional
from datetime import datetime

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.db.models import F

from .models import Order, Job


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_order(self, order_id: int) -> None:
    """Process an order asynchronously.

    Args:
        order_id: ID of the order to process

    This task:
    1. Validates the order
    2. Creates necessary jobs
    3. Updates order status
    4. Triggers job execution
    """
    try:
        with transaction.atomic():
            # Get the order
            order = Order.objects.select_related("customer", "campaign").get(
                id=order_id
            )

            # Check if order can be processed
            if order.status != "pending":
                logger.warning(
                    f"Order {order_id} is not in pending state: {order.status}"
                )
                return

            if not order.customer.active or not order.campaign.active:
                order.status = "failed"
                order.save()
                logger.error(f"Order {order_id} failed: Customer or campaign inactive")
                return

            # Create a job for the order
            job = Job.objects.create(
                order=order,
                job_id=f"JOB-{order_id}",
                job_name=f"Job for Order {order_id}",
                job_type="regular",
                state="created",
            )

            # Update order status
            order.status = "processing"
            order.save()

            # Trigger job execution
            execute_job.delay(job.id)

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error processing order {order_id}: {str(e)}")
        self.retry(exc=e)


@shared_task(bind=True, max_retries=3)
def execute_job(self, job_id: int) -> None:
    """Execute a job asynchronously.

    Args:
        job_id: ID of the job to execute

    This task:
    1. Updates job state
    2. Performs the actual job execution
    3. Updates completion metrics
    """
    try:
        with transaction.atomic():
            # Get the job
            job = Job.objects.select_related("order").get(id=job_id)

            # Check if job can be executed
            if job.state != "created":
                logger.warning(f"Job {job_id} is not in created state: {job.state}")
                return

            # Start job execution
            job.state = "active"
            job.starting_date = timezone.now()
            job.save()

            # Simulate job execution (replace with actual logic)
            try:
                execute_job_logic(job)

                # Update job completion
                job.state = "completed"
                job.end_date = timezone.now()
                job.calculate_completion_time()
                job.save()

                # Update order status if all jobs are completed
                order = job.order
                if not order.jobs.exclude(state="completed").exists():
                    order.status = "completed"
                    order.save()

            except Exception as e:
                # Handle job failure
                job.state = "failed"
                job.error_message = str(e)
                job.end_date = timezone.now()
                job.save()

                # Update order status
                order = job.order
                order.status = "failed"
                order.save()

                raise

    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {str(e)}")
        self.retry(exc=e)


def execute_job_logic(job: Job) -> None:
    """Execute the actual job logic.

    Args:
        job: Job instance to execute

    This is where you would implement the actual job execution logic.
    For now, it's a placeholder that simulates processing.
    """
    # Placeholder for actual job execution logic
    # In a real implementation, this would contain the specific
    # processing logic for different job types

    if job.job_type == "regular":
        # Simulate regular job processing
        pass
    elif job.job_type == "wafer_run":
        # Simulate wafer run processing
        pass
    else:
        raise ValueError(f"Unknown job type: {job.job_type}")


@shared_task
def cleanup_stale_jobs() -> None:
    """Cleanup stale jobs that have been stuck in processing.

    This periodic task:
    1. Identifies jobs that have been stuck in 'active' state
    2. Marks them as failed
    3. Updates corresponding orders
    """
    # Find jobs that have been active for too long (e.g., 24 hours)
    stale_jobs = Job.objects.filter(
        state="active", starting_date__lt=timezone.now() - timezone.timedelta(hours=24)
    )

    for job in stale_jobs:
        with transaction.atomic():
            job.state = "failed"
            job.error_message = "Job timed out"
            job.end_date = timezone.now()
            job.save()

            # Update order status
            order = job.order
            order.status = "failed"
            order.save()

        logger.warning(f"Cleaned up stale job {job.id} for order {order.id}")


@shared_task
def update_campaign_priorities() -> None:
    """Update campaign priorities based on performance metrics.

    This periodic task:
    1. Analyzes campaign performance
    2. Adjusts priorities based on success rates and completion times
    """
    from django.db.models import Avg, Count
    from .models import Campaign

    # Calculate campaign performance metrics
    campaigns = Campaign.objects.annotate(
        total_orders=Count("orders"),
        success_rate=Count("orders", filter={"jobs__state": "completed"})
        * 100.0
        / Count("orders"),
        avg_completion_time=Avg("orders__jobs__completion_time"),
    )

    # Update priorities based on performance
    for campaign in campaigns:
        if campaign.total_orders > 0:
            # Simple priority adjustment logic (customize as needed)
            if campaign.success_rate < 50:
                # Decrease priority for poorly performing campaigns
                Campaign.objects.filter(id=campaign.id).update(
                    priority=F("priority") + 1
                )
            elif campaign.success_rate > 90:
                # Increase priority for well-performing campaigns
                Campaign.objects.filter(id=campaign.id).update(
                    priority=F("priority") - 1
                ).filter(priority__lt=1).update(priority=1)
