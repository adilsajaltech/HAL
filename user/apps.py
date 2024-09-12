# user/apps.py
from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'user'

    def ready(self):
        # Import signals here to avoid AppRegistryNotReady error
        import user.signals
