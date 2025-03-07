// Assuming `movieGrid` is the element that contains the grid of movie recommendations
const movieGrid = document.querySelector('.movie-grid');

// Function to display the movie grid after recommendations are added
function showMovieGrid() {
    movieGrid.style.display = 'grid'; // Changes the display from 'none' to 'grid'
}

// Example: Fetch movie recommendations
fetch('/recommend_movies', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken, // Add CSRF token here
    },
    body: JSON.stringify({ movie: userSelectedMovie }) // Replace with selected movie
})
.then(response => {
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
})
.then(data => {
    if (data.error) {
        alert(`Error: ${data.error}`);
    } else {
        populateMovieGrid(data.movies);
        showMovieGrid();
    }
})
.catch(error => {
    console.error("Fetch error:", error);
    alert("Error occurred while fetching recommendations");
});



// Function to populate the movie grid dynamically
function populateMovieGrid(movies) {
    movies.forEach(movie => {
        const movieItem = document.createElement('div');
        movieItem.classList.add('movie-item');
        movieItem.innerText = movie.title; // Replace with desired data
        movieGrid.appendChild(movieItem);
    });
}
