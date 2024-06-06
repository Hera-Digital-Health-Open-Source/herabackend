from django.apps import AppConfig


class ChildHealthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'child_health'
    verbose_name = "Pregnancy & Child Health"

    def ready(self):
        super().ready()
        import child_health.signals
