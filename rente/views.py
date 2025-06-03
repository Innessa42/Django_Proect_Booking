import datetime

from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils.timezone import now
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Listing, Booking, Review, ViewHistory, SearchHistory
from .permissions import IsLandlord
from .serializers import (
    UserSerializer, RegisterSerializer,
    ListingSerializer, BookingSerializer,
    ReviewSerializer, ViewHistorySerializer, SearchHistorySerializer
)

# Регистрация

class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogInAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                data={"message": "Имя пользователя и пароль обязательны"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            request=request,
            username=username,
            password=password
        )

        if user:
            response = Response(
                data={"message": f"Авторизация для пользователя: {user.username} выполнена"},
                status=status.HTTP_200_OK
            )

            refresh_token = RefreshToken.for_user(user)
            access_token = refresh_token.access_token

            access_expiry = datetime.datetime.fromtimestamp(access_token['exp'], datetime.timezone.utc)
            refresh_expiry = datetime.datetime.fromtimestamp(refresh_token['exp'], datetime.timezone.utc)

            response.set_cookie(
                key='access_token',
                value=str(access_token),
                httponly=True,
                secure=False,
                samesite='Lax',
                expires=access_expiry
            )

            response.set_cookie(
                key='refresh_token',
                value=str(refresh_token),
                httponly=True,
                secure=False,
                samesite='Lax',
                expires=refresh_expiry
            )
            return response

        else:
            return Response(
                data={"message": "Не верный логин или пароль"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogOutAPIView(APIView):
    def post(self, request: Request) -> Response:


        response = Response(
            data={"message": f"Выход выполнен"},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response


# Профили пользователей (для примера/админов)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


# Объявления
class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsLandlord()]

    def perform_create(self, serializer):

        serializer.save(owner=self.request.user)

    def get_queryset(self):
        queryset = Listing.objects.filter(is_active=True)

        # Поиск по ключевым словам
        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
            if self.request.user.is_authenticated:
                SearchHistory.objects.create(user=self.request.user, query=q)

        # Фильтрация
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        location = self.request.query_params.get("location")
        rooms = self.request.query_params.get("rooms")
        property_type = self.request.query_params.get("property_type")

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if rooms:
            queryset = queryset.filter(rooms=rooms)
        if property_type:
            queryset = queryset.filter(property_type=property_type)

        # Сортировка
        ordering = self.request.query_params.get("ordering")
        if ordering == "price_asc":
            queryset = queryset.order_by("price")
        elif ordering == "price_desc":
            queryset = queryset.order_by("-price")
        elif ordering == "date":
            queryset = queryset.order_by("-created_at")

        return queryset

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def view(self, request, pk=None):
        listing = self.get_object()
        listing.views_count += 1
        listing.save()
        ViewHistory.objects.create(user=request.user, listing=listing)
        return Response({"status": "view recorded"})


# Бронирования
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Booking.objects.filter(Q(listing__owner=user) | Q(tenant=user))


    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        if booking.listing.owner != request.user:
            return Response({"error": "Нет доступа"}, status=403)
        booking.status = Booking.Status.CONFIRMED
        booking.save()
        return Response({"status": "confirmed"})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.tenant != request.user and booking.listing.owner != request.user:
            return Response({"error": "Нет доступа"}, status=403)
        print(now().date() > booking.start_date - timedelta(days=2))
        if ( now().date()) > booking.start_date - timedelta(days=2):
            return Response({'detail': 'Отмена возможна не позднее, чем за 2 дня до заезда.'},
                            status=status.HTTP_403_FORBIDDEN)

        booking.status = Booking.Status.CANCELED
        booking.save()
        return  Response({'detail': 'Бронирование успешно отменено.'}, status=status.HTTP_200_OK)




# Отзывы
class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(listing_id=self.kwargs["listing_pk"])

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, listing_id=self.kwargs["listing_pk"])


# История просмотров
class ViewHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ViewHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ViewHistory.objects.filter(user=self.request.user)


# История поиска
class SearchHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SearchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user)