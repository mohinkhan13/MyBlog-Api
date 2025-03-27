# Generated by Django 5.1.6 on 2025-02-28 12:19

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='poststats',
            name='liked_by',
            field=models.ManyToManyField(blank=True, default=None, related_name='liked_posts', to=settings.AUTH_USER_MODEL),
        ),
    ]
