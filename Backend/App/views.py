import re

from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.base_user import BaseUserManager

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from .models import User, Present, Criterion
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from .functions import query, parse_twitter, parse_facebook
from .classification import make_classification_tools, page_predict
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


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def search(request):
    try:
        gender = request.data['gender']
        age = 'Дитина' if request.data['age'] < 13 else \
            'Підліток' if request.data['age'] < 19 else 'Дорослий'
        link = request.data['link']
        holiday = request.data['holiday']
        interests = request.data['interests']

        if link and re.search(r'facebook|twitter', link):
            model, text_transformer = make_classification_tools()
            if 'twitter' in link:
                parse_data = parse_twitter(link)
            else:
                parse_data = parse_facebook(link)

            interests += page_predict(
                page_data=parse_data,
                classifier=model,
                vectorizer=text_transformer
            )

        string = ''
        for interest in interests:
            string += f", '{interest}'"
        sql = \
            f"""
            select present.name, present.link, present.price, present.desc, present.rate
            from present
                    inner join present_criteria pc on present.id = pc.present_id
                    inner join criterion c on c.id = pc.criterion_id
                    inner join present_holidays ph on present.id = ph.present_id
                    inner join holiday h on h.id = ph.holiday_id
            group by present.id
            order by SUM(c.name in ('{gender}', '{age}'{string})) + SUM(h.name in ('{holiday}')) DESC, present.rate;
            """
        status_code = status.HTTP_200_OK
        response = {
            'success': True,
            'status code': status_code,
            'data': query(sql)[:10]
        }
    except:
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            'success': False,
            'status code': status_code
        }
    return Response(response, status=status_code)


class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        request.POST._mutable = True
        if request.data.get('password') is None:
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
        if request.data.get('password') is None:
            if User.objects.filter(email=request.data['email']).exists():
                user = User.objects.get(email=request.data['email'])
                request.data['password'] = 'None'
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
                    'birthday': user_profile.birthday
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
