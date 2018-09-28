from django.contrib import admin
from .models import Book, Chapter, BookOriginalSource

# Register your models here.
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'desc', 'poster', 'tag', 'status', 'latest', 'updated')

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('book', 'section', 'title', 'content')

@admin.register(BookOriginalSource)
class BookOriginalSourceAdmin(admin.ModelAdmin):
    list_display = ('book_name', 'author', 'url', 'all', 'activate')
