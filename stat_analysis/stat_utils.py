import logging
from datetime import timedelta
from decimal import Decimal, DivisionByZero
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models

from execution.models import Order, Job, ServiceProvider, AccountManager, Customer, Campaign
from .models import Report, JobStatistics, OrderStatistics, UserStatistics, CampaignStatistics

# Define a logger for this module
logger = logging.getLogger(__name__)

def calculate_job_statistics(report, jobs_queryset=None):
    """Calculate job-related statistics for a report."""
    if report is None:
        raise ValidationError("Report object cannot be None")
    if not isinstance(report, Report):
        raise ValidationError(f"Expected Report object, got {type(report).__name__}")
    
    start_date = report.start_date
    end_date = report.end_date
    
    if start_date is None or end_date is None:
        raise ValidationError("Report must have both start_date and end_date defined")
    
    if start_date >= end_date:
        raise ValidationError("Start date must be before end date")
    
    # Use provided queryset or query the database
    if jobs_queryset is None:
        jobs_in_range = Job.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
    else:
        # Ensure the provided queryset is for the Job model
        if not isinstance(jobs_queryset, models.QuerySet) or jobs_queryset.model is not Job:
             raise ValidationError("Provided jobs_queryset must be a Job QuerySet.")
        # We assume the provided queryset is already filtered by date if necessary
        jobs_in_range = jobs_queryset

    for service_provider in ServiceProvider.objects.all():
        for job_type in dict(Job._meta.get_field('job_type').choices).keys():
            try:
                # Filter specifically for this provider and type within the range
                relevant_jobs = jobs_in_range.filter(
                    service_provider=service_provider,
                    job_type=job_type
                )
                total_jobs_count = relevant_jobs.count()
                completed_jobs_count = relevant_jobs.filter(status='COMPLETED').count()
                failed_jobs_count = relevant_jobs.filter(status='FAILED').count()

                completed_timed_jobs = relevant_jobs.filter(
                    status='COMPLETED',
                    started_at__isnull=False,
                    completed_at__isnull=False
                )

                if completed_timed_jobs.exists():
                    total_time = sum((
                        job.completed_at - job.started_at
                        for job in completed_timed_jobs
                    ), start=timedelta(0))
                    avg_completion_time = total_time / completed_timed_jobs.count()
                else:
                    avg_completion_time = None

                JobStatistics.objects.update_or_create(
                    report=report,
                    service_provider=service_provider,
                    job_type=job_type,
                    defaults={
                        'total_jobs': total_jobs_count,
                        'completed_jobs': completed_jobs_count,
                        'failed_jobs': failed_jobs_count,
                        'average_completion_time': avg_completion_time
                    }
                )
            except Exception as e:
                # Log the error
                logger.error(f"Error calculating job statistics for {service_provider}/{job_type} in report {report.id}: {str(e)}", exc_info=True)
                # Continue to next iteration instead of stopping the whole process
                # raise ValidationError(f"Error calculating job statistics: {str(e)}")


def calculate_order_statistics(report, orders_queryset=None):
    """Calculate order-related statistics for a report.
    
    Args:
        report (Report): The report instance to calculate statistics for
        orders_queryset (QuerySet, optional): Pre-filtered queryset of orders. If None,
            will query all orders within the report's date range.
            
    Raises:
        ValidationError: If report is invalid or date range is incorrect
    """
    if report is None:
        raise ValidationError("Report object cannot be None")
    if not isinstance(report, Report):
        raise ValidationError(f"Expected Report object, got {type(report).__name__}")
    
    start_date = report.start_date
    end_date = report.end_date
    
    if start_date is None or end_date is None:
        raise ValidationError("Report must have both start_date and end_date defined")
    
    if start_date >= end_date:
        raise ValidationError("Start date must be before end date")
    
    # Use provided queryset or query the database
    if orders_queryset is None:
        orders_in_range = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('customer')
    else:
        if not isinstance(orders_queryset, models.QuerySet) or orders_queryset.model is not Order:
            raise ValidationError("Provided orders_queryset must be an Order QuerySet.")
        orders_in_range = orders_queryset.select_related('customer')

    for service_provider in ServiceProvider.objects.all():
        try:
            # Filter orders for this provider
            provider_orders = orders_in_range.filter(
                services__service_provider=service_provider
            ).distinct()
            
            total_orders = provider_orders.count()
            total_revenue = provider_orders.filter(status='COMPLETED').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            completed_orders = provider_orders.filter(status='COMPLETED').count()
            completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            
            # Calculate average order value
            if completed_orders > 0:
                average_order_value = total_revenue / completed_orders
            else:
                average_order_value = Decimal('0.00')
            
            OrderStatistics.objects.update_or_create(
                report=report,
                service_provider=service_provider,
                defaults={
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'average_order_value': average_order_value,
                    'completion_rate': completion_rate
                }
            )
        except Exception as e:
            logger.error(
                f"Error calculating order statistics for {service_provider} in report {report.id}: {str(e)}",
                exc_info=True
            )


def calculate_user_statistics(report, orders_queryset=None):
    """Calculate user-related statistics for a report.
    
    Args:
        report (Report): The report instance to calculate statistics for
        orders_queryset (QuerySet, optional): Pre-filtered queryset of orders. If None,
            will query all orders within the report's date range.
            
    Raises:
        ValidationError: If report is invalid or date range is incorrect
    """
    if report is None:
        raise ValidationError("Report object cannot be None")
    if not isinstance(report, Report):
        raise ValidationError(f"Expected Report object, got {type(report).__name__}")
    
    start_date = report.start_date
    end_date = report.end_date
    
    if start_date is None or end_date is None:
        raise ValidationError("Report must have both start_date and end_date defined")
    
    if start_date >= end_date:
        raise ValidationError("Start date must be before end date")
    
    # Use provided queryset or query the database
    if orders_queryset is None:
        orders_in_range = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('customer')
    else:
        if not isinstance(orders_queryset, models.QuerySet) or orders_queryset.model is not Order:
            raise ValidationError("Provided orders_queryset must be an Order QuerySet.")
        orders_in_range = orders_queryset.select_related('customer')

    for account_manager in AccountManager.objects.all():
        try:
            # Get all customers managed by this account manager
            customers = Customer.objects.filter(account_manager=account_manager)
            total_customers = customers.count()
            
            # Get orders for these customers
            manager_orders = orders_in_range.filter(customer__in=customers)
            total_orders = manager_orders.count()
            
            # Calculate revenue
            total_revenue = manager_orders.filter(status='COMPLETED').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Calculate average customer value
            if total_customers > 0:
                average_customer_value = total_revenue / total_customers
            else:
                average_customer_value = Decimal('0.00')
            
            UserStatistics.objects.update_or_create(
                report=report,
                account_manager=account_manager,
                defaults={
                    'total_customers': total_customers,
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'average_customer_value': average_customer_value
                }
            )
        except Exception as e:
            logger.error(
                f"Error calculating user statistics for {account_manager} in report {report.id}: {str(e)}",
                exc_info=True
            )


def calculate_campaign_statistics(report, orders_queryset=None):
    """Calculate campaign-related statistics for a report.
    
    Args:
        report (Report): The report instance to calculate statistics for
        orders_queryset (QuerySet, optional): Pre-filtered queryset of orders. If None,
            will query all orders within the report's date range.
            
    Raises:
        ValidationError: If report is invalid or date range is incorrect
    """
    if report is None:
        raise ValidationError("Report object cannot be None")
    if not isinstance(report, Report):
        raise ValidationError(f"Expected Report object, got {type(report).__name__}")
    
    start_date = report.start_date
    end_date = report.end_date
    
    if start_date is None or end_date is None:
        raise ValidationError("Report must have both start_date and end_date defined")
    
    if start_date >= end_date:
        raise ValidationError("Start date must be before end date")
    
    # Use provided queryset or query the database
    if orders_queryset is None:
        orders_in_range = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('campaign')
    else:
        if not isinstance(orders_queryset, models.QuerySet) or orders_queryset.model is not Order:
            raise ValidationError("Provided orders_queryset must be an Order QuerySet.")
        orders_in_range = orders_queryset.select_related('campaign')

    for campaign in Campaign.objects.all():
        try:
            # Filter orders for this campaign
            campaign_orders = orders_in_range.filter(campaign=campaign)
            
            total_orders = campaign_orders.count()
            completed_orders = campaign_orders.filter(status='COMPLETED').count()
            cancelled_orders = campaign_orders.filter(status='CANCELLED').count()
            
            total_revenue = campaign_orders.filter(status='COMPLETED').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            conversion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            
            CampaignStatistics.objects.update_or_create(
                report=report,
                campaign=campaign,
                defaults={
                    'total_orders': total_orders,
                    'completed_orders': completed_orders,
                    'cancelled_orders': cancelled_orders,
                    'total_revenue': total_revenue,
                    'conversion_rate': conversion_rate
                }
            )
        except Exception as e:
            logger.error(
                f"Error calculating campaign statistics for {campaign} in report {report.id}: {str(e)}",
                exc_info=True
            )


def generate_report(title, description, start_date, end_date, created_by):
    """Generate a complete report with all statistics."""
    if not title or not description:
        raise ValidationError("Title and description are required")
    if not start_date or not end_date:
        raise ValidationError("Start date and end date are required")
    if start_date >= end_date:
        raise ValidationError("Start date must be before end date")
    if not created_by or not isinstance(created_by, models.Model): # Check for valid model instance
        raise ValidationError("Valid 'created by' user or manager instance is required")

    # Determine the user who created the report (assuming a User or similar model)
    # This might need adjustment based on your actual user model structure
    # For simplicity, assuming created_by has a 'username' or similar identifier
    creator_identifier = getattr(created_by, 'username', str(created_by.id))
    logger.info(f"Generating report '{title}' from {start_date} to {end_date} requested by {creator_identifier}")

    try:
        # Wrap report creation and subsequent calculations in a transaction
        # to ensure atomicity. If any calculation fails, the report
        # and associated stats are rolled back.
        from django.db import transaction
        with transaction.atomic():
            report = Report.objects.create(
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                created_by=created_by # Pass the model instance
            )
            logger.info(f"Report {report.id} created successfully.")

            # Fetch relevant objects ONCE for the date range
            jobs_in_range = Job.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
            orders_in_range = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)

            # Call calculation functions, passing the pre-fetched querysets
            logger.info(f"Calculating job statistics for report {report.id}...")
            calculate_job_statistics(report, jobs_queryset=jobs_in_range)
            logger.info(f"Calculating order statistics for report {report.id}...")
            calculate_order_statistics(report, orders_queryset=orders_in_range)
            logger.info(f"Calculating user statistics for report {report.id}...")
            calculate_user_statistics(report, orders_queryset=orders_in_range) # Pass orders queryset here too
            logger.info(f"Calculating campaign statistics for report {report.id}...")
            calculate_campaign_statistics(report, orders_queryset=orders_in_range)

            report.status = 'COMPLETED'
            report.save()
            logger.info(f"Report {report.id} generation completed successfully.")

        return report

    except ValidationError as ve:
        logger.error(f"Validation error generating report '{title}': {ve}")
        raise # Re-raise validation errors
    except Exception as e:
        # Log unexpected errors during report generation
        logger.error(f"Unexpected error generating report '{title}': {str(e)}", exc_info=True)
        # Optionally, update report status to FAILED here if created
        # reports = Report.objects.filter(title=title, start_date=start_date, end_date=end_date, created_by=created_by)
        # if reports.exists():
        #     report = reports.first()
        #     report.status = 'FAILED'
        #     report.save(update_fields=['status'])
        raise ValidationError(f"Failed to generate report due to an internal error: {str(e)}") 