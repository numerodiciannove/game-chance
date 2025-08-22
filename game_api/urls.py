from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, GameViewSet

router = DefaultRouter()
router.register("user", UserViewSet, basename="user")

game_viewset_patterns = [
    path(
        "game/<uuid:token>/",
        GameViewSet.as_view({"get": "retrieve"}),
        name="game-detail",
    ),
    path(
        "game/<uuid:token>/renew/",
        GameViewSet.as_view({"post": "renew"}),
        name="game-renew",
    ),
    path(
        "game/<uuid:token>/deactivate/",
        GameViewSet.as_view({"post": "deactivate"}),
        name="game-deactivate",
    ),
    path(
        "game/<uuid:token>/play/",
        GameViewSet.as_view({"post": "play"}),
        name="game-play",
    ),
    path(
        "game/<uuid:token>/history/",
        GameViewSet.as_view({"get": "history"}),
        name="game-history",
    ),
    path(
        "game/<id>/test_get_user_all_tokens/",
        GameViewSet.as_view({"get": "all_tokens"}),
        name="game-get_all_tokens",
    ),
]

urlpatterns = [
    path("", include(router.urls)),
    *game_viewset_patterns,
]
