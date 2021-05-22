from django.conf.urls import url
from django.urls import path

from .views import index, search, evaluate, UserRegistrationView, UserLoginView, UserProfileView

urlpatterns = [
    path(r'', index, name='home'),
    url(r'search', search, name='search'),
    url(r'evaluate', evaluate, name='evaluate'),
    url(r'api/signUp', UserRegistrationView.as_view(), name='signUp'),
    url(r'api/signIn', UserLoginView.as_view(), name='signIn'),
    url(r'api/profile', UserProfileView.as_view(), name='profile')
]
