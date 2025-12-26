from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("name", models.CharField(max_length=100, unique=True, verbose_name="分类名称")),
                ("description", models.TextField(blank=True, verbose_name="简介")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "分类",
                "verbose_name_plural": "分类",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Book",
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
                ("title", models.CharField(db_index=True, max_length=200, verbose_name="书名")),
                ("author", models.CharField(db_index=True, max_length=100, verbose_name="作者")),
                ("isbn", models.CharField(db_index=True, max_length=32, unique=True, verbose_name="ISBN")),
                ("publisher", models.CharField(blank=True, max_length=200, verbose_name="出版社")),
                ("publish_date", models.DateField(blank=True, null=True, verbose_name="出版日期")),
                ("description", models.TextField(blank=True, verbose_name="简介")),
                ("cover", models.FileField(blank=True, null=True, upload_to="covers/", verbose_name="封面")),
                ("total_copies", models.PositiveIntegerField(default=1, verbose_name="总数量")),
                ("available_copies", models.PositiveIntegerField(default=1, verbose_name="可借数量")),
                ("location", models.CharField(blank=True, max_length=100, verbose_name="书架位置")),
                (
                    "status",
                    models.CharField(
                        choices=[("on_shelf", "上架"), ("off_shelf", "下架")],
                        default="on_shelf",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="books",
                        to="books.category",
                        verbose_name="分类",
                    ),
                ),
            ],
            options={
                "verbose_name": "图书",
                "verbose_name_plural": "图书",
            },
        ),
        migrations.AddConstraint(
            model_name="book",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("available_copies__lte", models.F("total_copies")),
                ),
                name="book_available_lte_total",
            ),
        ),
    ]

