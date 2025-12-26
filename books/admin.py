from django.contrib import admin

from .models import Book, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "isbn",
        "category",
        "status",
        "available_copies",
        "total_copies",
        "location",
        "updated_at",
    )
    list_filter = ("status", "category")
    search_fields = ("title", "author", "isbn", "publisher")

    @admin.action(description="上架所选图书")
    def mark_on_shelf(self, request, queryset):
        queryset.update(status=Book.Status.ON_SHELF)

    @admin.action(description="下架所选图书")
    def mark_off_shelf(self, request, queryset):
        queryset.update(status=Book.Status.OFF_SHELF)

    actions = ("mark_on_shelf", "mark_off_shelf")
