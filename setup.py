__author__ = 'naveenkumar'
import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-queue-email',
    version='0.8',
    packages=['queue_email','queue_email.management', 'queue_email.management.commands'],
    include_package_data=True,
    description='Queue Email is a small app which lets any django project to send emails which are queued to AWS SQS. Queue Email also provides a command which can be run (eg. as a cron) to process those emails from the SQS queue.',
    long_description=README,
    author='Naveen Kumar',
    author_email='naveen.kumar@grofers.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'setuptools',
        'django>=1.6.5',
        'boto>=2.38.0'
    ],
    package_dir={
        'queue_email': 'queue_email',
        'queue_email.management': 'queue_email/management',
        'queue_email.management.commands': 'queue_email/management/commands'
    }
)