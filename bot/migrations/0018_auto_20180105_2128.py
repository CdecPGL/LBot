# Generated by Django 2.0 on 2018-01-05 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0017_auto_20180103_1821'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='is_soon_check_finished',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='task',
            name='is_tomorrow_check_finished',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='task',
            name='is_tomorrow_remind_finished',
            field=models.BooleanField(default=False),
        ),
    ]