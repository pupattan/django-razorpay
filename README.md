# django-razorpay
Razorpay payment integration in a django project 

## Installation

1. Install using pip:

    ```bash
    pip install django-razorpay
    ```

   1. Add to `INSTALLED_APPS` in your `settings.py`:

      ```python
      INSTALLED_APPS = (
          # ...
          "django_razorpay",
          # ...
      )
   
      DJ_RAZORPAY = {
       "organization_name": "Acme Corp",
       "organization_email": "something@gmail.com",  # Optional
       "organization_logo": "https://company.com/orlogo.png",  # Optional,
       "nav_links": [("Membership Fee", "/payments/membership-fee"),
                     ("Transactions", "/payments/transactions"),
                     ("Adhoc Pay", "/payments/adhoc")
                     ],
       "RAZORPAY_VARIANTS": {
           "public_key": "rzp_test_6GvpLSAmWckaTn",
           "secret_key": "Vo9OgyOw1FqGufiqhlWu4FyN",
           "currency": "inr"
       },
       "RAZORPAY_ENABLE_CONVENIENCE_FEE": True # You charge a convenience fee to your customer.
}

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}
   ```
   
3. Include the django_razorpay URLconf in your project urls.py like this to `urls.py`:

   ```python
   from django.urls import path, include
   urlpatterns = [
       path('payments/', include('django_razorpay.urls', namespace="django_razorpay")),
       # ....
   ]
   ```
   
4. Run ``python manage.py migrate`` to create the django_razorpay models.
5. Run ``python manage.py dj_razorpay_init`` to initialize models models. 
6. If you want to add members, create superuser, login and add.
7. Visit http://127.0.0.1:8000/payments/ for payments.

## Demo
A demo app is provided in example. 
You can run it from your virtualenv with python manage.py runserver.