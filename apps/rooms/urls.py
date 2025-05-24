from django.urls import path
from .views import RoomListView, RoomsAndSuitesView
from . import views

app_name = 'rooms'

urlpatterns = [
    path('', RoomsAndSuitesView, name='rooms_and_suites'),
    path('filter/', views.filter_rooms, name='filter_rooms'),
]