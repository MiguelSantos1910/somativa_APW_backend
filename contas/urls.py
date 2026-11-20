from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MeView,
    UsuarioViewSet,
    LogoutView
)

router = DefaultRouter()

router.register(
    "usuarios",
    UsuarioViewSet,
    basename="usuarios"
)

urlpatterns = [
    path(
        "me/",
        MeView.as_view(),
        name="me"
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "",
        include(router.urls),
    )
]