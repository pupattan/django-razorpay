from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Member)
admin.site.register(Transaction)
admin.site.register(Balance)
admin.site.register(Organization)