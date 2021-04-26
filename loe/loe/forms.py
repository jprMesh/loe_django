from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=False, help_text='Optional. Only used for account recovery password reset.')

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')
        help_texts = {
            'username': 'Required. Letters, digits, and @.+- only',
        }

    def clean(self):
        cleaned_data = super(SignUpForm, self).clean()
        username = cleaned_data.get('username')
        if username and get_user_model().objects.filter(username__iexact=username).exists():
            self.add_error('username', 'A user with that username already exists.')
        return cleaned_data
