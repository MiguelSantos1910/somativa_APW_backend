from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("filmes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="filme",
            name="sinopse",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
