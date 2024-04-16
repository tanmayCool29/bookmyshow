from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("logout", views.logout_view, name="logout"),
    path("login", views.login_view, name="login"),
    path("register", views.register, name="register"),
    path('movie_theaters/', views.movie_theaters, name='movie_theaters'),
    path('movie_showtimes/', views.movie_showtimes, name='movie_showtimes'),
    path('select_show/', views.select_show, name='select_show'),
    path('book_seats/', views.book_seats, name='book_seats'),
]