from django.db import migrations, models
import django.db.models.deletion


def create_book_copies(apps, schema_editor) -> None:
    Book = apps.get_model("books", "Book")
    BookCopy = apps.get_model("books", "BookCopy")
    db_alias = schema_editor.connection.alias

    for book in Book.objects.using(db_alias).all().iterator():
        total = int(getattr(book, "total_copies", 0) or 0)
        if total <= 0:
            continue

        existing = set(
            BookCopy.objects.using(db_alias)
            .filter(book_id=book.id)
            .values_list("copy_no", flat=True)
        )
        to_create = [
            BookCopy(book_id=book.id, copy_no=no, is_active=True)
            for no in range(1, total + 1)
            if no not in existing
        ]
        if to_create:
            BookCopy.objects.using(db_alias).bulk_create(to_create)


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BookCopy",
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
                ("copy_no", models.PositiveIntegerField(verbose_name="副本编号")),
                ("is_active", models.BooleanField(default=True, verbose_name="在馆")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="copies",
                        to="books.book",
                        verbose_name="图书",
                    ),
                ),
            ],
            options={
                "verbose_name": "馆藏副本",
                "verbose_name_plural": "馆藏副本",
                "ordering": ["book_id", "copy_no"],
            },
        ),
        migrations.AddConstraint(
            model_name="bookcopy",
            constraint=models.UniqueConstraint(
                fields=("book", "copy_no"),
                name="bookcopy_unique_book_copy_no",
            ),
        ),
        migrations.AddIndex(
            model_name="bookcopy",
            index=models.Index(
                fields=["book", "is_active", "copy_no"],
                name="bookcopy_book_active_no_idx",
            ),
        ),
        migrations.RunPython(create_book_copies, reverse_code=migrations.RunPython.noop),
    ]

