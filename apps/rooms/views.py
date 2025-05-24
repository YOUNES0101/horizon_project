from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .models import Room, AMENITIES_CHOICES, ROOM_TYPE_CHOICES
from .forms import RoomForm # Import the new form
from django.db.models import Count, Case, When, IntegerField
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

def RoomListView(request):
    return render(request, 'rooms/room_list.html')

def RoomsAndSuitesView(request):
    """
    Enhanced view to display a list of available rooms and suites with filtering capabilities.
    """
    # Start with all rooms and apply filters if provided
    rooms_query = Room.objects.all()

    # Get filter parameters from request
    room_number = request.GET.get('room_number')
    room_type = request.GET.getlist('room_type')
    amenities = request.GET.getlist('amenities')
    floor = request.GET.getlist('floor')
    available_only = request.GET.get('available_only', 'on')
    sort_by = request.GET.get('sort_by', 'recommended')

    # Apply filters
    if room_type:
        rooms_query = rooms_query.filter(room_type__in=room_type)

    if amenities:
        # Filter rooms that have ALL selected amenities
        for amenity in amenities:
            rooms_query = rooms_query.filter(amenities__contains=[amenity])

    if floor:
        floor_numbers = [int(f) for f in floor if f.isdigit()]
        if floor_numbers:
            rooms_query = rooms_query.filter(floor__in=floor_numbers)


    # Filter by availability if requested
    if available_only == 'on':
        rooms_query = rooms_query.filter(is_available=True)

    # Apply sorting
    if sort_by == 'price_low':
        rooms_query = rooms_query.order_by('price')
    elif sort_by == 'price_high':
        rooms_query = rooms_query.order_by('-price')
    elif sort_by == 'room_number':
        rooms_query = rooms_query.order_by('number')
    elif sort_by == 'floor_low':
        rooms_query = rooms_query.order_by('floor', 'number')
    elif sort_by == 'floor_high':
        rooms_query = rooms_query.order_by('-floor', 'number')
    else:  # recommended or default
        rooms_query = rooms_query.order_by('price', 'number')

    # Get counts for filters
    room_type_counts = {}
    for type_key, type_name in ROOM_TYPE_CHOICES:
        room_type_counts[type_key] = Room.objects.filter(room_type=type_key).count()

    # Get counts for amenities
    amenity_counts = {}
    for amenity_key, amenity_name in AMENITIES_CHOICES:
        # Count rooms that have this amenity
        amenity_counts[amenity_key] = Room.objects.filter(amenities__contains=[amenity_key]).count()

    # Get list of all floors and their counts
    floor_list = Room.objects.values_list('floor', flat=True).distinct().order_by('floor')
    floor_counts = {}
    for floor_num in floor_list:
        floor_counts[floor_num] = Room.objects.filter(floor=floor_num).count()

    # Prepare a dictionary to map amenity keys to Font Awesome icons
    amenity_icons = {
        'wifi': 'fas fa-wifi',
        'tv': 'fas fa-tv',
        'ac': 'fas fa-snowflake',
        'safe': 'fas fa-shield-alt',
        'balcony': 'fas fa-archway',
        'room_service': 'fas fa-concierge-bell',
        'coffee': 'fas fa-coffee',
        'bath': 'fas fa-bath',
        'view': 'fas fa-image',
    }

    context = {
        'rooms': rooms_query,
        'amenity_icons': amenity_icons,
        'all_amenities_choices': dict(AMENITIES_CHOICES),
        'room_types': dict(ROOM_TYPE_CHOICES),
        'room_type_counts': room_type_counts,
        'amenity_counts': amenity_counts,
        'floor_list': floor_list,
        'floor_counts': floor_counts,
        'selected_room_types': room_type,
        'selected_amenities': amenities,
        'selected_floors': floor,
        'available_only': available_only,
        'sort_by': sort_by,
    }

    return render(request, 'rooms/rooms_and_suites.html', context)

@require_http_methods(["POST"])
def filter_rooms(request):
    try:
        data = json.loads(request.body)
        room_types = data.get('roomTypes', [])
        amenities = data.get('amenities', [])
        floors = data.get('floors', [])
        availability = data.get('availability', False)

        # Start with all rooms
        rooms = Room.objects.all()

        # Apply filters
        if room_types:
            rooms = rooms.filter(room_type__in=room_types)

        if amenities:
            rooms = rooms.filter(amenities__overlap=amenities)

        if floors:
            rooms = rooms.filter(floor__in=floors)

        if availability:
            rooms = rooms.filter(is_available=True)

        # Serialize rooms data
        rooms_data = []
        for room in rooms:
            rooms_data.append({
                'id': room.id,
                'number': room.number,
                'room_type': room.get_room_type_display(),
                'floor': room.floor,
                'price': str(room.price),
                'is_available': room.is_available,
                'amenities': list(room.amenities),
                'image_url': room.get_image_url(),
            })

        return JsonResponse({
            'rooms': rooms_data,
            'count': len(rooms_data)
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

# class ManageRoomListView(ListView):
#     model = Room
#     template_name = 'rooms/dashboard/manage_rooms.html' # New template
#     context_object_name = 'rooms'
#     paginate_by = 10 # Optional: for pagination

#     def get_queryset(self):
#         return Room.objects.all().order_by('number')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['page_title'] = "Manage Rooms"
#         # For displaying amenity names nicely
#         context['amenity_names'] = dict(AMENITIES_CHOICES)
#         return context

# class RoomCreateView(SuccessMessageMixin, CreateView):
#     model = Room
#     form_class = RoomForm
#     template_name = 'rooms/dashboard/room_form.html' # New template
#     success_url = reverse_lazy('rooms:manage_rooms') # Redirect after success
#     success_message = "Room \"%(number)s\" was created successfully!"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['page_title'] = "Add New Room"
#         context['form_title'] = "Create a New Room"
#         context['submit_button_text'] = "Create Room"
#         return context

#     def form_valid(self, form):
#         # You can add custom logic here before saving if needed
#         return super().form_valid(form)

# class RoomUpdateView(SuccessMessageMixin, UpdateView):
#     model = Room
#     form_class = RoomForm
#     template_name = 'rooms/dashboard/room_form.html' # Re-use form template
#     success_url = reverse_lazy('rooms:manage_rooms')
#     success_message = "Room \"%(number)s\" was updated successfully!"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['page_title'] = f"Edit Room {self.object.number}"
#         context['form_title'] = f"Editing Room: {self.object.number}"
#         context['submit_button_text'] = "Update Room"
#         return context

#     def form_valid(self, form):
#         # You can add custom logic here before saving if needed
#         return super().form_valid(form)

# class RoomDeleteView(SuccessMessageMixin, DeleteView):
#     model = Room
#     template_name = 'rooms/dashboard/room_confirm_delete.html' # New template
#     success_url = reverse_lazy('rooms:manage_rooms')

#     def get_success_message(self, cleaned_data):
#         return f"Room \"{self.object.number}\" was deleted successfully!"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['page_title'] = f"Delete Room {self.object.number}"
#         context['form_title'] = f"Confirm Deletion of Room: {self.object.number}"
#         return context

#     def post(self, request, *args, **kwargs):
#         messages.success(self.request, self.get_success_message(None))
#         return super().post(request, *args, **kwargs)
