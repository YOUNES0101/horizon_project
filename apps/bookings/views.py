from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation # Import InvalidOperation
import uuid
import json
from xhtml2pdf import pisa
from io import BytesIO

from .models import Booking
from apps.rooms.models import Room # Assuming this is the correct path

@login_required
def booking_date_selection(request, room_id):
    """
    First step of booking process: Date selection
    """
    room = get_object_or_404(Room, id=room_id)

    # Check if room is generally available (e.g., not under maintenance)
    if not room.is_available:
        messages.error(request, "Sorry, this room is currently unavailable for booking.")
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Get today's date and default check-out date (tomorrow)
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # Get existing bookings for this room to disable dates in calendar
    # Fetch bookings that are active (pending or confirmed) and haven't ended yet
    existing_bookings = Booking.objects.filter(
        room=room,
        status__in=["pending", "confirmed"], # Only consider active bookings
        check_out_date__gte=today
    ).values("check_in_date", "check_out_date")

    # Format bookings for the calendar: Create a list of dates that are booked
    booked_dates = []
    for booking in existing_bookings:
        current_date = booking["check_in_date"]
        # Loop from check-in date up to (but not including) check-out date
        while current_date < booking["check_out_date"]:
            booked_dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

    context = {
        "room": room,
        "today": today.strftime("%Y-%m-%d"),
        "tomorrow": tomorrow.strftime("%Y-%m-%d"),
        # Pass the list of booked dates as JSON for the frontend calendar
        "booked_dates": json.dumps(booked_dates),
    }

    # Ensure your booking_date_selection.html template uses 'booked_dates'
    # in the date picker (e.g., Flatpickr) 'disable' option like:
    # disable: JSON.parse('{{ booked_dates|escapejs }}'),
    return render(request, "bookings/booking_date_selection.html", context)

@login_required
def booking_guest_info(request):
    """
    Second step of booking process: Guest information
    """
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Get data from previous step
    room_id = request.POST.get("room_id")
    check_in_date_str = request.POST.get("check_in_date")
    check_out_date_str = request.POST.get("check_out_date")
    num_guests = request.POST.get("num_guests", 1)

    # Validate data presence
    if not all([room_id, check_in_date_str, check_out_date_str, num_guests]):
        messages.error(request, "Missing required booking information.")
        # Redirect back to home or room list if essential data is missing
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Get room
    try:
        room = get_object_or_404(Room, id=room_id)
    except Exception as e:
        messages.error(request, f"Could not find the specified room. Error: {str(e)}")
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Convert and validate dates and guests
    try:
        check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out_date_str, "%Y-%m-%d").date()
        num_guests = int(num_guests)
    except (ValueError, TypeError):
        messages.error(request, "Invalid date format or number of guests.")
        return redirect("bookings:date_selection", room_id=room_id)

    # Basic date validation
    if check_in_date < timezone.now().date():
        messages.error(request, "Check-in date cannot be in the past.")
        return redirect("bookings:date_selection", room_id=room_id)
    if check_out_date <= check_in_date:
        messages.error(request, "Check-out date must be after check-in date.")
        return redirect("bookings:date_selection", room_id=room_id)
    # Removed capacity check as it's not in the Room model
    # if num_guests > room.capacity:
    #      messages.error(request, f"The selected room capacity ({room.capacity}) is less than the number of guests ({num_guests}).")
    #      return redirect("bookings:date_selection", room_id=room_id)

    # *** Optional: Early Overlap Check (Recommended for UX) ***
    # Check if the selected dates are still available before proceeding
    overlapping_bookings = Booking.objects.filter(
        room=room,
        status__in=["pending", "confirmed"],
        check_in_date__lt=check_out_date,  # Existing booking starts before new one ends
        check_out_date__gt=check_in_date   # Existing booking ends after new one starts
    )
    if overlapping_bookings.exists():
        # Use room.number as per the model
        messages.error(request, f"Sorry, Room {room.number} is no longer available for the selected dates ({check_in_date.strftime('%b %d')} - {check_out_date.strftime('%b %d')}). Please choose different dates.")
        return redirect("bookings:date_selection", room_id=room.id)
    # *** End of Optional Early Check ***

    # Calculate nights and price
    nights = (check_out_date - check_in_date).days
    room_price = room.price # Use the price field from the Room model
    subtotal = room_price * nights
    # Ensure tax calculation uses Decimal
    taxes_fees = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
    total_price = subtotal + taxes_fees

    context = {
        "room": room,
        "check_in_date": check_in_date.strftime("%Y-%m-%d"), # Pass as string for hidden input
        "check_out_date": check_out_date.strftime("%Y-%m-%d"),# Pass as string for hidden input
        "num_guests": num_guests,
        "nights": nights,
        "subtotal": subtotal,
        "taxes_fees": taxes_fees,
        "total_price": total_price,
        "user": request.user, # Pass user for pre-filling form
    }

    return render(request, "bookings/booking_guest_info.html", context)

@login_required
def booking_payment(request):
    """
    Third step of booking process: Payment Simulation
    """
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Get data from previous step (guest info form)
    room_id = request.POST.get("room_id")
    check_in_date_str = request.POST.get("check_in_date")
    check_out_date_str = request.POST.get("check_out_date")
    num_guests = request.POST.get("num_guests")
    guest_name = request.POST.get("guest_name")
    guest_email = request.POST.get("guest_email")
    guest_phone = request.POST.get("guest_phone")
    special_requests = request.POST.get("special_requests", "")
    total_price_str = request.POST.get("total_price")

    # Validate data presence
    if not all([room_id, check_in_date_str, check_out_date_str, num_guests, guest_name, guest_email, guest_phone, total_price_str]):
        messages.error(request, "Missing required booking or guest information.")
        # Redirect intelligently - perhaps back to guest info if possible, else to start
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Get room
    try:
        room = get_object_or_404(Room, id=room_id)
    except Exception as e:
        messages.error(request, f"Could not find the specified room. Error: {str(e)}")
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Convert dates, guests, and price
    try:
        check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out_date_str, "%Y-%m-%d").date()
        num_guests = int(num_guests)
        # Convert total_price carefully
        total_price = Decimal(total_price_str.replace("$", "").replace(",", ""))
    except (ValueError, TypeError, InvalidOperation):
        messages.error(request, "Invalid data format received.")
        return redirect("bookings:date_selection", room_id=room_id)

    # Recalculate nights and price components for display consistency
    nights = (check_out_date - check_in_date).days
    room_price = room.price # Use the price field from the Room model
    subtotal = room_price * nights
    taxes_fees = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
    calculated_total_price = subtotal + taxes_fees

    # Security check: Compare passed total_price with recalculated price
    # Allow for small floating point differences if necessary, but Decimal should be precise
    if abs(total_price - calculated_total_price) > Decimal("0.01"):
         messages.warning(request, "Price discrepancy detected. Please review your booking details.")
         # Use the recalculated price for safety
         total_price = calculated_total_price

    context = {
        "room": room,
        "check_in_date": check_in_date.strftime("%Y-%m-%d"),
        "check_out_date": check_out_date.strftime("%Y-%m-%d"),
        "num_guests": num_guests,
        "guest_name": guest_name,
        "guest_email": guest_email,
        "guest_phone": guest_phone,
        "special_requests": special_requests,
        "nights": nights,
        "subtotal": subtotal,
        "taxes_fees": taxes_fees,
        "total_price": total_price,
    }

    return render(request, "bookings/booking_payment.html", context)

@login_required
def booking_confirmation(request):
    """
    Final step of booking process: Confirmation & Saving Booking
    """
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Get all data from payment form
    room_id = request.POST.get("room_id")
    check_in_date_str = request.POST.get("check_in_date")
    check_out_date_str = request.POST.get("check_out_date")
    num_guests = request.POST.get("num_guests")
    guest_name = request.POST.get("guest_name")
    guest_email = request.POST.get("guest_email")
    guest_phone = request.POST.get("guest_phone")
    special_requests = request.POST.get("special_requests", "")
    total_price_str = request.POST.get("total_price")
    payment_method = request.POST.get("payment_method", "credit_card")

    # Validate data presence
    if not all([room_id, check_in_date_str, check_out_date_str, num_guests, guest_name, guest_email, guest_phone, total_price_str]):
        messages.error(request, "Missing required booking information for confirmation.")
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Get room
    try:
        room = get_object_or_404(Room, id=room_id)
    except Exception as e:
        messages.error(request, f"Could not find the specified room. Error: {str(e)}")
        return redirect("rooms:rooms_and_suites") # Adjust redirect if needed

    # Convert dates, guests, and price
    try:
        check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out_date_str, "%Y-%m-%d").date()
        num_guests = int(num_guests)
        total_price = Decimal(total_price_str.replace("$", "").replace(",", ""))
    except (ValueError, TypeError, InvalidOperation):
        messages.error(request, "Invalid data format received.")
        # Redirect back to date selection as the dates might be corrupted
        return redirect("bookings:date_selection", room_id=room_id)

    # *** CRUCIAL: Final Overlap Check Before Saving ***
    # Query for any existing confirmed or pending bookings that conflict with the requested dates.
    overlapping_bookings = Booking.objects.filter(
        room=room,
        status__in=["pending", "confirmed"],  # Check against active bookings
        check_in_date__lt=check_out_date,    # Existing booking starts before the new one ends
        check_out_date__gt=check_in_date     # Existing booking ends after the new one starts
    )

    if overlapping_bookings.exists():
        # If overlap found, redirect back to date selection with an error message.
        # Use room.number as per the model
        messages.error(request, f"Sorry, Room {room.number} is no longer available for the selected dates ({check_in_date.strftime('%b %d')} - {check_out_date.strftime('%b %d')}). Please choose different dates.")
        return redirect("bookings:date_selection", room_id=room.id)
    # *** End of Final Overlap Check ***

    # Determine payment status (simulation)
    # Assume payment is successful for card/paypal for this simulation
    payment_status = payment_method in ["credit_card", "paypal"]

    # Create the booking object
    try:
        booking = Booking.objects.create(
            user=request.user,
            room=room,
            # booking_number is generated by model's save method
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            num_guests=num_guests,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            special_requests=special_requests,
            status="confirmed", # Set status to confirmed upon successful creation
            total_price=total_price,
            payment_method=payment_method,
            payment_status=payment_status
        )
    except Exception as e:
        # Catch potential database errors during creation
        messages.error(request, f"An error occurred while saving your booking. Please try again. Error: {str(e)}")
        return redirect("bookings:date_selection", room_id=room.id)

    # Optional: Send confirmation email (ensure function is defined and working)
    # try:
    #     send_booking_confirmation_email(booking)
    # except Exception as mail_error:
    #     messages.warning(request, f"Booking confirmed, but could not send confirmation email: {mail_error}")

    messages.success(request, "Your booking has been confirmed successfully!")

    context = {
        "booking": booking,
    }

    return render(request, "bookings/booking_confirmation.html", context)

# --- Other Views (booking_history, booking_detail, cancel_booking) ---
# These views seem less relevant to the double-booking issue,
# but ensure they handle booking statuses correctly.

@login_required
def booking_history(request):
    """
    View to display user's booking history
    """
    today = timezone.now().date()
    user_bookings = Booking.objects.filter(user=request.user)

    upcoming_bookings = user_bookings.filter(
        status__in=["pending", "confirmed"],
        check_out_date__gte=today
    ).order_by("check_in_date")

    past_bookings = user_bookings.filter(
        status__in=["confirmed", "completed"], # Include completed bookings
        check_out_date__lt=today
    ).order_by("-check_out_date")

    cancelled_bookings = user_bookings.filter(
        status="cancelled"
    ).order_by("-updated_at")

    context = {
        "upcoming_bookings": upcoming_bookings,
        "past_bookings": past_bookings,
        "cancelled_bookings": cancelled_bookings,
    }
    # Assuming this template exists in your dashboard app structure
    return render(request, "dashboard/bookings/booking_history.html", context)

@login_required
def booking_detail(request, booking_id):
    """
    View to display detailed information about a specific booking
    """
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    context = {
        "booking": booking,
    }
    # Assuming this template exists in your dashboard app structure
    return render(request, "dashboard/bookings/booking_detail.html", context)

@login_required
def cancel_booking(request, booking_id):
    """
    View to cancel a booking
    """
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Check if booking can be cancelled
    if booking.status not in ["pending", "confirmed"]:
        messages.error(request, f"This booking cannot be cancelled (Status: {booking.get_status_display()}).")
        # Use the correct redirect URL name from your urls.py
        # Assuming 'profile:bookings' is correct based on previous templates
        return redirect("profile:bookings") # Adjust redirect if needed

    # Prevent cancelling too close to check-in? (Optional business logic)
    # if booking.check_in_date <= timezone.now().date() + timedelta(days=1):
    #     messages.error(request, "Bookings cannot be cancelled within 24 hours of check-in.")
    #     return redirect("profile:bookings")

    if request.method == "POST":
        # Update booking status
        booking.status = "cancelled"
        # You might want a field for cancellation reason
        # booking.cancel_reason = request.POST.get('cancel_reason', '')
        booking.save()

        # Optional: Send cancellation email
        # send_booking_cancellation_email(booking)

        messages.success(request, "Your booking has been cancelled successfully.")
        return redirect("profile:bookings") # Adjust redirect if needed

    # If GET request, you might render a confirmation page before cancelling
    # Or handle cancellation directly via POST as implemented here
    context = {
        "booking": booking
    }
    # Assuming you have a template for cancellation confirmation if needed via GET
    # return render(request, 'bookings/booking_cancel_confirm.html', context)
    # For now, redirect if GET request tries to access directly
    messages.info(request, "To cancel a booking, please use the cancel button on the booking details page.")
    return redirect("profile:bookings") # Adjust redirect if needed


# --- Utility Functions (Example: Email Sending - Implement these) ---

def send_booking_confirmation_email(booking):
    subject = f"Your Booking Confirmation at HORIZONH - Ref: {booking.booking_number}"
    context = {"booking": booking}
    # Ensure these email templates exist
    # html_message = render_to_string("emails/booking_confirmation_email.html", context)
    # plain_message = render_to_string("emails/booking_confirmation_email.txt", context)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = booking.guest_email
    # Ensure email backend is configured in settings.py
    # send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
    print(f"--- Sending confirmation email to {to_email} (Simulation) ---")
    print(f"Subject: {subject}")
    # print(f"Body:\n{plain_message}")
    print("----------------------------------------------------------")

def send_booking_cancellation_email(booking):
    subject = f"Your Booking Cancellation at HORIZONH - Ref: {booking.booking_number}"
    context = {"booking": booking}
    # Ensure these email templates exist
    # html_message = render_to_string("emails/booking_cancellation_email.html", context)
    # plain_message = render_to_string("emails/booking_cancellation_email.txt", context)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = booking.guest_email
    # send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
    print(f"--- Sending cancellation email to {to_email} (Simulation) ---")
    print(f"Subject: {subject}")
    # print(f"Body:\n{plain_message}")
    print("----------------------------------------------------------")

@login_required
def booking_pdf(request, booking_id):
    """
    Generate PDF of booking confirmation using xhtml2pdf
    """
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Render the template to HTML
    html_string = render_to_string('bookings/booking_pdf.html', {
        'booking': booking,
        'base_url': request.build_absolute_uri('/')[:-1],  # Remove trailing slash
    })

    # Create a BytesIO buffer to receive the PDF data
    buffer = BytesIO()

    # Generate PDF
    pisa_status = pisa.CreatePDF(
        html_string,
        dest=buffer,
        encoding='utf-8'
    )

    if pisa_status.err:
        return HttpResponse('We had some errors generating the PDF')

    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Create the HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="booking_confirmation_{booking.booking_number}.pdf"'

    return response


