from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Theaters(models.Model):
    theater_id = models.CharField(max_length=256)
    tid = models.CharField(max_length=256)
    theater_name = models.CharField(max_length=256)
    latitude = models.CharField(max_length=256)
    longitude = models.CharField(max_length=256)



class Dates(models.Model):
    theater_id = models.CharField(max_length=256)
    display_dates = models.CharField(max_length=256)


class Movies(models.Model):
    theater_id = models.CharField(max_length=256)
    movie_name = models.CharField(max_length=256)
    duration = models.CharField(max_length=256)
    image_url = models.CharField(max_length=512)
    show_times = models.CharField(max_length=512)


class Seats(models.Model):
    theater_id = models.CharField(max_length=256)
    movie_name = models.CharField(max_length=256)
    show_times = models.CharField(max_length=512)
    seat_number_booked = models.IntegerField()

