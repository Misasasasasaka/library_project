from django.urls import path

from . import views


urlpatterns = [
    path("borrows", views.borrows_collection, name="borrows_collection"),
    path("borrows/<int:borrow_id>/return", views.return_borrow, name="return_borrow"),
    path("borrows/<int:borrow_id>/renew", views.renew_borrow, name="renew_borrow"),
]

