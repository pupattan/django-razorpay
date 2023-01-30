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
    path('transactions', transactions_list, name="transactions_list"),
    path('expense', add_expense, name="add_expense"),
]
