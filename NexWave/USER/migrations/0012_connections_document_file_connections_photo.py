# Generated by Django 4.1.9 on 2023-07-12 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('USER', '0011_user_active_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='connections',
            name='document_file',
            field=models.FileField(blank=True, null=True, upload_to='documents/'),
        ),
        migrations.AddField(
            model_name='connections',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='photos/'),
        ),
    ]
