# django-razorpay
Razorpay payment integration in a django project 

## Installation

1. Install using pip:

    ```bash
    pip install django-razorpay
    ```

2. Add to `INSTALLED_APPS` in your `settings.py`:

   ```python
   INSTALLED_APPS = (
       # ...
       "django_razorpay",
       # ...
   )
   
   RAZORPAY_PAYMENT_VARIANTS = {
       "public_key": "rzp_test_6GvpLSAmWckaTn",
       "secret_key": "Vo9OgyOw1FqGufiqhlWu4FyN",
       "currency": "inr"
   }
   
   COMPANY_DATA = {
    "name": "Acme Corp", 
    "email": "asa@example.com", # Optional
    "logo": "https://example.com/your_logo" # Optional
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
5. Visit http://127.0.0.1:8000/payments/ for payments.