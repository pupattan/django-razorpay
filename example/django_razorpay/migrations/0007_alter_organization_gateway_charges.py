# Generated by Django 4.1.5 on 2023-01-31 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_razorpay', '0006_alter_organization_gateway_charges_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='gateway_charges',
            field=models.DecimalField(decimal_places=2, default=3, max_digits=12, null=True, verbose_name='gateway_charges'),
        ),
    ]