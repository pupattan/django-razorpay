import json
import datetime
import time
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
    razorpay_instance = RazorpayCustom()
    if request.method == "POST":
        org = Organization.objects.last()
        if razorpay_instance.is_fee_applicable():
            amount = razorpay_instance.get_amount_with_charges(org.membership_fee)
        else:
            amount = round(org.membership_fee, 2)

        phonenumber = request.POST.get("phonenumber")
        name = request.POST.get("name")
        email = request.POST.get("email")
        existing_member = Member.objects.filter(name=name).first()
        if existing_member and phonenumber and email:
            existing_member.email = email
            existing_member.phone = phonenumber
            existing_member.save()

        if razorpay_instance.use_payment_link():
            return redirect(razorpay_instance.create_payment_link(amount=amount,
                                                                  email=email,
                                                                  name=name,
                                                                  phonenumber=phonenumber,
                                                                  reference_id="membership_fee__"
                                                                               + str(existing_member.id)
                                                                               + "__"))
        else:
            payment_data = razorpay_instance.create_order(amount=amount,
                                                          email=email,
                                                          name=name,
                                                          phonenumber=phonenumber)

            return render(request, "django_razorpay/checkout.html", dict(payment_data=payment_data))
    else:
        use_rz_payment_link = razorpay_instance.use_payment_link() or False
        return render(request, "django_razorpay/membership_fee.html", dict(members=members,
                                                                           use_rz_payment_link=use_rz_payment_link))


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

            if rz.use_payment_link():
                payment_link_reference_id = self.request.GET.get('razorpay_payment_link_reference_id')
                razorpay_payment_link_id = self.request.GET.get('razorpay_payment_link_id')
                payment_link = rz.client.payment_link.fetch(razorpay_payment_link_id)
                if 'add_hoc' in payment_link_reference_id:
                    label = payment_link["notes"]["label"]
                elif "membership_fee" in payment_link_reference_id:
                    ids = payment_link_reference_id.split("__")
                    member = Member.objects.filter(id=int(ids[1])).first()
                    label = str(member.name) + "(Fee)"

            else:   # for checkout page
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

            if rz.is_fee_applicable():
                amount = rz.get_amount_deducting_charges(Decimal(amount))

            if Transaction.objects.filter(data__id=razorpay_payment_id).exists():
                return reverse("django_razorpay:payment_failed")

            add_amount_to_total(amount, razorpay_payment_id)
            Transaction.objects.create(amount=amount,
                                       data=payment,
                                       label=label,
                                       payment_type=Transaction.INCOMING)
            messages.success(self.request, "Payment successful....")
            return reverse("django_razorpay:transactions")
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
                                                 ).order_by('-created_at')
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
        razorpay_instance = RazorpayCustom()
        if razorpay_instance.is_fee_applicable():
            amount = razorpay_instance.get_amount_with_charges(Decimal(request.POST.get("amount")))
        else:
            amount = round(Decimal(request.POST.get("amount")), 2)

        if razorpay_instance.use_payment_link():
            return redirect(razorpay_instance.create_payment_link(amount=amount,
                                                                  label=request.POST.get("label"),
                                                                  reference_id="add_hoc_"))
        else:
            return render(request, "django_razorpay/checkout.html",
                          dict(payment_data=RazorpayCustom().create_order(amount=amount,
                                                                          name=request.POST.get("label"))))
    else:
        return render(request, "django_razorpay/adhoc_payment.html")