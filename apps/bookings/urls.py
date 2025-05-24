# from django.urls import path
# from .views import booking_date_selection, booking_guest_info, booking_payment, booking_confirmation, booking_history, booking_detail, cancel_booking

# app_name = 'bookings'

# urlpatterns = [
#     path('booking-date-selection/<int:room_id>/', booking_date_selection, name='booking_date_selection'),
#     path('booking-guest-info/', booking_guest_info, name='booking_guest_info'),
#     path('booking-payment/', booking_payment, name='booking_payment'),
#     path('booking-confirmation/', booking_confirmation, name='booking_confirmation'),
#     path('booking-history/', booking_history, name='booking_history'),
#     path('booking-detail/<int:booking_id>/', booking_detail, name='booking_detail'),
#     path('cancel-booking/<int:booking_id>/', cancel_booking, name='cancel_booking'),
# ]



from django.urls import path
from .views import booking_date_selection, booking_guest_info, booking_payment, booking_confirmation, booking_history, booking_detail, cancel_booking, booking_pdf

app_name = 'bookings'

urlpatterns = [
    path('date-selection/<int:room_id>/', booking_date_selection, name='date_selection'),
    path('guest-info/', booking_guest_info, name='guest_info'),
    path('payment/', booking_payment, name='payment'),
    path('confirmation/', booking_confirmation, name='confirmation'),
    path('history/', booking_history, name='booking_history'),
    path('detail/<int:booking_id>/', booking_detail, name='booking_detail'),
    path('cancel/<int:booking_id>/', cancel_booking, name='cancel_booking'),
    path('pdf/<int:booking_id>/', booking_pdf, name='booking_pdf'),

]