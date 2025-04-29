"""stat_analysis.models.__init__.py

This module defines models to store statistical report
information.

A complete report is stored in Report model instance.
The Report model defines the reporting range.

Each Report has results of statistical analysis,
i.e. statistics of orders and jobs, which are stored in
OrderReportResult and JobReportResult models.
"""

from .report import Report
from .statistics import JobReportResult, OrderReportResult
