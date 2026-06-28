from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_logincode"),
    ]

    operations = [
        migrations.AlterField(
            model_name="business",
            name="currency",
            field=models.CharField(
                choices=[("USD", "US Dollar ($)")],
                default="USD",
                help_text="Prices are quoted in US dollars.",
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="business",
            name="voice_persona",
            field=models.CharField(
                default="Mary",
                help_text="Display name for the AI agent (configurable per business)",
                max_length=64,
            ),
        ),
    ]
