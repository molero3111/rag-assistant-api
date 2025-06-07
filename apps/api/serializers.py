from rest_framework.serializers import ModelSerializer, CharField
from django.contrib.auth.models import User

class RegisterSerializer(ModelSerializer):
    password = CharField(write_only=True)
    email = CharField(write_only=True)
    class Meta:
        model = User
        fields = ('username', 'password', 'email')
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']
        )
        return user

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
