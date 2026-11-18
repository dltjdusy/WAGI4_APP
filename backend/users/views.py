
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User
from .serializers import SignupSerializer


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
