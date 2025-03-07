from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name="index"),
    path('showdetails/<str:movie_title>/',views.showdetails,name="showdetails"),
    path('recommend_movies', views.recommend_movies, name='recommend_movies'),
    path('movies/', views.moviefunc, name="movies"),
    path('search_movies/', views.search_movies, name="search_movies"),
    path('topmovies/', views.topmovies, name="topmovies"),
    path('fetch_top_movies/', views.fetch_top_movies, name="fetch_top_movies"),
    path('contacts/', views.contacts, name='contacts'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('autocomplete_movies/', views.autocomplete_movies, name='autocomplete_movies'),

]