from django import forms
from apps.rooms.models import Room, ROOM_TYPE_CHOICES, AMENITIES_CHOICES

class RoomForm(forms.ModelForm):
    room_type = forms.ChoiceField(choices=ROOM_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    amenities = forms.MultipleChoiceField(
        choices=AMENITIES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Room
        fields = ['number', 'room_type', 'floor', 'amenities', 'is_available', 'image']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }