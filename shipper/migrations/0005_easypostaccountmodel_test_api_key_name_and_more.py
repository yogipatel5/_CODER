# Generated by Django 5.1.5 on 2025-02-20 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shipper", "0004_addressmodel"),
    ]

    operations = [
        migrations.AddField(
            model_name="easypostaccountmodel",
            name="test_api_key_name",
            field=models.CharField(
                blank=True, help_text="Name used to store/retrieve test API key from vault", max_length=255, unique=True
            ),
        ),
        migrations.AddField(
            model_name="easypostaccountmodel",
            name="test_vault_path",
            field=models.CharField(
                blank=True, help_text="Full path where the test API key is stored in vault", max_length=512
            ),
        ),
    ]
