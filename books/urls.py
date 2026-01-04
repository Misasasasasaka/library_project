from django.urls import path

from . import views


urlpatterns = [
    path("books", views.books_collection, name="books_collection"),
    path("books/<int:book_id>", views.book_item, name="book_item"),
    path("admin/books/export", views.admin_books_export, name="admin_books_export"),
    path("admin/books/import", views.admin_books_import, name="admin_books_import"),
]
