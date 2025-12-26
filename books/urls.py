from django.urls import path

from . import views


urlpatterns = [
    path("books", views.books_collection, name="books_collection"),
    path("books/<int:book_id>", views.book_item, name="book_item"),
]

