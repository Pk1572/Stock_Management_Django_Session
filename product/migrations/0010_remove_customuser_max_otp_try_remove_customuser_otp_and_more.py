# Generated by Django 5.0.6 on 2024-09-30 07:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0009_customuser_max_otp_try_customuser_otp_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='max_otp_try',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='otp',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='otp_expiry',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='otp_max_out',
        ),
    ]
