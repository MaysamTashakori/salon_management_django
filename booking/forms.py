from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Appointment, Review
from datetime import datetime
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import Appointment

from datetime import datetime
from django import forms
from .models import Appointment, Stylist
from django import forms
from persiantools.jdatetime import JalaliDateTime
from .models import Appointment, Service, Stylist

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['service', 'stylist', 'date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'min': datetime.now().date().isoformat()
            }),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'stylist': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].label = 'تاریخ'
        self.fields['time'].label = 'ساعت'
        self.fields['service'].label = 'خدمت'
        self.fields['stylist'].label = 'آرایشگر'

        if user and hasattr(user, 'stylist'):
            # Remove the stylist from available options if they are a stylist
            self.fields['stylist'].queryset = Stylist.objects.exclude(user=user)


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 4})
        }

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('phone_number', 'email')




class AppointmentBookingForm(forms.ModelForm):
    jalali_date = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control datepicker-input'}),
        label='تاریخ'
    )
    
    time_slots = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='ساعت'
    )
    
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='خدمت'
    )
    
    stylist = forms.ModelChoiceField(
        queryset=Stylist.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='آرایشگر'
    )

    class Meta:
        model = Appointment
        fields = ['service', 'stylist']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['stylist'].queryset = Stylist.objects.none()
        
        if 'service' in self.data:
            try:
                service_id = int(self.data.get('service'))
                self.fields['stylist'].queryset = Stylist.objects.filter(
                    services__id=service_id,
                    is_available=True
                )
            except (ValueError, TypeError):
                pass

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['service', 'stylist', 'date', 'time']