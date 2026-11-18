
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import User


# 회원가입 데이터 검증
class SignupSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ["email", "password", "nickname"]

    # 이메일 중복 확인
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 가입된 이메일입니다.")

        return value

    # 회원가입 처리
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            nickname=validated_data["nickname"]
        )

        return user
