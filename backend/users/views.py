
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User
from .serializers import SignupSerializer, LoginSerializer


# 회원가입 API
class SignupView(APIView):

    # 회원가입은 로그인하지 않은 사용자도 이용 가능
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # 이메일 중복 확인
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

        # 요청 데이터 검증
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

        # 회원가입 진행
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

    # 로그인은 인증하지 않은 사용자도 이용 가능
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        # 로그인 데이터 검증
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():

            # 이메일 또는 비밀번호 인증 실패
            if "non_field_errors" in serializer.errors:
                return Response(
                    {
                        "status": 401,
                        "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
                        "data": {}
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # 필수 입력값 누락 또는 이메일 형식 오류
            return Response(
                {
                    "status": 400,
                    "message": "입력값이 올바르지 않습니다.",
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 인증된 사용자 정보 가져오기
        user = serializer.validated_data["user"]

        return Response(
            {
                "status": 200,
                "message": "로그인에 성공했습니다.",
                "data": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname
                }
            },
            status=status.HTTP_200_OK
        )
