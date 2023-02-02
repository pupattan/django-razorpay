from django.contrib import admin
from django.urls import path
from .views import *
app_name = "django_razorpay"
urlpatterns = [
    path('membership-fee', membership_fee, name="membership_fee"),
    path('get_member_details', get_member_details, name="get_member_details"),
    path('payment-verify', PaymentVerify.as_view(), name="payment_verify"),
    path('payment-success', payment_success, name="payment_success"),
    path('payment-failed', payment_failed, name="payment_failed"),
    path('transactions', transactions, name="transactions"),
    path('manual-transaction', manual_transaction, name="manual_transaction"),
    path('adhoc', addhoc_payment, name="addhoc_payment"),
    path('', transactions, name="index"),
]
