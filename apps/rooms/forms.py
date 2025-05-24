from django import forms
from .models import Room, AMENITIES_CHOICES

class RoomForm(forms.ModelForm):
    amenities = forms.MultipleChoiceField(
        choices=AMENITIES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Room
        fields = ['number', 'room_type', 'floor', 'amenities', 'price', 'is_available', 'image']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter room number'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter floor number'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # If editing an existing room, 'amenities' will be a list of strings (keys)
            # Set the initial value for the MultipleChoiceField
            self.fields['amenities'].initial = self.instance.amenities
        elif 'amenities' in self.data: # Handle POST data
             self.fields['amenities'].initial = self.data.getlist('amenities')

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0")
        return price

    def clean_amenities(self):
        # The form field 'amenities' will give a list of selected amenity keys.
        # This is already in the correct format for JSONField if it's a list of strings.
        return self.cleaned_data.get('amenities', [])

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Ensure amenities are saved correctly as a list (JSONField handles serialization)
        instance.amenities = self.cleaned_data.get('amenities', [])
        if commit:
            instance.save()
        return instance