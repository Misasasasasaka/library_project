from django.contrib import admin
from django.utils import timezone

from .models import Borrow


@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "book", "status", "borrow_date", "due_date", "return_date", "is_overdue")
    list_filter = ("status",)
    search_fields = ("user__username", "book__title", "book__isbn")
    date_hierarchy = "borrow_date"

    @admin.action(description="标记为已归还（自动回补库存）")
    def mark_returned(self, request, queryset):
        updated = 0
        for borrow in queryset:
            if borrow.status == Borrow.Status.RETURNED:
                continue
            borrow.status = Borrow.Status.RETURNED
            borrow.return_date = timezone.now()
            borrow.save()
            updated += 1
        self.message_user(request, f"已标记 {updated} 条记录为归还")

    actions = ("mark_returned",)
