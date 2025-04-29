"""execution.views.py

This module implements the API views for the workflow management system.
"""

from typing import Any, Dict

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.db.models import QuerySet
from django.utils import timezone

from .models import Campaign, Customer, Order, Job
from .serializers import (
    CampaignSerializer,
    CustomerSerializer,
    OrderSerializer,
    JobSerializer,
    OrderCreateSerializer,
)
from .tasks import process_order


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing Campaign instances."""

    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer

    @action(detail=True, methods=["get"])
    def stats(self, request: Request, pk: int = None) -> Response:
        """Get statistics for a specific campaign."""
        campaign = self.get_object()

        # Calculate campaign statistics
        total_orders = Order.objects.filter(campaign=campaign).count()
        completed_jobs = Job.objects.filter(
            order__campaign=campaign, state="completed"
        ).count()

        return Response(
            {
                "total_orders": total_orders,
                "completed_jobs": completed_jobs,
                "success_rate": (
                    (completed_jobs / total_orders * 100) if total_orders > 0 else 0
                ),
            }
        )


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing Customer instances."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    @action(detail=True, methods=["get"])
    def orders(self, request: Request, pk: int = None) -> Response:
        """Get all orders for a specific customer."""
        customer = self.get_object()
        orders = Order.objects.filter(customer=customer)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing Order instances."""

    queryset = Order.objects.all()

    def get_queryset(self) -> QuerySet:
        """Get the queryset for orders with proper filtering."""
        queryset = Order.objects.select_related("customer", "campaign")

        # Filter by status if provided
        status = self.request.query_params.get("status", None)
        if status:
            queryset = queryset.filter(status=status)

        # Filter by campaign if provided
        campaign_id = self.request.query_params.get("campaign", None)
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)

        # Filter by customer if provided
        customer_id = self.request.query_params.get("customer", None)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new order and trigger processing."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Trigger asynchronous order processing
        process_order.delay(order.id)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request: Request, pk: int = None) -> Response:
        """Cancel an order if possible."""
        order = self.get_object()

        if order.status in ["completed", "failed"]:
            return Response(
                {"error": "Cannot cancel completed or failed orders"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "cancelled"
        order.save()

        # Cancel associated jobs
        order.jobs.filter(state__in=["created", "active"]).update(
            state="cancelled", updated_at=timezone.now()
        )

        return Response({"status": "Order cancelled successfully"})


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing Job instances (read-only)."""

    queryset = Job.objects.select_related("order__customer", "order__campaign")
    serializer_class = JobSerializer

    def get_queryset(self) -> QuerySet:
        """Get the queryset for jobs with proper filtering."""
        queryset = self.queryset

        # Filter by state if provided
        state = self.request.query_params.get("state", None)
        if state:
            queryset = queryset.filter(state=state)

        # Filter by job type if provided
        job_type = self.request.query_params.get("type", None)
        if job_type:
            queryset = queryset.filter(job_type=job_type)

        # Filter by date range
        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)
        if start_date and end_date:
            queryset = queryset.filter(
                starting_date__gte=start_date, end_date__lte=end_date
            )

        return queryset

    @action(detail=True, methods=["get"])
    def timeline(self, request: Request, pk: int = None) -> Response:
        """Get the timeline of a job's execution."""
        job = self.get_object()

        timeline_data = {
            "created_at": job.created_at,
            "started_at": job.starting_date,
            "completed_at": job.end_date,
            "state": job.state,
            "completion_time": job.completion_time,
            "type": job.job_type,
        }

        return Response(timeline_data)
