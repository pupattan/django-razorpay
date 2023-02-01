from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def organization_name():
    return settings.DJ_RAZORPAY.get('organization_name')


@register.simple_tag
def organization_logo():
    return settings.DJ_RAZORPAY.get('organization_logo')


@register.simple_tag
def nav_links():
    return settings.DJ_RAZORPAY.get('nav_links')