# fastapi_app/django_setup.py
import os
import django

def setup_django():
    # Point to the settings file inside 'email_project' folder
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "email_project.settings")
    django.setup()