import json

import razorpay
from django.conf import settings
from django.urls import reverse
import decimal
from django_razorpay.models import Balance
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


class RazorpayCustom(object):
    KEY = settings.RAZORPAY_PAYMENT_VARIANTS.get("public_key")
    SECRET = settings.RAZORPAY_PAYMENT_VARIANTS.get("secret_key")
    CURRENCY = settings.RAZORPAY_PAYMENT_VARIANTS.get("currency")

    @property
    def client(self):
        if not hasattr(self, "__client"):
            self.__client = razorpay.Client(auth=(self.KEY, self.SECRET))
        return self.__client

    def verify_payment(self, request):
        params_dict = {
            'razorpay_order_id': request.GET.get('razorpay_order_id'),
            'razorpay_payment_id': request.GET.get('razorpay_payment_id'),
            'razorpay_signature': request.GET.get('razorpay_signature'),
        }
        try:
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            return False

    def create_order(self, **kwargs):
        order_amount = kwargs.pop("amount") * 100
        order_currency = kwargs.pop("currency").upper()
        notes = kwargs  # OPTIONAL
        return self.client.order.create(data=json.loads(json.dumps(dict(amount=order_amount,
                                                                        currency=order_currency,
                                                                        notes=notes),
                                                                   cls=DecimalEncoder))).get("id")


def add_amount_from_total(amount, razorpay_payment_id):
    if Balance.objects.exists():
        collection = Balance.objects.first()
        collection.amount += Decimal(amount)
        collection.razorpay_payment_id = razorpay_payment_id
        collection.save()
    else:
        Balance.objects.create(amount=amount, razorpay_payment_id=razorpay_payment_id)


def deduct_amount_from_total(amount):
    collection = Balance.objects.first()
    collection.amount -= amount
    collection.save()

