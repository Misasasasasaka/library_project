from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("borrows", "0003_borrow_copy"),
    ]

    operations = [
        migrations.AlterField(
            model_name="borrow",
            name="copy",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="borrows",
                to="books.bookcopy",
                verbose_name="副本",
            ),
        ),
    ]

