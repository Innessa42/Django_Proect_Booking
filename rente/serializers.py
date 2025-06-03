from rest_framework import serializers
from .models import User, Listing, Booking, Review, ViewHistory, SearchHistory
from django.contrib.auth.password_validation import validate_password


# 🔐 Сериализатор для регистрации пользователя
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password2", "role")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


# 👤 Сериализатор для профиля пользователя (вывод информации)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role")


# 🏘️ Объявления
class ListingSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = "__all__"

    def validate(self, attrs):
        title = attrs["title"]
        location = attrs["location"]

        listing = Listing.objects.filter(title=title, location=location)
        if listing.exists():
            raise  serializers.ValidationError("Tacoi obiect uje sushestvuet")
        return attrs

    def get_reviews_count(self, obj):
        return obj.reviews.count()

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum([r.rating for r in reviews]) / reviews.count(), 1)
        return None


# 📆 Бронирование
class BookingSerializer(serializers.ModelSerializer):
    tenant = UserSerializer(read_only=True)
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())

    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ("status", "created_at")


# ⭐ Отзывы
class ReviewSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ("created_at","listing")


# 👁️ История просмотров
class ViewHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewHistory
        fields = "__all__"


# 🔍 История поиска
class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = "__all__"