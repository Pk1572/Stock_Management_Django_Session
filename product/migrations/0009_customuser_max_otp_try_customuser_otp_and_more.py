# Generated by Django 5.0.6 on 2024-09-30 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_remove_units_unit_id_alter_product_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='max_otp_try',
            field=models.CharField(default=3, max_length=2),
        ),
        migrations.AddField(
            model_name='customuser',
            name='otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='otp_expiry',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='otp_max_out',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]