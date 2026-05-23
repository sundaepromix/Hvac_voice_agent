import apps.core.crypto
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_alter_business_trade"),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="whatsapp_access_token",
            field=apps.core.crypto.EncryptedCharField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="business",
            name="whatsapp_phone_number_id",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="business",
            name="whatsapp_verify_token",
            field=apps.core.crypto.EncryptedCharField(blank=True, default=""),
        ),
    ]
