
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# 사용자 생성 및 관리
class UserManager(BaseUserManager):
    def create_user(self, email, nickname, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수입니다.")

        if not nickname:
            raise ValueError("닉네임은 필수입니다.")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            nickname=nickname,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user


# 사용자 정보
class User(AbstractBaseUser):
    user_id = models.BigAutoField(primary_key=True)

    email = models.EmailField(
        max_length=255,
        unique=True
    )

    # Django의 비밀번호 해싱 기능을 사용하면서
    # DB 컬럼명은 ERD에 맞춰 password_hash로 지정
    password = models.CharField(
        max_length=255,
        db_column="password_hash"
    )

    nickname = models.CharField(max_length=255)

    profile_image_url = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # ERD에 없는 Django 기본 last_login 컬럼은 사용하지 않음
    last_login = None

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]

    # 탈퇴한 사용자는 인증할 수 없도록 처리
    @property
    def is_active(self):
        return self.deleted_at is None

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email

# 리프레시 토큰 정보
class RefreshToken(models.Model):
    token_id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="refresh_tokens"
    )

    token_hash = models.CharField(
        max_length=500,
        unique=True
    )

    expires_at = models.DateTimeField()

    revoked_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "refresh_tokens"

    def __str__(self):
        return self.user.email