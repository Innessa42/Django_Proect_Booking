"""
URL configuration for DjangoProjectRente project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from rente.views import (
    RegisterViewSet,
    UserViewSet,
    ListingViewSet,
    BookingViewSet,
    ReviewViewSet,
    ViewHistoryViewSet,
    SearchHistoryViewSet, LogInAPIView, LogOutAPIView
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Главный роутер
router = DefaultRouter()
router.register(r'auth/register', RegisterViewSet, basename='register')
router.register(r'users', UserViewSet)
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'views', ViewHistoryViewSet, basename='views')
router.register(r'searches', SearchHistoryViewSet, basename='searches')

#  Вложенные маршруты для отзывов: /listings/<listing_pk>/reviews/
listing_router = NestedSimpleRouter(router, r'listings', lookup='listing')
listing_router.register(r'reviews', ReviewViewSet, basename='listing-reviews')


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(listing_router.urls)),
]

urlpatterns += [
    path('api/login/', LogInAPIView.as_view(), name='token_obtain_pair'),      # login
    path('api/logout/', LogOutAPIView.as_view(), name='token_refresh'),     # refresh token

]