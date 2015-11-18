__author__ = 'naveenkumar'
import logging

from django.core.management import BaseCommand
from queue_email.email_producer_consumer import Email
from django.conf import settings

error_logger = logging.getLogger()
info_logger = logging.getLogger()

try:
    if settings.EMAIL_QUEUE.get('logger') is not None:
        if settings.EMAIL_QUEUE.get('logger').get('error') is not None:
            error_logger = logging.getLogger(settings.EMAIL_QUEUE.get('logger').get('error'))
        if settings.EMAIL_QUEUE.get('logger').get('info') is not None:
            info_logger = logging.getLogger(settings.EMAIL_QUEUE.get('logger').get('info'))
except Exception as e:
    raise AttributeError

class Command(BaseCommand):
    help = "command to process emails from sqs queue"
    option_list = BaseCommand.option_list

    def handle(self, *app_labels, **options):
        try:
            if settings.ENABLE_EMAIL_QUEUE:
                email_queue_instance = Email()
                email_queue_instance.dequeue_email()
        except Exception as e:
            error_logger.error("", exc_info=True, extra={})
            info_logger.info("Error happened while processing deque messages")