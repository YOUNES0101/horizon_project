from django.urls import path

from .views import room_list, dashboard_home,room_edit,room_delete,room_add, user_list, user_add, user_edit, user_delete, booking_list, booking_detail, booking_cancel

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_home, name='dashboard_home'),
    path('rooms/', room_list, name='room_list'),
    path('rooms/add/', room_add, name='room_add'),
    path('rooms/<int:pk>/edit/', room_edit, name='room_edit'),
    path('rooms/<int:pk>/delete/', room_delete, name='room_delete'),
    path('users/', user_list, name='user_list'),
    path('users/add/', user_add, name='user_add'),
    path('users/<int:user_id>/edit/', user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', user_delete, name='user_delete'),
    path("bookings/", booking_list, name="booking_list"),
    path("bookings/<int:pk>/", booking_detail, name="booking_detail"),
    path("bookings/<int:pk>/cancel/", booking_cancel, name="booking_cancel"),

]

