import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horizonh_project_config.settings")
import django
django.setup()

   # This will use Django ORM to execute SQL
from django.db import connection

cursor = connection.cursor()
   # Drop tables in reverse order of dependencies
cursor.execute("DROP TABLE IF EXISTS bookings_booking")
cursor.execute("DROP TABLE IF EXISTS rooms_room")
   # Remove migration records
cursor.execute("DELETE FROM django_migrations WHERE app = 'bookings'")
cursor.execute("DELETE FROM django_migrations WHERE app = 'rooms'")