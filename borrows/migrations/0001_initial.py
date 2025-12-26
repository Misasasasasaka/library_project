from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("books", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Borrow",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("borrow_date", models.DateTimeField(auto_now_add=True, verbose_name="借阅时间")),
                ("due_date", models.DateField(verbose_name="应还日期")),
                ("return_date", models.DateTimeField(blank=True, null=True, verbose_name="实际归还时间")),
                (
                    "status",
                    models.CharField(
                        choices=[("borrowed", "借阅中"), ("returned", "已归还"), ("overdue", "已逾期")],
                        default="borrowed",
                        max_length=10,
                        verbose_name="状态",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="borrows",
                        to="books.book",
                        verbose_name="图书",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="borrows",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "借阅记录",
                "verbose_name_plural": "借阅记录",
                "ordering": ["-borrow_date"],
            },
        ),
        migrations.AddConstraint(
            model_name="borrow",
            constraint=models.UniqueConstraint(
                condition=models.Q(("return_date__isnull", True)),
                fields=("user", "book"),
                name="borrow_unique_open_user_book",
            ),
        ),
        migrations.AddConstraint(
            model_name="borrow",
            constraint=models.CheckConstraint(
                check=models.Q(("status", "returned"), _negated=True)
                | models.Q(("return_date__isnull", False)),
                name="borrow_returned_requires_return_date",
            ),
        ),
    ]
