from decimal import Decimal
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone

from execution.models import Campaign, Customer, Order, Job


def calculate_campaign_performance(campaign_id):
    """Calculate performance metrics for a specific campaign."""
    campaign = Campaign.objects.get(id=campaign_id)
    orders = Order.objects.filter(campaign=campaign)
    
    total_orders = orders.count()
    completed_orders = orders.filter(status='COMPLETED').count()
    cancelled_orders = orders.filter(status='CANCELLED').count()
    
    conversion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    total_revenue = orders.filter(status='COMPLETED').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    return {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'conversion_rate': round(conversion_rate, 2),
        'total_revenue': total_revenue
    }


def calculate_customer_metrics(customer_id):
    """Calculate metrics for a specific customer."""
    customer = Customer.objects.get(id=customer_id)
    orders = Order.objects.filter(customer=customer)
    
    total_orders = orders.count()
    completed_orders = orders.filter(status='COMPLETED').count()
    
    success_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    total_spent = orders.filter(status='COMPLETED').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    average_order_value = (total_spent / completed_orders) if completed_orders > 0 else Decimal('0.00')
    
    return {
        'total_orders': total_orders,
        'average_order_value': average_order_value,
        'success_rate': round(success_rate, 2),
        'total_spent': total_spent
    }


def calculate_order_statistics():
    """Calculate overall order statistics."""
    orders = Order.objects.all()
    
    total_orders = orders.count()
    completed_orders = orders.filter(status='COMPLETED').count()
    
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    total_revenue = orders.filter(status='COMPLETED').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    average_order_value = (total_revenue / completed_orders) if completed_orders > 0 else Decimal('0.00')
    
    return {
        'total_orders': total_orders,
        'average_order_value': average_order_value,
        'completion_rate': round(completion_rate, 2),
        'total_revenue': total_revenue
    }


def calculate_job_metrics():
    """Calculate overall job processing metrics."""
    jobs = Job.objects.all()
    
    total_jobs = jobs.count()
    completed_jobs = jobs.filter(status='COMPLETED').count()
    failed_jobs = jobs.filter(status='FAILED').count()
    
    success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    failure_rate = (failed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    # Calculate average processing time (in seconds)
    completed_jobs_with_time = jobs.filter(
        status='COMPLETED',
        started_at__isnull=False,
        completed_at__isnull=False
    )
    
    if completed_jobs_with_time.exists():
        total_time = sum(
            (job.completed_at - job.started_at).total_seconds()
            for job in completed_jobs_with_time
        )
        average_processing_time = total_time / completed_jobs_with_time.count()
    else:
        average_processing_time = 0
    
    return {
        'total_jobs': total_jobs,
        'success_rate': round(success_rate, 2),
        'failure_rate': round(failure_rate, 2),
        'average_processing_time': round(average_processing_time, 2)
    } 