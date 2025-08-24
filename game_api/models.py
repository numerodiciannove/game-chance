import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


class User(models.Model):
    username = models.CharField(max_length=128, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)


class GameResult(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="game_results"
    )
    random_number = models.IntegerField()
    result = models.BooleanField()  # Serializer control (true/win - false/lose)
    prize = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)
