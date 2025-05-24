from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q , Count
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json
from functools import wraps
from django.core.exceptions import PermissionDenied

from apps.rooms.models import Room, ROOM_TYPE_CHOICES, AMENITIES_CHOICES
from apps.rooms.templatetags.template_filter import get_item
from apps.dashboard.templatetags.dashboard_filters import remove_param
from apps.bookings.models import Booking


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff and not request.user.is_superuser:
            raise PermissionDenied("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@staff_required
def dashboard_home(request):
    return render(request, 'dashboard/dashboard.html')

# Dictionary to map amenity keys to Font Awesome icons


AMENITY_ICONS = {
    'wifi': 'bx bx-wifi',
    'tv': 'bx bx-tv',
    'ac': 'bx bx-cool',
    'safe': 'bx bx-shield-quarter',
    'balcony': 'bx bx-building-house',
    'room_service': 'bx bx-restaurant',
    'coffee': 'bx bx-coffee',
    'bath': 'bx bx-bath',
    'view': 'bx bx-landscape',
}


@login_required
@staff_required
def room_list(request):
    """
    View to display a list of rooms with filtering, sorting, and pagination.
    """
    # Get all rooms initially
    rooms = Room.objects.all()

    # Get filter parameters from request

    room_number = request.GET.get('room_number')
    room_types = request.GET.getlist('room_type')
    floors = request.GET.getlist('floor')
    amenities = request.GET.getlist('amenities')
    availability = request.GET.get('is_available')
    sort_option = request.GET.get('sort', 'number')
    search_query = request.GET.get('q')

    # Apply filters if provided
    if room_types:
        rooms = rooms.filter(room_type__in=room_types)

    if floors:
        rooms = rooms.filter(floor__in=floors)

    if amenities:
        # Filter rooms that have all selected amenities
        for amenity in amenities:
            rooms = rooms.filter(amenities__contains=[amenity])

    if availability:
        is_available = availability.lower() == 'true'
        rooms = rooms.filter(is_available=is_available)

    # Apply search if provided
    if search_query:
        rooms = rooms.filter(
            Q(number__icontains=search_query) |
            Q(room_type__icontains=search_query)
        )

    # Apply sorting
    if sort_option == 'room_type':
        rooms = rooms.order_by('room_type', 'number')
    elif sort_option == 'floor_asc':
        rooms = rooms.order_by('floor', 'number')
    elif sort_option == 'floor_desc':
        rooms = rooms.order_by('-floor', 'number')
    elif sort_option == 'price_asc':
        rooms = rooms.order_by('price', 'number')
    elif sort_option == 'price_desc':
        rooms = rooms.order_by('-price', 'number')
    elif sort_option == 'created_at':
        rooms = rooms.order_by('-created_at')
    else:  # Default to room number
        rooms = rooms.order_by('number')

    # Get counts for filters
    room_type_counts = dict(Room.objects.values_list('room_type').annotate(count=Count('id')).values_list('room_type', 'count'))
    floor_counts = dict(Room.objects.values_list('floor').annotate(count=Count('id')).values_list('floor', 'count'))

    # Get unique floors for filter options
    floor_list = Room.objects.values_list('floor', flat=True).distinct().order_by('floor')

    # Calculate amenity counts
    amenity_counts = {}
    for amenity_key, _ in AMENITIES_CHOICES:
        amenity_counts[amenity_key] = Room.objects.filter(amenities__contains=[amenity_key]).count()

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(rooms, 12)  # Show 12 rooms per page

    try:
        rooms = paginator.page(page)
    except PageNotAnInteger:
        rooms = paginator.page(1)
    except EmptyPage:
        rooms = paginator.page(paginator.num_pages)

    context = {
        'rooms': rooms,
        'room_types': dict(ROOM_TYPE_CHOICES),
        'all_amenities_choices': dict(AMENITIES_CHOICES),
        'amenity_icons': AMENITY_ICONS,
        'room_type_counts': room_type_counts,
        'floor_counts': floor_counts,
        'floor_list': floor_list,
        'amenity_counts': amenity_counts,
        'current_filters': {
            'room_types': room_types,
            'floors': floors,
            'amenities': amenities,
            'availability': availability,
            'sort': sort_option,
            'search': search_query,
        },
    }

    return render(request, 'dashboard/rooms/room_list.html', context)





@login_required
@staff_required
def room_add(request):
    """
    View to add a new room.
    """
    # Prepare amenity icons for display
    amenity_icons = {
        'wifi': 'bx-wifi',
        'tv': 'bx-tv',
        'ac': 'bx-wind',
        'safe': 'bx-shield-quarter',
        'balcony': 'bx-door-open',
        'room_service': 'bx-food-menu',
        'coffee': 'bx-coffee',
        'bath': 'bx-bath',
        'view': 'bx-landscape',
    }

    if request.method == 'POST':
        # Get form data
        number = request.POST.get('number')
        room_type = request.POST.get('room_type')
        floor = request.POST.get('floor')
        price = request.POST.get('price')  # Get price from form
        is_available = request.POST.get('is_available') == 'on'
        amenities = request.POST.getlist('amenities')
        image = request.FILES.get('image')

        # Validate data
        if not all([number, room_type, floor, price]):  # Include price in validation
            messages.error(request, "Please fill in all required fields.")
            return redirect('dashboard:room_add')

        # Check if room number already exists
        if Room.objects.filter(number=number).exists():
            messages.error(request, f"Room number {number} already exists.")
            return redirect('dashboard:room_add')

        try:
            # Convert floor to integer
            floor = int(floor)
            # Convert price to decimal
            price = float(price)

            # Create new room
            room = Room(
                number=number,
                room_type=room_type,
                floor=floor,
                price=price,  # Save price to model
                is_available=is_available,
                amenities=amenities
            )

            if image:
                room.image = image

            room.save()

            messages.success(request, f"Room {number} has been added successfully.")

            # If AJAX request, return JSON response
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f"Room {number} has been added successfully.",
                    'redirect':reverse('dashboard:room_list')
                })

            return redirect('dashboard:room_list')

        except ValueError:
            messages.error(request, "Invalid floor number or price. Please enter valid numbers.")
            return redirect('dashboard:room_add')

    context = {
        'room_types': ROOM_TYPE_CHOICES,
        'amenities': AMENITIES_CHOICES,
        'amenity_icons': amenity_icons,

    }

    return render(request, 'dashboard/rooms/room_add.html', context)

@login_required
@staff_required
def room_edit(request, pk):
    """
    View to edit an existing room.
    """
    # Get the room or return 404
    room = get_object_or_404(Room, id=pk)

    # Prepare amenity icons for display
    amenity_icons = {
        'wifi': 'bx-wifi',
        'tv': 'bx-tv',
        'ac': 'bx-wind',
        'safe': 'bx-shield-quarter',
        'balcony': 'bx-door-open',
        'room_service': 'bx-food-menu',
        'coffee': 'bx-coffee',
        'bath': 'bx-bath',
        'view': 'bx-landscape',
    }

    if request.method == 'POST':
        # Get form data
        number = request.POST.get('number')
        room_type = request.POST.get('room_type')
        floor = request.POST.get('floor')
        price = request.POST.get('price')  # Get price from form
        is_available = request.POST.get('is_available') == 'on'
        amenities = request.POST.getlist('amenities')
        image = request.FILES.get('image')
        clear_image = request.POST.get('clear_image') == 'true'

        # Validate data
        if not all([number, room_type, floor, price]):  # Include price in validation
            messages.error(request, "Please fill in all required fields.")
            return redirect('dashboard:room_edit', pk=pk)

        # Check if room number already exists (excluding this room)
        if Room.objects.filter(number=number).exclude(id=pk).exists():
            messages.error(request, f"Room number {number} already exists.")
            return redirect('dashboard:room_edit', pk=pk)

        try:
            # Convert floor to integer
            floor = int(floor)
            # Convert price to decimal
            price = float(price)

            # Update room
            room.number = number
            room.room_type = room_type
            room.floor = floor
            room.price = price  # Update price
            room.is_available = is_available
            room.amenities = amenities

            if image:
                room.image = image
            elif clear_image:
                room.image = None

            room.save()

            messages.success(request, f"Room {number} has been updated successfully.")

            # If AJAX request, return JSON response
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f"Room {number} has been updated successfully.",
                    'redirect': reverse('dashboard:room_list')
                })

            return redirect('dashboard:room_list')

        except ValueError:
            messages.error(request, "Invalid floor number or price. Please enter valid numbers.")
            return redirect('dashboard:room_edit', pk=pk)

    context = {
        'room': room,
        'room_types': ROOM_TYPE_CHOICES,
        'amenities': AMENITIES_CHOICES,
        'amenity_icons': amenity_icons,
    }

    return render(request, 'dashboard/rooms/room_edit.html', context)

@login_required
@staff_required
def room_delete(request, pk):
    """
    View to delete a room.
    """
    # Get the room or return 404
    room = get_object_or_404(Room, id=pk)

    if request.method == 'POST':
        room_number = room.number
        room.delete()

        messages.success(request, f"Room {room_number} has been deleted successfully.")

        # If AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Room {room_number} has been deleted successfully."
            })
        return redirect('dashboard:room_list')

    context = {
        'room': room,
    }

    return render(request, 'dashboard/rooms/room_delete.html', context)

@login_required
@staff_required
def batch_delete_rooms(request):
    """
    View to delete multiple rooms at once.
    """
    if request.method == 'POST':
        room_ids = request.POST.getlist('room_ids')

        if not room_ids:
            messages.error(request, "No rooms selected for deletion.")
            return redirect('dashboard:room_list')

        # Delete selected rooms
        deleted_count = 0
        for room_id in room_ids:
            try:
                room = Room.objects.get(id=room_id)
                room.delete()
                deleted_count += 1
            except Room.DoesNotExist:
                pass

        messages.success(request, f"{deleted_count} room(s) have been deleted successfully.")

        # If AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"{deleted_count} room(s) have been deleted successfully."
            })

        return redirect('dashboard:room_list')

    # If not POST, redirect to room list
    return redirect('dashboard:room_list')

@login_required
@staff_required
def batch_update_availability(request):
    """
    View to update availability for multiple rooms at once.
    """
    if request.method == 'POST':
        room_ids = request.POST.getlist('room_ids')
        availability = request.POST.get('availability')

        if not room_ids or availability not in ['available', 'unavailable']:
            messages.error(request, "Invalid request. Please select rooms and specify availability.")
            return redirect('dashboard:room_list')

        # Update availability for selected rooms
        is_available = availability == 'available'
        updated_count = 0

        for room_id in room_ids:
            try:
                room = Room.objects.get(id=room_id)
                room.is_available = is_available
                room.save()
                updated_count += 1
            except Room.DoesNotExist:
                pass

        status_text = "available" if is_available else "unavailable"
        messages.success(request, f"{updated_count} room(s) have been marked as {status_text}.")

        # If AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"{updated_count} room(s) have been marked as {status_text}."
            })

        return redirect('dashboard:room_list')

    # If not POST, redirect to room list
    return redirect('dashboard:room_list')

@login_required
@staff_required
def update_room_availability(request, pk):
    """
    View to toggle availability for a single room.
    """
    # Get the room or return 404
    room = get_object_or_404(Room, id=pk)

    if request.method == 'POST':
        # Toggle availability
        room.is_available = not room.is_available
        room.save()

        status_text = "available" if room.is_available else "unavailable"
        messages.success(request, f"Room {room.number} has been marked as {status_text}.")

        # If AJAX request, return JSON response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Room {room.number} has been marked as {status_text}.",
                'is_available': room.is_available
            })

        return redirect('dashboard:room_list')

    # If not POST, redirect to room list
    return redirect('dashboard:room_list')


    #########################################################
    # User Management
    #########################################################





User = get_user_model()

@login_required
@staff_required
def user_list(request):
    """
    View to display a list of users with filtering, sorting, and pagination.
    """
    # Get all users initially
    users = User.objects.all()

    # Get filter parameters from request
    roles = request.GET.getlist('role')
    status = request.GET.get('status')
    last_login = request.GET.get('last_login')
    sort_option = request.GET.get('sort', 'username')
    search_query = request.GET.get('q')

    # Apply filters if provided
    if roles:
        role_filters = Q()
        for role in roles:
            if role == 'admin':
                role_filters |= Q(is_superuser=True)
            elif role == 'staff':
                role_filters |= Q(is_staff=True, is_superuser=False)
            elif role == 'user':
                role_filters |= Q(is_staff=False, is_superuser=False)
        users = users.filter(role_filters)

    if status:
        is_active = status.lower() == 'active'
        users = users.filter(is_active=is_active)

    if last_login:
        now = timezone.now()
        if last_login == 'today':
            users = users.filter(last_login__date=now.date())
        elif last_login == 'week':
            users = users.filter(last_login__gte=now - timedelta(days=7))
        elif last_login == 'month':
            users = users.filter(last_login__gte=now - timedelta(days=30))
        elif last_login == 'never':
            users = users.filter(last_login__isnull=True)

    # Apply search if provided
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Apply sorting
    if sort_option == 'email':
        users = users.order_by('email')
    elif sort_option == 'date_joined':
        users = users.order_by('-date_joined')
    elif sort_option == 'last_login':
        # Put users who have never logged in at the end
        users = users.order_by(
            '-last_login__isnull',  # Nulls last
            '-last_login'  # Most recent first
        )
    else:  # Default to username
        users = users.order_by('username')

    # Get counts for filters
    admin_count = User.objects.filter(is_superuser=True).count()
    staff_count = User.objects.filter(is_staff=True, is_superuser=False).count()
    user_count = User.objects.filter(is_staff=False, is_superuser=False).count()

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(users, 12)  # Show 12 users per page

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    context = {
        'users': users,
        'admin_count': admin_count,
        'staff_count': staff_count,
        'user_count': user_count,
        'current_filters': {
            'roles': roles,
            'status': status,
            'last_login': last_login,
            'sort': sort_option,
            'search': search_query,
        },
    }

    return render(request, 'dashboard/users/user_list.html', context)

@login_required
@staff_required
def user_add(request):
    """
    View to add a new user.
    """
    if request.method == 'POST':
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Get form data
                username = request.POST.get('username')
                email = request.POST.get('email')
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')
                is_staff = request.POST.get('is_staff') == 'on'
                is_active = request.POST.get('is_active') == 'on'

                # Validate data
                if User.objects.filter(username=username).exists():
                    return JsonResponse({
                        'success': False,
                        'message': f'Username {username} already exists.'
                    })

                if User.objects.filter(email=email).exists():
                    return JsonResponse({
                        'success': False,
                        'message': f'Email {email} already exists.'
                    })

                if password1 != password2:
                    return JsonResponse({
                        'success': False,
                        'message': 'Passwords do not match.'
                    })

                # Create new user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_active=is_active
                )

                return JsonResponse({
                    'success': True,
                    'message': f'User {username} created successfully.',
                    'user_id': user.id
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error creating user: {str(e)}'
                })

        # Handle regular form submission
        else:
            try:
                # Get form data
                username = request.POST.get('username')
                email = request.POST.get('email')
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')
                is_staff = request.POST.get('is_staff') == 'on'
                is_active = request.POST.get('is_active') == 'on'

                # Validate data
                if User.objects.filter(username=username).exists():
                    messages.error(request, f'Username {username} already exists.')
                    return redirect('dashboard:users_add')

                if User.objects.filter(email=email).exists():
                    messages.error(request, f'Email {email} already exists.')
                    return redirect('dashboard:users_add')

                if password1 != password2:
                    messages.error(request, 'Passwords do not match.')
                    return redirect('dashboard:users_add')

                # Create new user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_active=is_active
                )

                messages.success(request, f'User {username} created successfully.')
                return redirect('dashboard:users')

            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
                return redirect('dashboard:users_add')

    # GET request - show the form
    return render(request, 'dashboard/users/user_add.html')

@login_required
@staff_required
def user_edit(request, user_id):
    """
    View to edit an existing user.
    """
    # Get the user or return 404
    user_to_edit = get_object_or_404(User, id=user_id)

    # Prevent editing superusers unless you are a superuser
    if user_to_edit.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit this user.')
        return redirect('dashboard:user_list')

    if request.method == 'POST':
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Get form data
                username = request.POST.get('username')
                email = request.POST.get('email')
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')
                is_staff = request.POST.get('is_staff') == 'on'
                is_active = request.POST.get('is_active') == 'on'

                # Check if username already exists (excluding this user)
                if User.objects.filter(username=username).exclude(id=user_id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': f'Username {username} already exists.'
                    })

                # Check if email already exists (excluding this user)
                if User.objects.filter(email=email).exclude(id=user_id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': f'Email {email} already exists.'
                    })

                # Update user data
                user_to_edit.username = username
                user_to_edit.email = email
                user_to_edit.first_name = first_name
                user_to_edit.last_name = last_name

                # Only update staff status if you're a superuser or if the user is not a superuser
                if request.user.is_superuser or not user_to_edit.is_superuser:
                    user_to_edit.is_staff = is_staff
                    user_to_edit.is_active = is_active

                # Update password if provided
                if password1 and password2:
                    if password1 != password2:
                        return JsonResponse({
                            'success': False,
                            'message': 'Passwords do not match.'
                        })
                    user_to_edit.set_password(password1)

                user_to_edit.save()

                return JsonResponse({
                    'success': True,
                    'message': f'User {username} updated successfully.'
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error updating user: {str(e)}'
                })

        # Handle regular form submission
        else:
            try:
                # Get form data
                username = request.POST.get('username')
                email = request.POST.get('email')
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')
                is_staff = request.POST.get('is_staff') == 'on'
                is_active = request.POST.get('is_active') == 'on'

                # Check if username already exists (excluding this user)
                if User.objects.filter(username=username).exclude(id=user_id).exists():
                    messages.error(request, f'Username {username} already exists.')
                    return redirect('dashboard:user_edit', user_id=user_id)

                # Check if email already exists (excluding this user)
                if User.objects.filter(email=email).exclude(id=user_id).exists():
                    messages.error(request, f'Email {email} already exists.')
                    return redirect('dashboard:user_edit', user_id=user_id)

                # Update user data
                user_to_edit.username = username
                user_to_edit.email = email
                user_to_edit.first_name = first_name
                user_to_edit.last_name = last_name

                # Only update staff status if you're a superuser or if the user is not a superuser
                if request.user.is_superuser or not user_to_edit.is_superuser:
                    user_to_edit.is_staff = is_staff
                    user_to_edit.is_active = is_active

                # Update password if provided
                if password1 and password2:
                    if password1 != password2:
                        messages.error(request, 'Passwords do not match.')
                        return redirect('dashboard:user_edit', user_id=user_id)
                    user_to_edit.set_password(password1)

                user_to_edit.save()

                messages.success(request, f'User {username} updated successfully.')
                return redirect('dashboard:user_list')

            except Exception as e:
                messages.error(request, f'Error updating user: {str(e)}')
                return redirect('dashboard:user_edit', user_id=user_id)

    # GET request - show the form with user data
    context = {
        'user': user_to_edit,
    }

    return render(request, 'dashboard/users/user_edit.html', context)

@login_required
@staff_required
def user_delete(request, user_id):
    """
    View to delete a user.
    """
    # Get the user or return 404
    user_to_delete = get_object_or_404(User, id=user_id)

    # Prevent deleting superusers unless you are a superuser
    if user_to_delete.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete this user.')
        return redirect('dashboard:user_list')

    # Prevent users from deleting themselves
    if user_to_delete.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('dashboard:user_list')

    if request.method == 'POST':
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                username = user_to_delete.username
                user_to_delete.delete()

                return JsonResponse({
                    'success': True,
                    'message': f'User {username} deleted successfully.'
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error deleting user: {str(e)}'
                })

        # Handle regular form submission
        else:
            try:
                username = user_to_delete.username
                user_to_delete.delete()

                messages.success(request, f'User {username} deleted successfully.')
                return redirect('dashboard:user_list')

            except Exception as e:
                messages.error(request, f'Error deleting user: {str(e)}')
                return redirect('dashboard:user_delete', user_id=user_id)

    # GET request - show confirmation page
    context = {
        'user': user_to_delete,
    }

    return render(request, 'dashboard/users/user_delete.html', context)

@login_required
@staff_required
@require_POST
def batch_delete_users(request):
    """
    View to delete multiple users at once.
    """
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])

        # Get users to delete
        users_to_delete = User.objects.filter(id__in=user_ids)

        # Filter out superusers if current user is not a superuser
        if not request.user.is_superuser:
            users_to_delete = users_to_delete.filter(is_superuser=False)

        # Filter out current user
        users_to_delete = users_to_delete.exclude(id=request.user.id)

        if not users_to_delete.exists():
            return JsonResponse({
                'success': False,
                'message': 'No users found to delete or you do not have permission to delete the selected users.'
            })

        # Delete users
        count = users_to_delete.count()
        users_to_delete.delete()

        return JsonResponse({
            'success': True,
            'message': f'{count} user(s) deleted successfully.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting users: {str(e)}'
        })

@login_required
@staff_required
@require_POST
def batch_update_status(request):
    """
    View to update status for multiple users at once.
    """
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        is_active = data.get('is_active', True)

        # Get users to update
        users_to_update = User.objects.filter(id__in=user_ids)

        # Filter out superusers if current user is not a superuser
        if not request.user.is_superuser:
            users_to_update = users_to_update.filter(is_superuser=False)

        if not users_to_update.exists():
            return JsonResponse({
                'success': False,
                'message': 'No users found to update or you do not have permission to update the selected users.'
            })

        # Update users
        count = users_to_update.count()
        users_to_update.update(is_active=is_active)

        return JsonResponse({
            'success': True,
            'message': f'{count} user(s) marked as {"active" if is_active else "inactive"} successfully.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating user status: {str(e)}'
        })

@login_required
@staff_required
@require_POST
def update_user_status(request, user_id):
    """
    View to update status for a single user.
    """
    try:
        # Get the user or return 404
        user_to_update = get_object_or_404(User, id=user_id)

        # Prevent updating superusers unless you are a superuser
        if user_to_update.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to update this user.'
            })

        data = json.loads(request.body)
        is_active = data.get('is_active', True)

        # Update user
        user_to_update.is_active = is_active
        user_to_update.save()

        return JsonResponse({
            'success': True,
            'message': f'User {user_to_update.username} marked as {"active" if is_active else "inactive"} successfully.',
            'username': user_to_update.username
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating user status: {str(e)}'
        })






# booking views



@login_required
@staff_required
def booking_list(request):
    """
    View to display a list of bookings with filtering, sorting, and pagination.
    """
    # Get all bookings, prefetch related user and room for efficiency
    bookings_queryset = Booking.objects.select_related("user", "room").all()

    # Get filter parameters from request
    status_filter = request.GET.getlist("status")
    room_type_filter = request.GET.getlist("room_type")
    date_filter = request.GET.get("date_filter") # e.g., 'upcoming', 'past', 'today'
    search_query = request.GET.get("q")
    sort_option = request.GET.get("sort", "-created_at") # Default sort by newest booking

    # Apply filters
    if status_filter:
        bookings_queryset = bookings_queryset.filter(status__in=status_filter)

    if room_type_filter:
        bookings_queryset = bookings_queryset.filter(room__room_type__in=room_type_filter)

    today = timezone.now().date()
    if date_filter == "upcoming":
        bookings_queryset = bookings_queryset.filter(check_in_date__gte=today, status__in=["pending", "confirmed"])
    elif date_filter == "past":
        bookings_queryset = bookings_queryset.filter(check_out_date__lt=today)
    elif date_filter == "active_today":
        bookings_queryset = bookings_queryset.filter(check_in_date__lte=today, check_out_date__gte=today, status="confirmed")

    # Apply search if provided (searches guest name, email, booking number, room number)
    if search_query:
        bookings_queryset = bookings_queryset.filter(
            Q(guest_name__icontains=search_query) |
            Q(guest_email__icontains=search_query) |
            Q(booking_number__icontains=search_query) |
            Q(room__number__icontains=search_query)
        )

    # Apply sorting
    valid_sort_options = [
        "check_in_date", "-check_in_date",
        "check_out_date", "-check_out_date",
        "created_at", "-created_at",
        "guest_name", "-guest_name",
        "room__number", "-room__number",
        "status", "-status",
    ]
    if sort_option in valid_sort_options:
        bookings_queryset = bookings_queryset.order_by(sort_option)
    else:
        bookings_queryset = bookings_queryset.order_by("-created_at") # Default sort

    # Pagination
    page = request.GET.get("page", 1)
    paginator = Paginator(bookings_queryset, 15) # Show 15 bookings per page

    try:
        bookings = paginator.page(page)
    except PageNotAnInteger:
        bookings = paginator.page(1)
    except EmptyPage:
        bookings = paginator.page(paginator.num_pages)

    context = {
        "bookings": bookings,
        "booking_statuses": Booking.STATUS_CHOICES,
        "room_types": ROOM_TYPE_CHOICES,  # Use the imported constant directly
        "current_filters": {
            "status": status_filter,
            "room_type": room_type_filter,
            "date_filter": date_filter,
            "search": search_query,
        },
        "current_sort": sort_option,
        "page_title": "Booking Management",
    }

    return render(request, "dashboard/bookings/booking_list.html", context)

# --- End of booking_list view ---




# --- Add this view to your existing dashboard views.py ---

@login_required
@staff_required
def booking_detail(request, pk):
    """
    View to display the details of a specific booking.
    """
    # Get the booking or return 404, prefetch related user and room
    booking = get_object_or_404(Booking.objects.select_related("user", "room"), pk=pk)

    context = {
        "booking": booking,
        "page_title": f"Booking Detail - {booking.booking_number}", # Example page title
    }

    return render(request, "dashboard/bookings/booking_detail.html", context)

# --- End of booking_detail view ---




# --- Add this view to your existing dashboard views.py ---

@login_required
@staff_required
def booking_cancel(request, pk):
    """
    View to handle booking cancellation.
    GET: Displays a confirmation page.
    POST: Processes the cancellation.
    """
    booking = get_object_or_404(Booking, pk=pk)

    # Check if the booking can be cancelled
    if booking.status in ["cancelled", "completed"]:
        messages.warning(request, f"Booking {booking.booking_number} is already {booking.get_status_display()} and cannot be cancelled.")
        return redirect("dashboard:booking_detail", pk=pk) # Redirect back to detail page

    if request.method == "POST":
        # Process the cancellation
        booking.status = "cancelled"
        # Optional: Add logic here to record the cancellation reason if needed
        # reason = request.POST.get("reason")
        # booking.cancellation_reason = reason
        booking.save()

        messages.success(request, f"Booking {booking.booking_number} has been successfully cancelled.")

        # Optional: Add logic here to send a notification email to the guest
        # send_cancellation_email(booking)

        # Redirect back to the booking list page after cancellation
        return redirect("dashboard:booking_list")

    # Handle GET request: Show confirmation page
    context = {
        "booking": booking,
        "page_title": f"Confirm Cancellation - {booking.booking_number}",
    }
    return render(request, "dashboard/bookings/booking_confirm_cancel.html", context)
