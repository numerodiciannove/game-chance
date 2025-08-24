import re

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from game_api.models import User, GameResult, Token


class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=128)
    phone_number = serializers.IntegerField()

    @staticmethod
    def validate_username(value):
        value = value.lower()
        if not re.match(r"^[a-z0-9_-]+$", value):
            raise serializers.ValidationError(
                "Username can be (a-z), numbers (0-9), (-) and (_)"
            )
        return value

    @staticmethod
    def validate_phone_number(value):
        # TODO добавить валидацию через библиотеку phonenumbers

        value_str = str(value)

        if len(value_str) < 7:
            raise serializers.ValidationError(
                f"Phone number must contain at least 7 digits (found {len(value_str)})."
            )

        if len(value_str) > 20:
            raise serializers.ValidationError(
                f"Phone number must contain max 20 digits (found {len(value_str)})."
            )

        return value


class UserRegistrationResponseSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="id", read_only=True)
    token = serializers.SerializerMethodField()
    token_expires_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["user_id", "username", "token", "token_expires_at"]

    def get_token(self, obj):
        token: Token = self.context.get("token")
        return token.token if token else None

    def get_token_expires_at(self, obj):
        token: Token = self.context.get("token")
        return token.expires_at if token else None


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "phone_number"]


class TokenRenewResponseSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="id", read_only=True)
    token = serializers.SerializerMethodField()
    token_expires_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["user_id", "token", "token_expires_at"]

    def get_token(self, obj):
        token: Token = self.context.get("token")
        return token.token if token else None

    def get_token_expires_at(self, obj):
        token: Token = self.context.get("token")
        return token.expires_at if token else None



class GamePlayResponseSerializer(serializers.Serializer):
    random_number = serializers.IntegerField()
    result = serializers.ChoiceField(choices=[("win", "win"), ("lose", "lose")])
    prize = serializers.FloatField()


class GameResultSerializer(serializers.ModelSerializer):
    result = serializers.SerializerMethodField()

    class Meta:
        model = GameResult
        fields = ["random_number", "result", "prize"]

    @extend_schema_field(serializers.CharField)
    def get_result(self, obj):
        return "win" if obj.result else "lose"

