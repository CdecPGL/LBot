# Generated by Django 2.0 on 2017-12-29 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0006_auto_20171229_2354'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='authority',
            field=models.CharField(choices=[('Master', 'Master'), ('Editor', 'Editor'), ('Watcher', 'Watcher')], max_length=16),
        ),
    ]