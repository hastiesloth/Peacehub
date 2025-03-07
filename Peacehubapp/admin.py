from django.contrib import admin
from .models import Comment  # Import the Comment model
from .models import SearchTerm  # Import the SearchTerm model
# Register your models here.
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie_title', 'content', 'created_at')  # Fields to display in admin
    search_fields = ('user__username', 'movie_title', 'content')  # Search functionality
    list_filter = ('created_at',)  # Filter by creation date
    ordering = ('-created_at',)  # Order comments by most recent

@admin.register(SearchTerm)
class SearchTermAdmin(admin.ModelAdmin):
    list_display = ('user', 'term', 'searched_at')  # Fields to display
    search_fields = ('user__username', 'term')  # Search functionality
    list_filter = ('searched_at',)  # Filter by search date
    ordering = ('-searched_at',)