from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.base_user import BaseUserManager

from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from .models import User
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from GiftGenerator.settings import EMAIL_HOST_USER


def index(request):
    if request.method == 'POST':
        rating = request.POST['rating']
        email = request.POST['email']
        message = request.POST['message']
        subject = 'Feedback'
        message = f'Rating: {rating}/5\nEmail: {email}\nMessage: {message}\n'
        send_mail(subject, message, EMAIL_HOST_USER, [
            EMAIL_HOST_USER], fail_silently=False)
        messages.success(request, 'Form submission successful')
        return redirect('home')
    return render(request, 'index.html', {})


class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        request.POST._mutable = True
        if request.data.get('password', None) is None:
            request.data['password'] = BaseUserManager().make_random_password()

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            success = True
            status_code = status.HTTP_200_OK
            message = 'User registered successfully'
        else:
            success = False
            message = ''
            for value in serializer.errors.values():
                message += value[0][:-1].capitalize() + ';'
            status_code = status.HTTP_400_BAD_REQUEST

        response = {
            'success': success,
            'status code': status_code,
            'message': message,
        }
        return Response(response, status=status_code)


class UserLoginView(RetrieveAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        request.POST._mutable = True
        if request.data.get('password', None) is None:
            if User.objects.filter(email=request.data['email']).exists():
                user = User.objects.get(email=request.data['email'])
                request.data['password'] = user.password
            else:
                response = {
                    'success': False,
                    'status code': status.HTTP_400_BAD_REQUEST,
                    'message': 'User does not exists',
                    'token': None
                }
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            success = True
            status_code = status.HTTP_200_OK
            message = 'User logged in successfully'
            token = serializer.data['token']
        else:
            success = False
            message = ''
            for value in serializer.errors.values():
                message += value[0][:-1].capitalize() + ';'
            status_code = status.HTTP_400_BAD_REQUEST
            token = None

        response = {
            'success': success,
            'status code': status_code,
            'message': message,
            'token': token
        }
        return Response(response, status=status_code)


class UserProfileView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_class = JSONWebTokenAuthentication

    def get(self, request, *args, **kwargs):
        try:
            user_profile = User.objects.get(email=request.user)
            status_code = status.HTTP_200_OK
            response = {
                'success': True,
                'status code': status_code,
                'message': 'User profile fetched successfully',
                'data': [{
                    'name': user_profile.name,
                    'premium': user_profile.premium,
                    'theme': user_profile.theme,
                    'phone_number': user_profile.phone_number,
                    'birthday': user_profile.birthday,
                }]
            }
        except Exception as e:
            status_code = status.HTTP_400_BAD_REQUEST
            response = {
                'success': False,
                'status code': status.HTTP_400_BAD_REQUEST,
                'message': 'User does not exists',
                'error': str(e)
            }
        return Response(response, status=status_code)
