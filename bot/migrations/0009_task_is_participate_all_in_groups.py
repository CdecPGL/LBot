# Generated by Django 2.0 on 2017-12-30 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0008_auto_20171230_0223'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='is_participate_all_in_groups',
            field=models.BooleanField(default=False),
        ),
    ]
