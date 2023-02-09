from setuptools import find_packages, setup

setup(
    name='django-razorpay',
    version='1.0.17',
    url='https://github.com/pupattan/django-razorpay',
    license='MIT',
    author='pupattan',
    author_email='pulak.pattanayak@gmail.com',
    description='Razorpay payment integration in a django project ',
    packages=find_packages(exclude=["tests.*", "tests", "example.*", "example", "docs"]),
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=["Django>=3.2", 'python-dateutil', 'razorpay'],
)
