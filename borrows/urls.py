from django.urls import path

from . import views


urlpatterns = [
    path("borrows", views.borrows_collection, name="borrows_collection"),
    path("borrows/<int:borrow_id>/return", views.return_borrow, name="return_borrow"),
    path("borrows/<int:borrow_id>/renew", views.renew_borrow, name="renew_borrow"),
    path("admin/borrows/export", views.admin_borrows_export, name="admin_borrows_export"),
    path("admin/overdue/preview", views.admin_overdue_preview, name="admin_overdue_preview"),
    path("admin/overdue/send", views.admin_overdue_send, name="admin_overdue_send"),
]
