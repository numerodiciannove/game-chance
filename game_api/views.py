import random

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import User, Token, GameResult
from .serializers import (
    UserRegistrationSerializer,
    UserRegistrationResponseSerializer,
    UserInfoSerializer,
    TokenRenewResponseSerializer,
    GamePlayResponseSerializer,
    GameResultSerializer,
    AllTokensSerializer,
)


class UserViewSet(GenericViewSet):
    @extend_schema(
        request=UserRegistrationSerializer,
        responses={201: UserRegistrationResponseSerializer},
        description="Register a new user and return token",
    )
    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.create(
            username=serializer.validated_data["username"],
            phone_number=serializer.validated_data["phone_number"],
        )

        token = Token.objects.create(
            user=user
        )  # TODO Добавить хеширование через ключ из сеттингс

        response_serializer = UserRegistrationResponseSerializer(
            instance={
                "user_id": user.id,
                "username": user.username,
                "token": token.token,
                "token_expires_at": token.expires_at,
            }
        )

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class GameViewSet(GenericViewSet):
    serializer_class = UserInfoSerializer

    def get_serializer_class(self):
        if self.action == "renew":
            return TokenRenewResponseSerializer
        elif self.action == "play":
            return GamePlayResponseSerializer
        elif self.action == "history":
            return GameResultSerializer
        return self.serializer_class

    def get_token(self):
        token_str = self.kwargs["token"]
        return get_object_or_404(
            Token, token=token_str, is_active=True, expires_at__gt=timezone.now()
        )

    def get_user(self):
        token = self.get_token()
        return token.user

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.PATH,  # убрал в свагере повтороное поле ввода параметров
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
    def retrieve(self, request, *args, **kwargs):
        user = self.get_user()
        serializer = UserInfoSerializer(user)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.PATH,
                description="Enter UUID token for update",
                required=True,
            )
        ],
        responses={
            200: TokenRenewResponseSerializer,
            400: OpenApiResponse(description="Another active token already exists"),
            404: OpenApiResponse(description="Invalid or expired token"),
        },
        description="""Renews a user's token.
        It deactivates the old token (if active) and creates a new one.
        Returns an error if another active token already exists for the user.""",
    )
    @action(detail=True, methods=["post"], url_path="renew")
    def renew(self, request, *args, **kwargs):
        """
        Renews a user's token.
        It deactivates the old token (if active) and creates a new one.
        Returns an error if another active token already exists for the user.
        """
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

        response_data = {
            "user_id": old_token.user.id,
            "token": new_token.token,
            "token_expires_at": new_token.expires_at,
        }

        response_serializer = TokenRenewResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

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
    def deactivate(self, request, *args, **kwargs):
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
    def play(self, request, *args, **kwargs):
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
    def history(self, request, *args, **kwargs):
        user = self.get_user()
        results = user.game_results.order_by("-created_at")[:3]
        serializer = GameResultSerializer(results, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=str,
                location=OpenApiParameter.PATH,
                description="User id for testing",
                required=True,
            )
        ],
        responses={
            200: AllTokensSerializer(many=True),
            404: OpenApiResponse(description="Invalid or expired token"),
        },
        description="Retrieve all tokens for a user for testing",
    )
    @action(detail=True, methods=["get"], url_path="all-tokens")
    def all_tokens(self, request, *args, **kwargs):
        """
        Retrieves all tokens associated with a user, including active and inactive ones.
        This method is for testing and debugging purposes.
        """
        user = User.objects.get(id=kwargs["id"])
        all_tokens = Token.objects.filter(user=user)
        serializer = AllTokensSerializer(all_tokens, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
