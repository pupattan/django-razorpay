# Generated by Django 4.1.5 on 2023-01-30 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_razorpay', '0003_remove_balance_razorpay_payment_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='data',
            field=models.JSONField(blank=True, null=True),
        ),
    ]