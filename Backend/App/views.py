import os
import datetime
import re

from django.http import HttpResponse, Http404
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

from .models import User, Present, Criterion, History, Holiday
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from .functions import query, parse_twitter, parse_facebook, get_upcoming, add_event
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


def download_apk(request):
    file_base_name = 'GiftGenerator'
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = BASE_DIR + '/App/download/' + file_base_name + '.apk'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(
                fh.read(), content_type="application/force_download")
            response['Content-Disposition'] = 'inline; filename=' + \
                os.path.basename(file_path)
            return response
    raise Http404


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def search(request):
    try:
        gender = request.data['gender']
        age = 'Дитина' if int(request.data['age']) < 13 else \
            'Підліток' if int(request.data['age']) < 19 else 'Дорослий'
        link = request.data['link']
        holiday = request.data['holiday']
        interests = request.data['interests'].split(',')

        if link != 'null' and re.search(r'facebook|twitter', link):
            if 'twitter' in link:
                parse_data = parse_twitter(link)
            else:
                parse_data = parse_facebook(link)
            if parse_data:
                model, text_transformer = make_classification_tools()
                interests += page_predict(
                    page_data=parse_data,
                    classifier=model,
                    vectorizer=text_transformer
                )

        string = ''
        if interests[0] != 'null':
            for interest in interests:
                string += f", '{interest}'"

        search_sql = \
            f"""
            select present.id, present.name, present.link, present.price, present.desc, present.rate
            from present
                    inner join present_criteria pc on present.id = pc.present_id
                    inner join criterion c on c.id = pc.criterion_id
                    inner join present_holidays ph on present.id = ph.present_id
                    inner join holiday h on h.id = ph.holiday_id
            group by present.id
            having (c.name in ('{gender}', 'Інше'))
            order by 2 * SUM(c.name in ('{age}'{string})) + SUM(h.name in ('{holiday}')) DESC, rand()
            limit 10;
            """
        search_data = query(search_sql)

        if request.data.get('email'):
            email = request.data['email']
            user_id = User.objects.get(email=email).id
            holiday_id = Holiday.objects.get(name=holiday, owner_id=1).id
            History.objects.filter(user_id=user_id).delete()

            current_date = datetime.datetime.now()
            gender_number = {'Чоловік': 0, 'Жінка': 1, 'Інше': 2}[gender]
            for i in search_data[:5]:
                present_id = i.get('id')
                h = History(link=link, age=request.data['age'], gender=gender_number, present_id=present_id,
                            user_id=user_id, holiday_id=holiday_id, date=current_date)
                h.save()
                if interests[0] != 'null':
                    for name in interests:
                        h.criteria.add(Criterion.objects.get(name=name))

        status_code = status.HTTP_200_OK
        response = {
            'success': True,
            'status code': status_code,
            'message': 'Request processed successfully',
            'data': search_data
        }
    except:
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            'success': False,
            'status code': status_code,
            'message': 'Bad request'
        }
    return Response(response, status=status_code)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def evaluate(request):
    try:
        present_id = int(request.data['id'])
        rating = int(request.data['rating'])
        present = Present.objects.get(id=present_id)

        current_rating = present.rate
        new_rating = (current_rating + rating * 20) // 2
        present.rate = new_rating
        present.save()

        status_code = status.HTTP_200_OK
        response = {
            'success': True,
            'status code': status_code,
            'message': 'Gift successfully evaluated'
        }
    except:
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            'success': False,
            'status code': status_code,
            'message': 'Gift with such id not found'
        }
    return Response(response, status=status_code)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAuthenticated])
def change_fields(request):
    try:
        user = User.objects.get(email=request.data['email'])

        if request.data.get('new_email'):
            user.email = request.data['new_email']
        if request.data.get('name'):
            user.name = request.data['name']
        if request.data.get('password'):
            user.set_password(request.data['password'])
        if request.data.get('premium') is not None:
            user.premium = int(request.data['premium'])
        if request.data.get('theme') is not None:
            user.theme = int(request.data['theme'])
        user.save()

        status_code = status.HTTP_200_OK
        response = {
            'success': True,
            'status code': status_code,
            'message': 'Fields changed successfully'
        }
    except:
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            'success': False,
            'status code': status_code,
            'message': 'User does not exists'
        }
    return Response(response, status=status_code)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_history(request):
    try:
        user = User.objects.get(email=request.data['email'])
        success = True
        status_code = status.HTTP_200_OK
        message = 'History received successfully'
        data = {
            'date': '',
            'link': '',
            'age': '',
            'gender': '',
            'holiday': '',
            'criteria': [],
            'presents': []
        }
        genders = {0: 'Чоловік', 1: 'Жінка', 2: 'Інше'}

        if not user.premium:
            success = False
            status_code = status.HTTP_400_BAD_REQUEST
            message = 'Not premium user'
            data = {}
        else:
            historys = History.objects.filter(user_id=user.id)
            if historys.exists():
                data['date'] = datetime.datetime.strftime(
                    historys[0].date, '%d-%m-%Y')
                data['link'] = historys[0].link
                data['age'] = historys[0].age
                data['gender'] = genders[historys[0].gender]
                data['holiday'] = historys[0].holiday.name
                data['criteria'] = [criterion['name']
                                    for criterion in historys[0].criteria.values()]
                for history in historys:
                    present = Present.objects.get(id=history.present_id)
                    data['presents'].append({
                        'id': present.id,
                        'name': present.name,
                        'link': present.link,
                        'price': present.price,
                        'desc': present.desc,
                        'rate': present.rate
                    })
            else:
                success = False
                status_code = status.HTTP_400_BAD_REQUEST
                message = 'User has no history'
                data = {}
        response = {
            'success': success,
            'status code': status_code,
            'message': message,
            'data': data
        }
    except:
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            'success': False,
            'status code': status_code,
            'message': 'User does not exists'
        }
    return Response(response, status=status_code)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def upcoming_holidays(request):
    try:
        if request.data.get('email'):
            user = User.objects.get(email=request.data['email'])
            holidays = get_upcoming(user.id)
        else:
            holidays = get_upcoming(None)

        status_code = status.HTTP_200_OK

        response = {
            'success': True,
            'status code': status_code,
            'message': 'Upcoming holidays received successfully',
            'data': {
                'holidays': holidays
            }
        }
    except:
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            'success': False,
            'status code': status_code,
            'message': 'User does not exists'
        }
    return Response(response, status=status_code)


@api_view(['POST'])
@authentication_classes([JSONWebTokenAuthentication])
@permission_classes([IsAuthenticated])
def add_holiday(request):
    try:
        user = User.objects.get(email=request.data['email'])
        status_code = status.HTTP_200_OK
        success = True
        message = 'Holiday added successfully'
        date = datetime.datetime.strptime(
            request.data['date'], '%Y-%m-%d').date()

        if not add_event(request.data['name'], date, user.id):
            success = False
            message = 'Holiday already exists'

        response = {
            'success': success,
            'status code': status_code,
            'message': message
        }
    except:
        status_code = status.HTTP_400_BAD_REQUEST
        response = {
            'success': False,
            'status code': status_code,
            'message': 'User does not exists'
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
        except:
            status_code = status.HTTP_400_BAD_REQUEST
            response = {
                'success': False,
                'status code': status.HTTP_400_BAD_REQUEST,
                'message': 'User does not exists'
            }
        return Response(response, status=status_code)
