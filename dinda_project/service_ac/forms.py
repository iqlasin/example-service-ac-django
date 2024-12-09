from django import forms
from .models import User
from django.contrib.auth.hashers import make_password

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'role', 'alamat', 'nomor_hp']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget = forms.Select(choices=User.ROLE_CHOICES)

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        label="Password"
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'alamat', 'nomor_hp']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])
        user.role = 'user'
        if commit:
            user.save()
        return user