from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_term = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)



class Comment(models.Model):
    movie_title = models.CharField(max_length=255)  # Store the title of the movie
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user who commented
    content = models.TextField()  # The comment content
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for the comment

    def __str__(self):
        return f"{self.user.username} - {self.movie_title}"
    

class SearchTerm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Nullable for guests
    term = models.CharField(max_length=255)  # The search term
    searched_at = models.DateTimeField(auto_now_add=True)  # Timestamp of the search

    class Meta:
        ordering = ["-searched_at",]

    def __str__(self):
        return f"{self.user} searched '{self.term}'"
    

