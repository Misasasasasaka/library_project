from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("borrows", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OverdueMailLog",
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
                ("mail", models.EmailField(blank=True, max_length=254, verbose_name="收件邮箱")),
                ("sent_date", models.DateField(verbose_name="发送日期")),
                ("sent_at", models.DateTimeField(auto_now_add=True, verbose_name="发送时间")),
                ("borrow_count", models.PositiveIntegerField(default=0, verbose_name="逾期条数")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="overdue_mail_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "逾期通知日志",
                "verbose_name_plural": "逾期通知日志",
                "ordering": ["-sent_date", "-sent_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="overduemaillog",
            constraint=models.UniqueConstraint(
                fields=("user", "sent_date"),
                name="overduemaillog_unique_user_sent_date",
            ),
        ),
    ]

