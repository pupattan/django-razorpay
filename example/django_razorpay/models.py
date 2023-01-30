from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# Create your models here.


class Member(models.Model):
    name = models.CharField("name", blank=True, max_length=50)
    phone = models.CharField("phone number", blank=True, max_length=20)
    email = models.EmailField("email address", blank=True)
    date_joined = models.DateTimeField("date joined", default=timezone.now)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    TYPE_CHOICES = (
        (INCOMING, "Incoming"),
        (OUTGOING, "Outgoing"),
    )

    payment_type = models.CharField(max_length=15,
                                    choices=TYPE_CHOICES,
                                    default=INCOMING)

    label = models.CharField("label", blank=True, max_length=50)
    amount = models.DecimalField("amount", blank=True, decimal_places=2, max_digits=12)
    data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField("date joined", default=timezone.now)

    def __str__(self):
        sign = "-" if self.payment_type == self.OUTGOING else "+"
        return "{}{}".format(sign, self.label)

    @property
    def get_label(self):
        return self.label

    @property
    def get_amount(self):
        sign = "-" if self.payment_type == self.OUTGOING else "+"
        return "{}{}".format(sign, self.amount)

    @property
    def date(self):
        print(self.data)
        return self.created_at


class Balance(models.Model):
    """
    Total current balance
    """
    amount = models.DecimalField("amount", default=0, decimal_places=2, max_digits=12)
    label = models.CharField("label", blank=True, max_length=50)
    updated_at = models.DateTimeField("Updated at", default=timezone.now)

    def __str__(self):
        return str(self.amount) + " | " + str(self.updated_at) + " | " + str(self.label)

    def save(self, *args, **kwargs):
        if not self.pk and Balance.objects.exists():
            raise ValidationError('There is can be only one Balance instance')
        return super(Balance, self).save(*args, **kwargs)

