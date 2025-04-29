from django.apps import AppConfig


class StatAnalysisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "stat_analysis"

    def ready(self):
        """Import signals when the app is ready."""
        import stat_analysis.signals
