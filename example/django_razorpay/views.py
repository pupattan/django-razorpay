import json
import datetime
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from django.contrib import messages
from django_razorpay.models import *
from django_razorpay.utils import RazorpayCustom, add_amount_from_total, deduct_amount_from_total
from django.utils.timezone import make_aware


def membership_fee(request):
    members = Member.objects.all().values_list('name', flat=True)
    if request.method == "POST":
        org = Organization.objects.last()
        if hasattr(settings, "RAZORPAY_ENABLE_CONVENIENCE_FEE") and settings.RAZORPAY_ENABLE_CONVENIENCE_FEE:
            amount = round(org.membership_fee + (org.membership_fee * (org.gateway_charges / 100)), 2)
        else:
            amount = round(org.membership_fee, 2)

        # payment_data["gateway"] = {"key": RazorpayCustom.KEY, "amount": amount}
        # payment_data["amount"] = amount
        # payment_data["description"] = "Membership fee"
        # payment_data["currency"] = RazorpayCustom.CURRENCY.upper()
        # payment_data["organization_name"] = settings.DJ_RAZORPAY.get('organization_name')
        # payment_data["organization_logo"] = settings.DJ_RAZORPAY.get('organization_logo')
        # payment_data["order_id"] = RazorpayCustom().create_order(amount=amount,
        #                                                          currency=payment_data["currency"],
        #                                                          type="membership_fee")
        phonenumber = request.POST.get("phonenumber")
        name = request.POST.get("name")
        email = request.POST.get("email")
        payment_data = RazorpayCustom().create_order(amount=amount, email=email, name=name, phonenumber=phonenumber)
        existing_member = Member.objects.filter(name=name).first()
        if existing_member:
            existing_member.email = email
            existing_member.phone = phonenumber
            existing_member.save()
        else:
            Member.objects.create(name=name, email=email)
        return render(request, "django_razorpay/fee_checkout.html", dict(payment_data=payment_data))
    else:
        return render(request, "django_razorpay/membership_fee.html", dict(members=members))


def payment_success(request):
    messages.success(request, "Payment successful....")
    return render(request, "django_razorpay/payment_status.html")


def payment_failed(request):
    messages.error(request, "Payment failed !!")
    return render(request, "django_razorpay/payment_status.html")


@csrf_exempt
def get_member_details(request):
    data = json.loads(request.body)
    member = Member.objects.filter(name=data['name']).first()
    member_detail = {"email": member.email, "phonenumber": member.phone}
    return JsonResponse(member_detail)


class PaymentVerify(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        rz = RazorpayCustom()
        if rz.verify_payment(self.request):
            razorpay_payment_id = self.request.GET.get('razorpay_payment_id')
            payment = rz.client.payment.fetch(razorpay_payment_id)
            amount = payment['amount'] / 100
            email = ""
            if payment.get('email'):
                email = payment.get('email')
            elif payment.get('customer_id'):
                customer = rz.client.customer.fetch(payment['customer_id'])
                email = customer["email"]
            member = Member.objects.filter(email=email).first()
            if member:
                label = member.name
            else:
                label = email
            add_amount_from_total(amount, razorpay_payment_id)
            Transaction.objects.create(amount=amount,
                                       data=payment,
                                       label=label,
                                       payment_type=Transaction.INCOMING)

            return reverse("django_razorpay:payment_success")
        else:
            return reverse("django_razorpay:payment_failed")


def transactions_list(request):
    transactions = Transaction.objects.all()
    return render(request, "django_razorpay/transactions_list.html", {"transactions": transactions})


def add_expense(request):
    if request.method == "POST":
        label = request.POST.get("label")
        amount = request.POST.get("amount")
        date_dt = datetime.datetime.strptime(request.POST.get("date"), '%d/%m/%Y')
        deduct_amount_from_total(amount, "expense")
        Transaction.objects.create(amount=amount,
                                   label=label,
                                   payment_type=Transaction.OUTGOING,
                                   created_at=make_aware(date_dt))
        messages.success(request, "Expense added....")
    return render(request, "django_razorpay/add_expense.html")