
from datetime import datetime, timezone as dt_timezone
from hashlib import sha256

from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings

from .models import User, RefreshToken as StoredRefreshToken
from .serializers import SignupSerializer, LoginSerializer


# Refresh Token 검증 및 DB 조회
def get_valid_refresh_token(raw_token):

    try:
        # 전달받은 Refresh Token 검증
        refresh = JWTRefreshToken(raw_token)

        # Refresh Token의 SHA-256 해시 생성
        token_hash = sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

        # DB에서 해당 토큰 조회
        stored_token = StoredRefreshToken.objects.select_for_update().select_related(
            "user"
        ).get(token_hash=token_hash)

        # 이미 폐기된 토큰인지 확인
        if stored_token.revoked_at is not None:
            raise ValueError("이미 폐기된 토큰입니다.")

        # DB에 기록된 만료 시각 확인
        if stored_token.expires_at <= timezone.now():
            raise ValueError("만료된 토큰입니다.")

        # 토큰의 사용자 ID와 DB의 사용자 ID 비교
        token_user_id = refresh[api_settings.USER_ID_CLAIM]

        if str(token_user_id) != str(stored_token.user.user_id):
            raise ValueError("사용자 정보가 일치하지 않습니다.")

        # 탈퇴한 사용자 확인
        if not stored_token.user.is_active:
            raise ValueError("탈퇴한 사용자입니다.")

        return stored_token, refresh

    except (
        TokenError,
        StoredRefreshToken.DoesNotExist,
        KeyError,
        TypeError,
        ValueError
    ):
        raise ValueError("유효하지 않은 Refresh Token입니다.")


# 회원가입 API
class SignupView(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")

        if email and User.objects.filter(email=email).exists():
            return Response(
                {
                    "status": 409,
                    "message": "이미 가입된 이메일입니다.",
                    "data": {}
                },
                status=status.HTTP_409_CONFLICT
            )

        serializer = SignupSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "status": 400,
                    "message": "입력값이 올바르지 않습니다.",
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()

        return Response(
            {
                "status": 201,
                "message": "회원가입이 완료되었습니다.",
                "data": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "created_at": user.created_at.isoformat()
                }
            },
            status=status.HTTP_201_CREATED
        )


# 로그인 API
class LoginView(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():

            if "non_field_errors" in serializer.errors:
                return Response(
                    {
                        "status": 401,
                        "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
                        "data": {}
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            return Response(
                {
                    "status": 400,
                    "message": "입력값이 올바르지 않습니다.",
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data["user"]

        # Access Token과 Refresh Token 발급
        refresh = JWTRefreshToken.for_user(user)
        access = refresh.access_token

        refresh_token = str(refresh)

        # Refresh Token 만료 시각 계산
        expires_at = datetime.fromtimestamp(
            refresh["exp"],
            tz=dt_timezone.utc
        )

        # Refresh Token 해시 생성
        token_hash = sha256(
            refresh_token.encode("utf-8")
        ).hexdigest()

        # 해시값만 DB에 저장
        with transaction.atomic():
            StoredRefreshToken.objects.create(
                user=user,
                token_hash=token_hash,
                expires_at=expires_at
            )

        return Response(
            {
                "status": 200,
                "message": "로그인에 성공했습니다.",
                "data": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "access": str(access),
                    "refresh": refresh_token
                }
            },
            status=status.HTTP_200_OK
        )


# 로그아웃 API
class LogoutView(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        raw_token = request.data.get("refresh")

        if not isinstance(raw_token, str) or not raw_token:
            return Response(
                {
                    "status": 400,
                    "message": "올바른 Refresh Token이 필요합니다.",
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():

                stored_token = get_valid_refresh_token(raw_token)

                # 토큰 폐기 시각 기록
                stored_token.revoked_at = timezone.now()
                stored_token.save(update_fields=["revoked_at"])

        except ValueError:
            return Response(
                {
                    "status": 401,
                    "message": "유효하지 않은 Refresh Token입니다.",
                    "data": {}
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(
            {
                "status": 200,
                "message": "로그아웃에 성공했습니다.",
                "data": {}
            },
            status=status.HTTP_200_OK
        )


# 토큰 재발급 API
class TokenRefreshView(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        raw_token = request.data.get("refresh")

        if not isinstance(raw_token, str) or not raw_token:
            return Response(
                {
                    "status": 400,
                    "message": "올바른 Refresh Token이 필요합니다.",
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():

                # 기존 Refresh Token 검증
                stored_token, _ = get_valid_refresh_token(raw_token)

                user = stored_token.user

                # 기존 Refresh Token 폐기
                stored_token.revoked_at = timezone.now()
                stored_token.save(update_fields=["revoked_at"])

                # 새로운 토큰 발급
                new_refresh = JWTRefreshToken.for_user(user)
                new_access = new_refresh.access_token

                new_refresh_token = str(new_refresh)

                # 새로운 Refresh Token 만료 시각
                expires_at = datetime.fromtimestamp(
                    new_refresh["exp"],
                    tz=dt_timezone.utc
                )

                # 새로운 Refresh Token 해시 생성
                token_hash = sha256(
                    new_refresh_token.encode("utf-8")
                ).hexdigest()

                # 새로운 해시값 DB 저장
                StoredRefreshToken.objects.create(
                    user=user,
                    token_hash=token_hash,
                    expires_at=expires_at
                )

        except ValueError:
            return Response(
                {
                    "status": 401,
                    "message": "유효하지 않은 Refresh Token입니다.",
                    "data": {}
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(
            {
                "status": 200,
                "message": "토큰이 재발급되었습니다.",
                "data": {
                    "access": str(new_access),
                    "refresh": new_refresh_token
                }
            },
            status=status.HTTP_200_OK
        )
