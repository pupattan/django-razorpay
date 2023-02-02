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
    ALL = "ALL"
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    TYPE_CHOICES = (
        (INCOMING, "Incoming"),
        (OUTGOING, "Outgoing"),
    )
    PAYMENT_TYPE_LABEL = [{"label": "All", "value": ALL},
                          {"label": "Incoming", "value": INCOMING},
                          {"label": "Expense", "value": OUTGOING},
                          ]

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
    def get_amount_html(self):
        sign = "<span class='text-danger'>-" if self.payment_type == self.OUTGOING else "<span class='text-success'>+"
        return "{}{}</span>".format(sign, self.amount)

    @property
    def date(self):
        return self.created_at.date


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


class Organization(models.Model):
    """
    Organization details
    """
    membership_fee = models.DecimalField("membership_fee", default=200, decimal_places=2, max_digits=12, null=True)
    gateway_charges = models.DecimalField("gateway_charges", default=3, decimal_places=2, max_digits=12, null=True)

    updated_at = models.DateTimeField("Updated at", default=timezone.now)

    def __str__(self):
        return str(self.membership_fee) + " | " + str(self.updated_at) + " | " + str(self.gateway_charges)

    def save(self, *args, **kwargs):
        if not self.pk and Organization.objects.exists():
            raise ValidationError('There is can be only one Balance instance')
        return super(Organization, self).save(*args, **kwargs)

# # ----------------
# # Create initial object on load
# # ----------------
#
# if not Balance.objects.exists():
#     Balance.objects.create()
#
# if not Organization.objects.exists():
#     Organization.objects.create()