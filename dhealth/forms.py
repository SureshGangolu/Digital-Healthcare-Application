from django import forms
from django.contrib.auth.models import User
from .models import Profile, Slot

class DocForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['spec', 'license', 'address']

class PatForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['address']

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
class SlotForm(forms.ModelForm):
    class Meta:
        model = Slot
        fields = ['date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'time': forms.Select(choices=[
                ('09:00', '09:00 AM – 10:00 AM'),
                ('10:00', '10:00 AM – 11:00 AM'),
                ('11:00', '11:00 AM – 12:00 PM'),
                ('12:00', '12:00 PM – 01:00 PM'),
                ('13:00', '01:00 PM – 02:00 PM'),
                ('14:00', '02:00 PM – 03:00 PM'),
                ('15:00', '03:00 PM – 04:00 PM'),
                ('16:00', '04:00 PM – 05:00 PM'),
                ('17:00', '05:00 PM – 06:00 PM'),
            ], attrs={'class': 'form-select'})
        }
