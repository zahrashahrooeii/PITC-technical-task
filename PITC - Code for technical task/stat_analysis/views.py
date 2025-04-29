"""stat_analysis.views.py

This module implements views for statistical analysis of job execution data.
"""

from typing import Any, Dict
from datetime import datetime

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.utils import timezone
from django.core.cache import cache

from .models import Report, JobReportResult
from .serializers import ReportSerializer, JobReportResultSerializer
from .stat_utils import (
    calculate_job_stats,
    analyze_campaign_performance,
    analyze_customer_patterns,
)


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing Report instances."""

    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def get_queryset(self):
        """Get the list of reports with optional filtering."""
        queryset = self.queryset

        # Filter by year if provided
        year = self.request.query_params.get("year", None)
        if year:
            queryset = queryset.filter(year_from=year)

        # Filter by quarter if provided
        quarter = self.request.query_params.get("quarter", None)
        if quarter:
            queryset = queryset.filter(quarter_from=quarter)

        return queryset

    @action(detail=True, methods=["get"])
    def stats(self, request: Request, pk: int = None) -> Response:
        """Get detailed statistics for a report."""
        report = self.get_object()

        try:
            # Try to get stats from cache
            cache_key = f"report_stats_{report.id}"
            stats = cache.get(cache_key)

            if not stats:
                # Calculate stats if not in cache
                job_stats = calculate_job_stats(
                    report.quarter_from,
                    report.year_from,
                    report.quarter_to,
                    report.year_to,
                )

                serializer = JobReportResultSerializer(job_stats)
                stats = serializer.data

                # Cache for 1 hour
                cache.set(cache_key, stats, 3600)

            return Response(stats)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for advanced analytics endpoints."""

    def _parse_date_params(self, request: Request) -> tuple[datetime, datetime]:
        """Parse date parameters from request."""
        # Get date range parameters
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)

        if not start_date or not end_date:
            # Default to last 30 days if no dates provided
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=30)
        else:
            # Parse provided dates
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        return start_date, end_date

    @action(detail=False, methods=["get"])
    def campaign_performance(self, request: Request) -> Response:
        """Get campaign performance analytics."""
        try:
            start_date, end_date = self._parse_date_params(request)

            # Try to get from cache
            cache_key = f"campaign_perf_{start_date.date()}_{end_date.date()}"
            performance_data = cache.get(cache_key)

            if not performance_data:
                # Calculate if not in cache
                performance_data = analyze_campaign_performance(start_date, end_date)

                # Cache for 1 hour
                cache.set(cache_key, performance_data, 3600)

            return Response(performance_data)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def customer_patterns(self, request: Request) -> Response:
        """Get customer behavior pattern analytics."""
        try:
            start_date, end_date = self._parse_date_params(request)

            # Try to get from cache
            cache_key = f"customer_patterns_{start_date.date()}_{end_date.date()}"
            pattern_data = cache.get(cache_key)

            if not pattern_data:
                # Calculate if not in cache
                pattern_data = analyze_customer_patterns(start_date, end_date)

                # Cache for 1 hour
                cache.set(cache_key, pattern_data, 3600)

            return Response(pattern_data)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def performance_summary(self, request: Request) -> Response:
        """Get overall system performance summary."""
        try:
            start_date, end_date = self._parse_date_params(request)

            # Try to get from cache
            cache_key = f"perf_summary_{start_date.date()}_{end_date.date()}"
            summary_data = cache.get(cache_key)

            if not summary_data:
                # Get campaign performance
                campaign_data = analyze_campaign_performance(start_date, end_date)

                # Get customer patterns
                pattern_data = analyze_customer_patterns(start_date, end_date)

                # Calculate overall metrics
                total_orders = sum(
                    camp["total_jobs"] for camp in campaign_data.values()
                )
                avg_success_rate = (
                    sum(camp["success_rate"] for camp in campaign_data.values())
                    / len(campaign_data)
                    if campaign_data
                    else 0
                )

                summary_data = {
                    "period": {"start_date": start_date, "end_date": end_date},
                    "overall_metrics": {
                        "total_orders": total_orders,
                        "avg_success_rate": avg_success_rate,
                    },
                    "campaign_performance": campaign_data,
                    "customer_patterns": pattern_data,
                }

                # Cache for 1 hour
                cache.set(cache_key, summary_data, 3600)

            return Response(summary_data)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
