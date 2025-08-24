import random
from typing import Type

from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from .models import User, Token, GameResult
from .serializers import (
    UserRegistrationSerializer,
    UserRegistrationResponseSerializer,
    UserInfoSerializer,
    TokenRenewResponseSerializer,
    GamePlayResponseSerializer,
    GameResultSerializer
)


class UserViewSet(GenericViewSet):
    @extend_schema(
        request=UserRegistrationSerializer,
        responses={
            201: UserRegistrationResponseSerializer,
            400: OpenApiResponse(description="User with this username or phone number already exists"),
        },
        description="Register a new user and return token. Returns error if user already exists.",
    )
    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request) -> Response:
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        phone_number = serializer.validated_data["phone_number"]

        try:
            with transaction.atomic():
                user = User.objects.create(username=username, phone_number=phone_number)
                token = Token.objects.create(user=user)
        except IntegrityError:
            return Response(
                {"message": "User with this username or phone number already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = UserRegistrationResponseSerializer(
            instance=user,
            context={"token": token}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class GameViewSet(GenericViewSet):
    serializer_class = UserInfoSerializer

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "renew":
            return TokenRenewResponseSerializer
        elif self.action == "play":
            return GamePlayResponseSerializer
        elif self.action == "history":
            return GameResultSerializer
        return self.serializer_class

    def get_token(self) -> Token:
        token_str = self.kwargs["token"]
        return get_object_or_404(
            Token, token=token_str, is_active=True, expires_at__gt=timezone.now()
        )

    def get_user(self) -> User:
        token = self.get_token()
        return token.user

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.PATH,
                description="Enter UUID token for get user info",
                required=True,
            )
        ],
        responses={
            200: UserInfoSerializer,
            404: OpenApiResponse(description="Invalid or expired token"),
        },
        description="Retrieve user information by valid token.",
    )
    def retrieve(self, request, *args, **kwargs) -> Response:
        user = self.get_user()
        serializer = UserInfoSerializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="renew")
    def renew(self, request, *args, **kwargs) -> Response:
        token_str = self.kwargs.get("token")
        old_token = get_object_or_404(
            Token, token=token_str, expires_at__gt=timezone.now()
        )

        other_active_token_exists = (
            Token.objects.filter(user=old_token.user, is_active=True)
            .exclude(token=old_token.token)
            .exists()
        )

        if other_active_token_exists:
            return Response(
                {
                    "message": "You are using an old token. "
                               "You already have an active token for this user. Please use the active token to renew."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if old_token.is_active:
            old_token.is_active = False
            old_token.save()

        new_token = Token.objects.create(user=old_token.user)

        response_serializer = TokenRenewResponseSerializer(
            instance=old_token.user,
            context={"token": new_token}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID token for deactivation",
                required=True,
            )
        ],
        responses={
            200: OpenApiResponse(description="Token deactivated"),
            404: OpenApiResponse(description="Invalid or expired token"),
        },
        description="Deactivate the current token.",
    )
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, *args, **kwargs) -> Response:
        token = self.get_token()
        token.is_active = False
        token.save()
        return Response({"message": "Token deactivated"})

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID token for user authentication",
                required=True,
            )
        ],
        responses={
            200: GamePlayResponseSerializer,
            404: OpenApiResponse(description="Invalid or expired token"),
        },
        description="Play a game: generate a random number, determine win/lose, and calculate prize.",
    )
    @action(detail=True, methods=["post"], url_path="play")
    def play(self, request, *args, **kwargs) -> Response:
        user = self.get_user()
        random_number = random.randint(1, 1000)
        is_win = random_number % 2 == 0
        prize = 0.0

        if is_win:
            prize_tiers = [(900, 0.7), (600, 0.5), (300, 0.3), (0, 0.1)]
            for threshold, multiplier in prize_tiers:
                if random_number > threshold:
                    prize = random_number * multiplier
                    break

        game_result_obj = GameResult.objects.create(
            user=user, random_number=random_number, result=is_win, prize=round(prize, 2)
        )

        serializer = GameResultSerializer(game_result_obj)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID token",
                required=True,
            )
        ],
        responses={
            200: GameResultSerializer(many=True),
            404: OpenApiResponse(description="Invalid or expired token"),
        },
        description="Retrieve the last 3 game results for the user.",
    )
    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, *args, **kwargs) -> Response:
        user = self.get_user()
        results = user.game_results.order_by("-created_at")[:3]
        serializer = GameResultSerializer(results, many=True)
        return Response(serializer.data)
