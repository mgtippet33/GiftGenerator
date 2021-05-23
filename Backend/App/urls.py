from django.conf.urls import url
from django.urls import path

from .views import index, search, evaluate, get_history, change_fields, upcoming_holidays, add_holiday, UserRegistrationView, UserLoginView, UserProfileView

urlpatterns = [
    path(r'', index, name='home'),
    url(r'search', search, name='search'),
    url(r'evaluate', evaluate, name='evaluate'),
    url(r'change_fields', change_fields, name='change_fields'),
    url(r'get_history', get_history, name='get_history'),
    url(r'upcoming_holidays', upcoming_holidays, name='upcoming_holidays'),
    url(r'add_holiday', add_holiday, name='add_holiday'),
    url(r'api/signUp', UserRegistrationView.as_view(), name='signUp'),
    url(r'api/signIn', UserLoginView.as_view(), name='signIn'),
    url(r'api/profile', UserProfileView.as_view(), name='profile')
]
