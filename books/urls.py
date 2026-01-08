from django.urls import path

from . import views


urlpatterns = [
    path("categories", views.categories_collection, name="categories_collection"),
    path("categories/<int:category_id>", views.category_item, name="category_item"),
    path("books", views.books_collection, name="books_collection"),
    path("books/<int:book_id>", views.book_item, name="book_item"),
    path("books/<int:book_id>/available-copies", views.book_available_copies, name="book_available_copies"),
    path("books/<int:book_id>/cover", views.book_cover, name="book_cover"),
    path("admin/books/export", views.admin_books_export, name="admin_books_export"),
    path("admin/books/import", views.admin_books_import, name="admin_books_import"),
]
