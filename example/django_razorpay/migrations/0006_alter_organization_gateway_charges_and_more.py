# Generated by Django 4.1.5 on 2023-01-31 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_razorpay', '0005_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='gateway_charges',
            field=models.DecimalField(decimal_places=2, default=2, max_digits=12, null=True, verbose_name='gateway_charges'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='membership_fee',
            field=models.DecimalField(decimal_places=2, default=200, max_digits=12, null=True, verbose_name='membership_fee'),
        ),
    ]
