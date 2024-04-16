from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import requests
from django.db import IntegrityError
from django.urls import reverse
from .models import *
from django.contrib.auth.hashers import make_password
import speech_recognition as sr
from datetime import datetime
from openai import OpenAI
import numpy as np
import json
from modernrpc.views import RPCEntryPoint
import http.client
from threading import Thread


def fetch_theaters_api():
    conn = http.client.HTTPSConnection("flixster.p.rapidapi.com")

    headers = {
        'X-RapidAPI-Key': "023ef40098msh7e20ffef9e148a6p1f0e47jsn89b0a771d7f7",
        'X-RapidAPI-Host': "flixster.p.rapidapi.com"
    }

    conn.request("GET", "/theaters/list?zipCode=90002&radius=50",
                 headers=headers)

    res = conn.getresponse()
    data = res.read()

    movies_data = data.decode("utf-8")

    # Now you can parse movies_data directly as JSON
    my_data = json.loads(movies_data)

    # Accessing the dictionary elements
    theaters = my_data["data"]["theaters"]

    for theater in theaters:
        Theaters.objects.create(
            theater_id=theater['id'],
            tid=theater['tid'],
            theater_name=theater['name'],
            latitude=theater['latitude'],
            longitude=theater['longitude'],
        )


def fetch_movies_api():
    theaters = Theaters.objects.all()

    for theater in theaters:

        theater_id = ""
        theater_id += f"{theater.theater_id}"

        conn = http.client.HTTPSConnection("flixster.p.rapidapi.com")

        headers = {
            'X-RapidAPI-Key': "023ef40098msh7e20ffef9e148a6p1f0e47jsn89b0a771d7f7",
            'X-RapidAPI-Host': "flixster.p.rapidapi.com"
        }

        # theater_id_ = theater['theater_id']

        conn.request("GET", f"/theaters/detail?id={theater_id}", headers=headers)

        res = conn.getresponse()
        data = res.read()

        movies_data = data.decode("utf-8")

        my_data = json.loads(movies_data)

        movies_data_details = my_data["data"]["theaterShowtimeGroupings"]
        displayDates = movies_data_details["displayDates"]
        startDate = movies_data_details["displayDate"]
        moviesInThisTheater = movies_data_details["movies"]

        for mov in moviesInThisTheater:
            showtimes = mov.get('movieVariants', []) and mov['movieVariants'][0].get('amenityGroups', []) and \
                        mov['movieVariants'][0]['amenityGroups'][0].get('showtimes', [])

            if not showtimes:
                continue

            for showtime in showtimes:
                provider_time = showtime.get('providerTime')

                name = mov.get('name')
                poster_image = mov.get('posterImage')
                poster_image_url = poster_image and poster_image.get('url')
                duration_minutes = mov.get('durationMinutes')

                if not (provider_time and name and poster_image_url and duration_minutes):
                    continue

                print(provider_time)
                print(name)
                print(theater_id)
                print(poster_image_url)
                print(duration_minutes)
                print("\n----------------------\n")

                Movies.objects.create(
                    theater_id=theater_id,
                    movie_name=name,
                    duration=str(duration_minutes),
                    image_url=poster_image_url,
                    show_times=provider_time
                )


def index(request):
    # theaters = Theaters.objects.all()

    movies = Movies.objects.all()
    unique_movies_name = []
    movies_data = []
    for mov in movies:
        if mov.movie_name not in unique_movies_name:
            unique_movies_name.append(mov.movie_name)
            movies_data.append([mov.movie_name, mov.duration, mov.image_url])

    return render(request, 'index.html', {
        "movies_data": movies_data
    })

def fetch_theater_data(theater, movies_with_name, theater_data):
    theater_show_times = [
        movie.show_times for movie in movies_with_name if movie.theater_id == theater.theater_id
    ]
    theater_data.append({
        'theater_id': theater.theater_id,
        'theater_name': theater.theater_name,
        'tid': theater.tid,
        'show_times': theater_show_times,
    })
def movie_theaters(request):
    if request.method == 'POST':
        movie_name = request.POST.get('movie_name')
        movies_with_name = Movies.objects.filter(movie_name=movie_name)
        theater_ids = set(movie.theater_id for movie in movies_with_name)
        theaters_with_movie = Theaters.objects.filter(theater_id__in=theater_ids)

        theater_data = []
        threads = []

        for theater in theaters_with_movie:
            # Create and start a new Thread for each theater data fetching
            thread = Thread(target=fetch_theater_data, args=(theater, movies_with_name, theater_data))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        print(theater_data)  # For debugging purposes

        return render(request, 'theaters.html', {'theater_data': theater_data, 'movie_name': movie_name})
    else:
        movies = Movies.objects.all()
        unique_movies_name = []
        movies_data = []

        for mov in movies:
            if mov.movie_name not in unique_movies_name:
                unique_movies_name.append(mov.movie_name)
                movies_data.append([mov.movie_name, mov.duration, mov.image_url])

        return render(request, 'index.html', {"movies_data": movies_data})


# def movie_theaters(request):
#     if request.method == 'POST':
#         movie_name = request.POST.get('movie_name')
#
#         # Filter Movies model to get all records with the given movie_name
#         movies_with_name = Movies.objects.filter(movie_name=movie_name)
#
#         # Extract unique theater_id values from the filtered Movies records
#         theater_ids = set(movie.theater_id for movie in movies_with_name)
#
#         # Filter Theaters model using the extracted theater_id values
#         theaters_with_movie = Theaters.objects.filter(theater_id__in=theater_ids)
#
#         # Create a data structure that contains the required information
#         theater_data = []
#         for theater in theaters_with_movie:
#             theater_show_times = [movie.show_times for movie in movies_with_name if movie.theater_id == theater.theater_id]
#             theater_data.append({
#                 'theater_id': theater.theater_id,
#                 'theater_name': theater.theater_name,
#                 'tid': theater.tid,
#                 'show_times': theater_show_times,
#             })
#         print(theater_data)
#         # Render the template with the theater_data
#         return render(request, 'theaters.html', {'theater_data': theater_data, 'movie_name':movie_name})
#     else:
#         movies = Movies.objects.all()
#         unique_movies_name = []
#         movies_data = []
#         for mov in movies:
#             if mov.movie_name not in unique_movies_name:
#                 unique_movies_name.append(mov.movie_name)
#                 movies_data.append([mov.movie_name, mov.duration, mov.image_url])
#         return render(request, 'index.html', {
#             "movies_data": movies_data
#         })


def movie_showtimes(request):
    if request.method == 'POST':

        movie_name = request.POST.get('movie_name')
        theater_name = request.POST.get('theater_name')

        # print(movie_name)
        # print(theater_name)
        # print("\n---------------\n")
        # Filter Movies model to get all records with the given movie_name
        movies_with_name = Movies.objects.filter(movie_name=movie_name)

        # Extract unique theater_id values from the filtered Movies records
        theater_ids = set(movie.theater_id for movie in movies_with_name)

        # Filter Theaters model using the extracted theater_id values
        theaters_with_movie = Theaters.objects.filter(theater_id__in=theater_ids)

        # Create a data structure that contains the required information
        theater_data = []
        for theater in theaters_with_movie:
            theater_show_times = [movie.show_times for movie in movies_with_name if
                                  movie.theater_id == theater.theater_id]
            # print(f"1: {theater_name}, 2: {theater.theater_name}\n")
            if theater_name == theater.theater_name:
                theater_data.append({
                    'theater_id': theater.theater_id,
                    'theater_name': theater.theater_name,
                    'tid': theater.tid,
                    'show_times': theater_show_times,
                    'movie_name': movie_name
                })
        # print(theater_data)

        # Render the template with the theater_data
        return render(request, 'showtimes.html', {'theater_data': theater_data})
    else:
        # Handle the case when the request method is not POST, like displaying an error message
        movies = Movies.objects.all()
        unique_movies_name = []
        movies_data = []
        for mov in movies:
            if mov.movie_name not in unique_movies_name:
                unique_movies_name.append(mov.movie_name)
                movies_data.append([mov.movie_name, mov.duration, mov.image_url])
        return render(request, 'index.html', {
            "movies_data": movies_data
        })


def select_show(request):
    if request.method == 'POST':
        theater_id = request.POST.get('theater_id')
        theater_name = request.POST.get('theater_name')
        tid = request.POST.get('tid')
        movie_name = request.POST.get('movie_name')
        show_time = request.POST.get('show_time')

        print(f"theater_id:{theater_id}\ntheater_name:{theater_name}\ntid:{tid}\n:movie_name:{movie_name}\nshow_time:{show_time}\n")

        # Render a new template or redirect to another view as needed
        return render(request, 'selected_show.html', {
            'theater_id': theater_id,
            'theater_name': theater_name,
            'tid': tid,
            'movie_name': movie_name,
            'show_time': show_time,
            'range': range(11),  # Add this line
        })
    else:
        # Handle the case when the request method is not POST, like displaying an error message
        pass

def book_seats(request):
    if request.method == 'POST':
        selected_seats = request.POST.getlist('selected_seats')
        theater_name = request.POST.get('theater_name')
        movie_name = request.POST.get('movie_name')
        show_time = request.POST.get('show_time')  # You may need to pass the show time from the template as well

        # Check if the seat numbers are valid integers
        invalid_seats = [seat for seat in selected_seats if not seat.isdigit()]
        if invalid_seats:
            return HttpResponse(f'Invalid seat numbers: {", ".join(invalid_seats)}.', status=400)

        # Convert the seat numbers to integers
        selected_seats = [int(seat) for seat in selected_seats]

        # Find or create a Seats instance for the given theater, movie, and show time
        seats_instance, created = Seats.objects.get_or_create(
            theater_id=theater_name,
            movie_name=movie_name,
            show_times=show_time,
        )

        # Update the seat_number_booked field with the newly selected seats
        current_booked_seats = seats_instance.seat_number_booked
        new_booked_seats = list(set(current_booked_seats.split(',')) | set(selected_seats))
        seats_instance.seat_number_booked = ','.join(map(str, sorted(new_booked_seats)))
        seats_instance.save()

        return HttpResponse('Selected seats submitted successfully.')
    else:
        return HttpResponse('Invalid request.', status=400)



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmPassword"]

        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "register.html")
