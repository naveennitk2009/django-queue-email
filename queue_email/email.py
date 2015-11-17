__author__ = 'naveenkumar'
from django.conf import settings
import boto.sqs
from boto.sqs.message import Message
import logging
import json
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
import smtplib

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

class Email(object):

    def _establish_aws_connection(self):
        if settings.ENABLE_EMAIL_QUEUE:
            sqs_conn = boto.sqs.connect_to_region(
            settings.EMAIL_QUEUE['aws']['region'], aws_access_key_id=settings.EMAIL_QUEUE['aws']['key'], aws_secret_access_key=settings.EMAIL_QUEUE['aws']['secret'])
            self._email_queue = sqs_conn.get_queue(settings.EMAIL_QUEUE['aws']['queue'])
            if self._email_queue is None:
                self._email_queue = sqs_conn.create_queue(settings.EMAIL_QUEUE['aws']['queue'])


    def enqueue_email(self ,send_from, send_to, subject, body, cc=None, **extras):
        try:
            self._send_from = send_from
            self._send_to = send_to
            self._subject = subject
            self._body = body
            self._cc = cc
            self._extras = extras
            self._enqueue_email()
        except Exception as e:
            raise e

    def payload_builder(self, **kwargs):
        try:
            self._payload = {
                "from": self._send_from,
                "to": self._send_to,
                "subject": self._subject,
                "body": self._body,
                "cc": [] if self._cc is None else self._cc
            }
        except Exception as e:
            raise e

    def pre_enqueue_send(self, **kwargs):
        pass

    def post_enqueue_send(self, **kwargs):
        pass

    def on_enqueue_error(self, **kwargs):
        pass

    def _enqueue_email(self):
        try:
            if not settings.ENABLE_EMAIL_QUEUE:
                return

            self._establish_aws_connection()
            self.payload_builder()
            self.pre_enqueue_send()
            message = Message()
            message.set_body(json.dumps(self._payload))
            self._email_queue.write(message)
            info_logger.info("Email queued to: " + self._send_to + " with subject: " + self._subject)
            self.post_enqueue_send()
        except Exception as e:
            self.on_enqueue_error()
            error_logger.error("", exc_info=True, extra={})
            info_logger.info("Email skipped to: " + self._send_to + " with subject: " + self._subject)
            raise  e

    def dequeue_email(self):
        self._dequeue_email()

    def pre_dequeue(self, **kwargs):
        pass

    def post_dequeue(self, **kwargs):
        pass

    def on_dequeue_error(self, **kwargs):
        pass

    def _dequeue_email(self):
        if not settings.ENABLE_EMAIL_QUEUE:
            return

        self._establish_aws_connection()
        sleep_time = 0.05
        while 1 == 1:
            self.pre_dequeue()
            rs = self._email_queue.get_messages(5)
            if len(rs) > 0:
                sleep_time = 0.05
                for message in rs:
                    try:
                        message_body = json.loads(message.get_body())
                        from_email = message_body.get('from')
                        to_email = message_body.get('to')
                        subject = message_body.get('subject')
                        body = message_body.get('body')
                        cc = message_body.get('cc')
                        if self._process_email({
                            "send_from" : from_email,
                            "send_to" : to_email,
                            "subject": subject,
                            "body" : body,
                            "cc" : cc
                        }):
                            self.post_dequeue()
                            self._email_queue.delete_message(message)
                            info_logger.info("Email sent to: " + self._send_to + " with subject: " + self._subject)
                    except:
                        self.on_dequeue_error()
                        error_logger.error("", exc_info=True, extra={})
                        info_logger.info("error while reading message: " + message.get_body())
                        raise e
            else:
                info_logger.info("No emails queued at " + str(datetime.now()))
                sleep(sleep_time)
                if sleep_time < 3:
                    sleep_time *= 2

    def _process_email(self, **kwargs):
        try:
            send_to = kwargs.get('send_to')
            if settings.DEBUG:
                send_to = settings.DEFAULT_EMAIL_ID

            msg = MIMEMultipart()
            msg['Subject'] = kwargs.get('subject')
            msg['From'] = kwargs.get('send_from')
            msg['To'] = send_to
            msg['cc'] = [] if kwargs.get('cc') is None else kwargs.get('cc')
            msg.attach(MIMEText(kwargs.get('body'), 'html', 'utf-8'))

            smtp_server = settings.EMAIL_HOST
            smtp_port = settings.EMAIL_PORT
            user_name = settings.EMAIL_HOST_USER
            password = settings.EMAIL_HOST_PASSWORD

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.ehlo()
            server.login(user_name, password)
            server.sendmail(kwargs.get('send_from'), send_to, msg.as_string())
            server.quit()
        except Exception as e:
            error_logger.error("", exc_info=True, extra={})
            return False
        return True