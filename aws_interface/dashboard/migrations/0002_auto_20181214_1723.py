# Generated by Django 2.1.4 on 2018-12-14 17:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='password_s_hash',
            new_name='password_hash',
        ),
    ]