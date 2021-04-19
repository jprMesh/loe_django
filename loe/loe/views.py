from django.views import View
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect

from .forms import CaseInsensitiveUserCreationForm


class Signup(View):
    def post(self, request):
        form = CaseInsensitiveUserCreationForm(request.POST)
        if not form.is_valid():
            return self.get(request, retry=True)
        form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(request, user)
        return redirect('index')

    def get(self, request, retry=False):
        form = CaseInsensitiveUserCreationForm()
        return render(request, 'registration/signup.html', {'form': form, 'retry': retry})
