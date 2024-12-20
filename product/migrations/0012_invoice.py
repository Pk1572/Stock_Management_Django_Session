# Generated by Django 5.0.6 on 2024-10-09 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_product_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=255)),
                ('customer_name', models.CharField(max_length=255)),
                ('customer_address', models.TextField()),
                ('customer_contact', models.CharField(max_length=50)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
