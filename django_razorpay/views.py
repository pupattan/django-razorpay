import json
import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from django.contrib import messages
from django_razorpay.models import *
from django_razorpay.utils import RazorpayCustom, add_amount_to_total, deduct_amount_from_total
from django.utils.timezone import make_aware
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required


def membership_fee(request):
    members = Member.objects.all().values_list('name', flat=True)
    if request.method == "POST":
        org = Organization.objects.last()
        if RazorpayCustom.is_fee_applicable():
            amount = org.get_amount_fee_with_charges(org.membership_fee)
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
        return render(request, "django_razorpay/checkout.html", dict(payment_data=payment_data))
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
            label = self.request.GET.get('label')
            payment = rz.client.payment.fetch(razorpay_payment_id)
            amount = payment['amount'] / 100
            email = ""
            if payment.get('email'):
                email = payment.get('email')
            elif payment.get('customer_id'):
                customer = rz.client.customer.fetch(payment['customer_id'])
                email = customer["email"]
            member = Member.objects.filter(email=email).first()
            if label:
                pass
            elif member:
                label = member.name
            else:
                label = email
            add_amount_to_total(amount, razorpay_payment_id)
            Transaction.objects.create(amount=amount,
                                       data=payment,
                                       label=label,
                                       payment_type=Transaction.INCOMING)

            return reverse("django_razorpay:payment_success")
        else:
            return reverse("django_razorpay:payment_failed")


def transactions(request):
    total_balance = Balance.objects.last().amount
    month_selected = request.GET.get("month")
    payment_type_selected = request.GET.get("payment-type")
    last_few_months = []
    now = timezone.now()
    month_value_format = "%b-%Y"

    if month_selected:
        current_month = month_selected
    else:
        current_month = now.strftime(month_value_format)

    current_month_dt = datetime.datetime.strptime(current_month, month_value_format)
    for i in range(10):
        __month = now - relativedelta(months=i)
        last_few_months.append({"label": __month.strftime("%b %Y"), "value": __month.strftime(month_value_format)})

    transactions_qs = Transaction.objects.filter(created_at__month=current_month_dt.month,
                                                 created_at__year=current_month_dt.year,
                                                 )
    if not payment_type_selected or payment_type_selected == Transaction.ALL:
        current_payment_type = Transaction.ALL
        transactions = transactions_qs.all()
    else:
        current_payment_type = payment_type_selected
        transactions = transactions_qs.filter(payment_type=payment_type_selected,
                                                  ).all()

    return render(request, "django_razorpay/transactions.html", {"transactions": transactions,
                                                                      "total_balance": total_balance,
                                                                      "last_few_months": last_few_months,
                                                                      "current_month": current_month,
                                                                      "payment_types": Transaction.PAYMENT_TYPE_LABEL,
                                                                      "current_payment_type": current_payment_type
                                                                      })


@login_required
@staff_member_required
def manual_transaction(request):
    if request.method == "POST":
        payment_type = request.POST.get("payment_type")
        label = request.POST.get("label")
        amount = request.POST.get("amount")
        date_dt = datetime.datetime.strptime(request.POST.get("date"), '%d/%m/%Y')
        if payment_type == Transaction.INCOMING:
            add_amount_to_total(amount, "manual-transaction")
        elif payment_type == Transaction.OUTGOING:
            deduct_amount_from_total(amount, "manual-transaction")
        else:
            raise ValidationError("Please provide payment type")
        Transaction.objects.create(amount=amount,
                                   label=label,
                                   payment_type=payment_type,
                                   created_at=make_aware(date_dt))

        messages.success(request, "Transaction added....")
    return render(request, "django_razorpay/manual_transaction.html",
                  {"payment_types": Transaction.PAYMENT_TYPE_LABEL[1:]})


def addhoc_payment(request):
    if request.method == "POST":
        org = Organization.objects.last()
        if RazorpayCustom.is_fee_applicable():
            amount = org.get_amount_fee_with_charges(Decimal(request.POST.get("amount")))
        else:
            amount = round(org.membership_fee, 2)

        payment_data = RazorpayCustom().create_order(amount=amount, name=request.POST.get("label"))
        return render(request, "django_razorpay/checkout.html", dict(payment_data=payment_data))
    else:
        return render(request, "django_razorpay/adhoc_payment.html")