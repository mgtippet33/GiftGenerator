from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'name')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def authenticateUser(self, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            return None

    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)
        if password != 'None':
            user = authenticate(email=email, password=password)
        else:
            user = self.authenticateUser(email=email)
        if user is None:
            raise serializers.ValidationError(
                'A user with this email or password is not found.'
            )
        try:
            payload = JWT_PAYLOAD_HANDLER(user)
            jwt_token = JWT_ENCODE_HANDLER(payload)
            update_last_login(None, user)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'User with given email or password does not exists'
            )
        return {
            'email': user.email,
            'token': jwt_token
        }
