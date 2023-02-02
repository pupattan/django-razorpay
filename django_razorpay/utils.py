import json
import logging
from decimal import Decimal
import razorpay
from django.conf import settings

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

    @staticmethod
    def is_fee_applicable():
        return hasattr(settings, "DJ_RAZORPAY") and settings.DJ_RAZORPAY.get("RAZORPAY_ENABLE_CONVENIENCE_FEE")

    def caculate_amount(self):
        org = Organization.objects.first()
        amount = round(org.membership_fee + (org.membership_fee * (org.gateway_charges / 100)), 2)


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

