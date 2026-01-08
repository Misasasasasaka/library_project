from django.db import migrations, models
import django.db.models.deletion


def assign_borrow_copies(apps, schema_editor) -> None:
    Borrow = apps.get_model("borrows", "Borrow")
    BookCopy = apps.get_model("books", "BookCopy")
    db_alias = schema_editor.connection.alias

    book_ids = list(
        Borrow.objects.using(db_alias)
        .order_by()
        .values_list("book_id", flat=True)
        .distinct()
    )

    for book_id in book_ids:
        copy_ids = list(
            BookCopy.objects.using(db_alias)
            .filter(book_id=book_id, is_active=True)
            .order_by("copy_no")
            .values_list("id", flat=True)
        )
        if not copy_ids:
            raise RuntimeError(f"book_id={book_id} 借阅记录存在但没有副本")

        open_ids = list(
            Borrow.objects.using(db_alias)
            .filter(book_id=book_id, return_date__isnull=True)
            .order_by("borrow_date", "id")
            .values_list("id", flat=True)
        )
        if len(open_ids) > len(copy_ids):
            raise RuntimeError(
                f"book_id={book_id} 未归还借阅数量({len(open_ids)})超过副本数量({len(copy_ids)})"
            )

        for idx, borrow_id in enumerate(open_ids):
            Borrow.objects.using(db_alias).filter(pk=borrow_id).update(copy_id=copy_ids[idx])

        returned_ids = list(
            Borrow.objects.using(db_alias)
            .filter(book_id=book_id, return_date__isnull=False)
            .order_by("borrow_date", "id")
            .values_list("id", flat=True)
        )
        for idx, borrow_id in enumerate(returned_ids):
            Borrow.objects.using(db_alias).filter(pk=borrow_id).update(
                copy_id=copy_ids[idx % len(copy_ids)]
            )


class Migration(migrations.Migration):
    dependencies = [
        ("books", "0002_bookcopy"),
        ("borrows", "0002_overduemaillog"),
    ]

    operations = [
        migrations.AddField(
            model_name="borrow",
            name="copy",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="borrows",
                to="books.bookcopy",
                verbose_name="副本",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="borrow",
            name="borrow_unique_open_user_book",
        ),
        migrations.RunPython(assign_borrow_copies, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="borrow",
            name="copy",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="borrows",
                to="books.bookcopy",
                verbose_name="副本",
            ),
        ),
        migrations.AddConstraint(
            model_name="borrow",
            constraint=models.UniqueConstraint(
                condition=models.Q(("return_date__isnull", True)),
                fields=("copy",),
                name="borrow_unique_open_copy",
            ),
        ),
    ]

