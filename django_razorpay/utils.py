import json
import logging
import time
from decimal import Decimal
import razorpay
from django.conf import settings
from django.urls import reverse

from django_razorpay.models import Balance, Organization


logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


class RazorpayCustom(object):
    KEY = settings.DJ_RAZORPAY.get("RAZORPAY_VARIANTS").get("public_key")
    SECRET = settings.DJ_RAZORPAY.get("RAZORPAY_VARIANTS").get("secret_key")
    CURRENCY = settings.DJ_RAZORPAY.get("RAZORPAY_VARIANTS").get("currency")

    @property
    def client(self):
        if not hasattr(self, "__client"):
            self.__client = razorpay.Client(auth=(self.KEY, self.SECRET))
        return self.__client

    def verify_payment(self, request):
        try:
            if self.use_payment_link():
                self.client.utility.verify_payment_link_signature({
                    'payment_link_id': request.GET.get('razorpay_payment_link_id'),
                    'payment_link_reference_id': request.GET.get('razorpay_payment_link_reference_id'),
                    'payment_link_status': request.GET.get('razorpay_payment_link_status'),
                    'razorpay_payment_id': request.GET.get('razorpay_payment_id'),
                    'razorpay_signature': request.GET.get('razorpay_signature')
                })
            else:
                self.client.utility.verify_payment_signature({
                    'razorpay_order_id': request.GET.get('razorpay_order_id'),
                    'razorpay_payment_id': request.GET.get('razorpay_payment_id'),
                    'razorpay_signature': request.GET.get('razorpay_signature'),
                })

            return True
        except Exception as e:
            return False

    def __create_order(self, **kwargs):
        order_amount = kwargs.pop("amount") * 100
        order_currency = kwargs.pop("currency").upper()
        notes = kwargs  # OPTIONAL
        return self.client.order.create(data=json.loads(json.dumps(dict(amount=order_amount,
                                                                        currency=order_currency,
                                                                        notes=notes),
                                                                   cls=DecimalEncoder))).get("id")

    def create_order(self, amount, name="", email="", phonenumber=""):
        payment_data = dict(name=name, email=email, phonenumber=phonenumber)
        payment_data["gateway"] = {"key": self.KEY, "amount": amount}
        payment_data["amount"] = amount
        payment_data["description"] = "Membership fee"
        payment_data["currency"] = self.CURRENCY.upper()
        payment_data["organization_name"] = settings.DJ_RAZORPAY.get('organization_name')
        payment_data["organization_logo"] = settings.DJ_RAZORPAY.get('organization_logo')
        payment_data["order_id"] = self.__create_order(amount=amount,
                                                       currency=payment_data["currency"],
                                                       type="membership_fee")
        return payment_data

    def create_payment_link(self, amount, name="", email="", phonenumber="", reference_id="", label=""):
        razorpay_data = {
            "amount": amount * 100,
            "currency": self.CURRENCY.upper(),
            "description": settings.DJ_RAZORPAY["organization_name"],

            "notify": {
                "sms": True,
                "email": True
            },
            "reminder_enable": True,
            "notes": {
                "label": label if label else name
            },
            "callback_url": settings.DJ_RAZORPAY["organization_domain"] + reverse("django_razorpay:payment_verify"),
            "callback_method": "get"
        }
        if reference_id:
            razorpay_data["reference_id"] = reference_id + str(time.time()).replace(".", "")

        if name:
            razorpay_data.update({"customer": {
                "name": name
            }})
        if phonenumber and email:
            razorpay_data["customer"]["email"] = email
            razorpay_data["customer"]["contact"] = "+91" + phonenumber
        return self.client.payment_link.create(json.loads(json.dumps(razorpay_data, cls=DecimalEncoder)))["short_url"]

    @staticmethod
    def is_fee_applicable():
        return hasattr(settings, "DJ_RAZORPAY") and settings.DJ_RAZORPAY.get("RAZORPAY_ENABLE_CONVENIENCE_FEE")

    @staticmethod
    def use_payment_link():
        return hasattr(settings, "DJ_RAZORPAY") and settings.DJ_RAZORPAY.get("USE_PAYMENT_LINK")

    @staticmethod
    def get_percentage(whole, part):
        return Decimal(whole) / 100 * Decimal(part)

    @staticmethod
    def get_amount_with_charges(amount):
        org = Organization.objects.first()
        return round(amount + RazorpayCustom.get_percentage(amount, org.gateway_charges), 2)

    @staticmethod
    def get_amount_deducting_charges(amount):
        org = Organization.objects.first()
        return round((amount * 100) / (100 + org.gateway_charges))


def add_amount_to_total(amount, label):
    logger.info("Adding payment {}, label: {}".format(Decimal(amount), label))
    if Balance.objects.exists():
        collection = Balance.objects.first()
        collection.amount += Decimal(amount)
        collection.label = label
        collection.save()
    else:
        Balance.objects.create(amount=amount, label=label)


def deduct_amount_from_total(amount, label):
    logger.info("Deducting payment {}, label: {}".format(Decimal(amount), label))
    collection = Balance.objects.first()
    collection.amount -= Decimal(amount)
    collection.label = label
    collection.save()

