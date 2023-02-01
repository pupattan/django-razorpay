from django.core.management.base import BaseCommand

from django_razorpay.models import Balance, Organization


class Command(BaseCommand):
    help = 'Initialize models'

    def handle(self, *args, **kwargs):
        Organization.objects.create()
        Balance.objects.create(amount=0, label="init")
        self.stdout.write("Initialization  successful")