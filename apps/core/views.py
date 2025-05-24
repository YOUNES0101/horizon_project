from django.shortcuts import render
from django.views.generic import TemplateView
from allauth.account.views import SignupView as AllauthSignupView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

# Create your views here.

class HomeView(TemplateView):
    template_name = 'core/home.html'

class AboutView(TemplateView):
    template_name = 'core/about.html'

class ContactView(TemplateView):
    template_name = 'core/contact.html'

class SignupView(AllauthSignupView):
    template_name = 'core/signup.html'

@require_POST
def custom_logout(request):
    logout(request)
    return redirect('core:home')


