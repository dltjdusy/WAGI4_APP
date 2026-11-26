
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from .models import User, RefreshToken as StoredRefreshToken


class AuthAPITest(APITestCase):

    def setUp(self):
        self.email = "testuser@example.com"
        self.password = "Zebra!River#4829Cloud"
        self.nickname = "testuser"

        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            nickname=self.nickname
        )

        self.signup_url = "/api/v1/auth/signup"
        self.login_url = "/api/v1/auth/login"
        self.logout_url = "/api/v1/auth/logout"
        self.refresh_url = "/api/v1/auth/refresh"
        self.me_url = "/api/v1/users/me"

    def login(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.email,
                "password": self.password
            },
            format="json"
        )
        return response.data["data"]

    # 회원가입 성공
    def test_signup_success(self):
        response = self.client.post(
            self.signup_url,
            {
                "email": "newuser@example.com",
                "password": "River!Mountain#8392Tree",
                "nickname": "newuser"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email="newuser@example.com").exists()
        )

    # 중복 이메일 회원가입 실패
    def test_signup_duplicate_email(self):
        response = self.client.post(
            self.signup_url,
            {
                "email": self.email,
                "password": "River!Mountain#8392Tree",
                "nickname": "anotheruser"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    # 로그인 성공
    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.email,
                "password": self.password
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

    # 잘못된 비밀번호 로그인 실패
    def test_login_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {
                "email": self.email,
                "password": "Wrong!Password#8392"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Access Token으로 내 프로필 조회
    def test_me_with_valid_access_token(self):
        tokens = self.login()

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
        )

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.email)

    # Access Token 없이 내 프로필 조회 실패
    def test_me_without_access_token(self):
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 만료된 Access Token 인증 실패
    def test_me_with_expired_access_token(self):
        access = AccessToken.for_user(self.user)
        access["exp"] = int(
            (timezone.now() - timedelta(minutes=1)).timestamp()
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(access)}"
        )

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Refresh Token 재발급 성공 및 기존 토큰 재사용 차단
    def test_refresh_token_rotation(self):
        tokens = self.login()

        response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

        old_token_response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json"
        )

        self.assertEqual(
            old_token_response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    # 로그아웃 후 기존 Refresh Token 재사용 차단
    def test_logout_and_refresh_token_reuse(self):
        tokens = self.login()

        response = self.client.post(
            self.logout_url,
            {"refresh": tokens["refresh"]},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stored_token = StoredRefreshToken.objects.get(
            user=self.user
        )
        self.assertIsNotNone(stored_token.revoked_at)

        refresh_response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json"
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
