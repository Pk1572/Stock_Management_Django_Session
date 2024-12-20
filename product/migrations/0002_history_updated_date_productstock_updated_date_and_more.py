# Generated by Django 5.0.6 on 2024-09-02 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='history',
            name='updated_date',
            field=models.DateTimeField(auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productstock',
            name='updated_date',
            field=models.DateTimeField(auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='history',
            name='product_quantity',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_quantity',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='productstock',
            name='product_quantity',
            field=models.FloatField(default=0),
        ),
    ]
