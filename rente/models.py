from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


# Расширенный пользователь
class User(AbstractUser):
    class Role(models.TextChoices):
        TENANT = 'tenant', _('Арендатор')
        LANDLORD = 'landlord', _('Арендодатель')
        ADMIN = 'admin', _('Администратор')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)



def is_admin(self):
    return self.role == self.Role.ADMIN


def is_tenant(self):
    return self.role == self.Role.TENANT


def is_landlord(self):
    return self.role == self.Role.LANDLORD

def save(self, *args, **kwargs):
    if self.role == self.Role.ADMIN:
        self.is_staff = True
        self.is_superuser = True
    super().save(*args, **kwargs)


# Объявления
class Listing(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = 'apartment', _('Квартира')
        HOUSE = 'house', _('Дом')
        STUDIO = 'studio', _('Студия')
        PENTHOUSE = 'penthouse', _('Пентхаус')
        DUPLEX = 'duplex', _('Дуплекс')
        LOFT = 'loft', _('Лофт')
        ROOM = 'room', _('Комната')
        MAISONETTE = 'maisonette', _('Мезонет')
        BUNGALOW = 'bungalow', _('Бунгало')
        TOWNHOUSE = 'townhouse', _('Таунхаус')
        FARMHOUSE = 'farmhouse', _('Фермерский дом')
        OTHER = 'other', _('Другое')

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rooms = models.PositiveIntegerField()
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


# Бронирования
class Booking(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()

    class Status(models.TextChoices):
        PENDING = 'pending', _('Ожидание')
        CONFIRMED = 'confirmed', _('Подтверждено')
        CANCELED = 'canceled', _('Отменено')

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# История просмотров
class ViewHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)


# История поиска
class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)