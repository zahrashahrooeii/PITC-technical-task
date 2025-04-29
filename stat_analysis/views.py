from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from execution.models import Customer, Order, Job, ServiceProvider
from .stat_utils import (
    calculate_job_statistics,
    calculate_order_statistics,
    calculate_user_statistics,
    generate_report
)


class ReportViewSet(viewsets.ViewSet):
    """ViewSet for generating various reports."""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def campaign_performance(self, request):
        """DEPRECATED or needs refactoring. 
           Get performance metrics for all campaigns (based on old structure). 
           This might need to be adapted for ServiceProvider performance.
        """
        return Response({"message": "Campaign performance endpoint needs refactoring for Service Providers."})

    @action(detail=False, methods=['get'])
    def customer_metrics(self, request):
        """Get metrics for all customers (based on old structure - needs verification)."""
        return Response({"message": "Customer metrics endpoint needs review against UserStatistics."})

    @action(detail=False, methods=['get'])
    def order_statistics(self, request):
        """Get overall order statistics (based on old structure - needs verification)."""
        return Response({"message": "Order statistics endpoint needs review against OrderStatistics."})

    @action(detail=False, methods=['get'])
    def job_metrics(self, request):
        """Get overall job processing metrics (based on old structure - needs verification)."""
        return Response({"message": "Job metrics endpoint needs review against JobStatistics."})


class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for real-time analytics (based on old structure - needs refactoring)."""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def revenue_by_campaign(self, request):
        """DEPRECATED or needs refactoring.
           Get revenue breakdown by campaign. Should be by Service Provider.
        """
        return Response({"message": "Revenue by campaign endpoint needs refactoring for Service Providers."})

    @action(detail=False, methods=['get'])
    def customer_segments(self, request):
        """Get customer segmentation based on order value (needs review)."""
        return Response({"message": "Customer segments endpoint needs review and potential refactoring."})

    @action(detail=False, methods=['get'])
    def job_performance(self, request):
        """Get detailed job performance metrics (needs review)."""
        return Response({"message": "Job performance endpoint needs review, should likely use JobStatistics model."})
