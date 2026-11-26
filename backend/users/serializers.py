
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

from django.contrib.auth import authenticate


# 로그인 데이터 검증
class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False
    )

    # 이메일과 비밀번호 확인
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password
        )

        if user is None:
            raise serializers.ValidationError(
                "이메일 또는 비밀번호가 올바르지 않습니다."
            )

        attrs["user"] = user

        return attrs

# 내 프로필 조회 데이터
class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "user_id",
            "email",
            "nickname",
            "profile_image_url",
            "created_at",
            "updated_at"
        ]
        read_only_fields = fields
