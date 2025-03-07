import os
from django.conf import settings
from django.shortcuts import render,redirect
from django.http import JsonResponse
import pickle
import pandas as pd
import requests
import json
from math import ceil
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import SearchHistory, SearchTerm
from django.contrib.auth.models import User
from .models import Comment
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

# Define paths to the pickle files
movie_dict_path = os.path.join(settings.BASE_DIR, 'data', 'movie_dict.pkl')
similarity_path = os.path.join(settings.BASE_DIR, 'data', 'similarity.pkl')
print(f"Movie Dict Path: {movie_dict_path}, Exists: {os.path.exists(movie_dict_path)}")
print(f"Similarity Path: {similarity_path}, Exists: {os.path.exists(similarity_path)}")

# Load preprocessed data
movies_dict = pickle.load(open(movie_dict_path, 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open(similarity_path, 'rb'))

# Helper function to fetch movie posters
def fetch_poster(movie_id):
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US'
        )
        data = response.json()

        # Check if 'poster_path' exists in the API response
        if 'poster_path' in data and data['poster_path']:
            return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
        else:
            return "https://via.placeholder.com/500x750?text=No+Image"
    except Exception as e:
        print(f"Error fetching poster: {e}")  # Log for debugging
        return "https://via.placeholder.com/500x750?text=No+Image"


# Recommendation logic
def recommend(movie):
    try:
        # Ensure the movie exists in the dataset
        if movie not in movies['title'].values:
            raise ValueError(f"Movie '{movie}' not found in the dataset.")
        
        
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[0:6]
        
        recommended_movies = []
        recommended_movies_posters = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            recommended_movies.append(movies.iloc[i[0]].title)
            recommended_movies_posters.append(fetch_poster(movie_id))
        return recommended_movies, recommended_movies_posters
    except Exception as e:
        print(f"Error in recommendation logic: {e}")  # Log for debugging
        return [], []  # Return empty lists in case of failure

# View to handle recommendations
def recommend_movies(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Parse the JSON body
            user_movie = data.get('movie')  # Extract the selected movie

            user = request.user
            SearchTerm.objects.create(user=user,term=user_movie)

            if not user_movie:
                return JsonResponse({"error": "Movie name not provided"}, status=400)

            recommended_movies, recommended_posters = recommend(user_movie)

            # Check if recommendations were successfully generated
            if not recommended_movies:
                return JsonResponse({"error": f"No recommendations found for '{user_movie}'."}, status=404)

            return JsonResponse({
                "movies": [{"title": movie, "poster": poster} for movie, poster in zip(recommended_movies, recommended_posters)]
            })
        except Exception as e:
            print(f"Error in `recommend_movies` view: {e}")  # Log the error for debugging
            return JsonResponse({"error": "An internal server error occurred."}, status=500)
    return JsonResponse({"error": "Invalid method"}, status=405)

# Existing views
def index(request):
    previous_searches = []
    if request.user.is_authenticated:
        previous_searches = SearchTerm.objects.filter(user=request.user)[:4]

    if request.method == 'POST':
        search_term = request.POST.get('movie_name')
        if search_term:
            if request.user.is_authenticated:
                SearchHistory.objects.create(user=request.user, search_term=search_term)
            # Recommendation logic remains unchanged
            recommended_movies, recommended_posters = recommend(search_term)
            return render(request, 'index.html', {
                'recommended_movies': recommended_movies,
                'recommended_posters': recommended_posters,
                'previous_searches': previous_searches,
            })

    return render(request, 'index.html', {
        'recommended_movies': [],
        'recommended_posters': [],
        'previous_searches': previous_searches,
    })

def showdetails(request, movie_title):
    # Fetch movie details based on the title
    try:
        movie = movies[movies['title'] == movie_title].iloc[0]
        movie_poster = fetch_poster(movie.movie_id)
        movie_details = get_movie_details(movie_title)
        
        # Handle comment submission
        if request.method == 'POST':
            if request.user.is_authenticated:
                comment_content = request.POST.get('comment')
                if comment_content:
                    Comment.objects.create(
                        movie_title=movie_title,
                        user=request.user,
                        content=comment_content
                    )
                    messages.success(request, "Your comment has been posted!")
                    return redirect('showdetails', movie_title=movie_title)
            else:
                messages.error(request, "You must log in to submit a comment.")
                return redirect('login')
        
        # Fetch all comments for this movie
        comments = Comment.objects.filter(movie_title=movie_title).order_by('-created_at')

        context = {
            'title': movie_title,
            'poster': movie_poster,
            'description': movie_details['overview'],
            'rating': movie_details['rating'],
            'comments': comments,
        }
        return render(request, 'showdetails.html', context)
    except Exception as e:
        print(f"Error fetching details for '{movie_title}': {e}")
        return render(request, 'showdetails.html', {'error': "Movie details not found."})


csv_path = os.path.join(settings.BASE_DIR, 'data', 'tmdb_5000_movies.csv')
movies_data = pd.read_csv(csv_path)

# Function to fetch movie details
def get_movie_details(movie_title):
    try:
        # Search for the movie in the dataset
        movie_row = movies_data[movies_data['title'] == movie_title].iloc[0]
        return {
            'overview': movie_row['overview'],
            'rating': movie_row['vote_average'],
            'id': movie_row['id'],
        }
    except IndexError:
        # Return defaults if the movie is not found
        return {
            'overview': 'Overview not available.',
            'rating': 'N/A',
            'id': None,
        }
    

def moviefunc(request):
    

    print(f"Type of 'movies': {type(movies)}")

    # Ensure 'movies' is a DataFrame
    if not isinstance(movies, pd.DataFrame):
        raise TypeError("Expected 'movies' to be a pandas DataFrame.")

    # Rename 'id' column to 'movie_id' for consistency
    if 'id' in movies.columns:
        movies.rename(columns={'id': 'movie_id'}, inplace=True)

    # Load initial movies (limit to 10 for performance)
    all_movies = movies['title'].tolist()[:10]
    all_posters = []
    print("All Movies:", all_movies)
    print("All Posters:", all_posters)

    for movie_id in movies['movie_id'][:10]:  # Fetch only the first 10 posters
        try:
            all_posters.append(fetch_poster(movie_id))
        except Exception as e:
            print(f"Error fetching poster for movie_id {movie_id}: {e}")
            all_posters.append("https://via.placeholder.com/500x750?text=Error")

    return render(request, 'movies.html', {
        'all_movies': all_movies,
        'all_posters': all_posters,
    })


# AJAX search endpoint
def search_movies(request):
    if request.method == 'GET':
        query = request.GET.get('query', '').strip().lower()

        # Filter movies matching the query
        filtered_movies = movies[movies['title'].str.lower().str.contains(query, na=False)]
        filtered_titles = filtered_movies['title'].tolist()
        filtered_posters = [fetch_poster(movie_id) for movie_id in filtered_movies['movie_id']]

        return JsonResponse({
            'movies': [{'title': title, 'poster': poster} for title, poster in zip(filtered_titles, filtered_posters)]
        })
    return JsonResponse({"error": "Invalid request"}, status=400)


#Top-movies

def topmovies(request):
    # Load data from tmdb_5000_movies.csv
    csv_path = os.path.join(settings.BASE_DIR, 'data', 'tmdb_5000_movies.csv')
    movies_data = pd.read_csv(csv_path)

    # Sort movies by vote_average and fetch top 20
    sorted_movies = movies_data.sort_values(by='vote_average', ascending=False).head(20)

    # Prepare movies for rendering
    movies = []
    for _, movie in sorted_movies.iterrows():
        movies.append({
            'title': movie['title'],
            'vote_average': movie['vote_average'],
            'poster_path': fetch_poster(movie['id']),  # Fetch the poster dynamically
        })

    return render(request, 'topmovies.html', {'movies': movies})



def fetch_top_movies(request):
    if request.method == 'GET':
        # Load data from tmdb_5000_movies.csv
        csv_path = os.path.join(settings.BASE_DIR, 'data', 'tmdb_5000_movies.csv')
        movies_data = pd.read_csv(csv_path)

        # Get the current page and calculate the offset
        page = int(request.GET.get('page', 1))
        page_size = 20
        start = (page - 1) * page_size
        end = start + page_size

        # Sort movies by vote_average and get the slice
        sorted_movies = movies_data.sort_values(by='vote_average', ascending=False).iloc[start:end]

        # Prepare movies for JSON response
        movies = []
        for _, movie in sorted_movies.iterrows():
            movies.append({
                'title': movie['title'],
                'vote_average': movie['vote_average'],
                'poster_path': fetch_poster(movie['id']),  # Fetch the poster dynamically
            })

        # Determine if more pages are available
        total_movies = len(movies_data)
        has_more = end < total_movies

        return JsonResponse({'movies': movies, 'has_more': has_more})
    return JsonResponse({"error": "Invalid request"}, status=400)


def contacts(request):
    return render(request, 'contacts.html')


#Login/logout functionality
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect('index')  # Redirect to home page after login
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('index')

#Signup view
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user
            username = form.cleaned_data.get('username')

            # Automatically log in the user after signup
            user = authenticate(username=username, password=request.POST.get('password1'))
            if user is not None:
                login(request, user)
                return redirect('index')  # Redirect to homepage

            return redirect('login')  # Redirect to login if authentication fails
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})

def delete_comment(request, comment_id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to delete a comment.")
        return redirect('login')

    # Fetch the comment
    comment = get_object_or_404(Comment, id=comment_id)

    # Ensure the logged-in user is the owner of the comment
    if comment.user != request.user:
        messages.error(request, "You are not authorized to delete this comment.")
        return redirect('showdetails', movie_title=comment.movie_title)

    # Delete the comment if POST request
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted successfully.")
        return redirect('showdetails', movie_title=comment.movie_title)

    # Show confirmation page
    return render(request, 'confirm_delete.html', {'comment': comment})


def autocomplete_movies(request):
    """Returns movie titles matching the user's input"""
    query = request.GET.get('query', '').strip().lower()
    
    if query:
        # Get movies that contain the input query (case insensitive)
        matching_movies = movies[movies['title'].str.lower().str.contains(query, na=False)]['title'].tolist()[:10]
    else:
        matching_movies = []

    return JsonResponse({'movies': matching_movies})