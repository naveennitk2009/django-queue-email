__author__ = 'naveenkumar'
from django.conf import settings
import boto.sqs
from boto.sqs.message import Message
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import logging
import json
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from time import sleep
import smtplib
import urlparse
import os.path
import copy
from tempfile import TemporaryFile

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

    def __init__(self):
        self._email_queue = None
        self._s3_conn = None

    def _establish_aws_connection(self):
        try:
            if settings.ENABLE_EMAIL_QUEUE:
                sqs_conn = boto.sqs.connect_to_region(
                settings.EMAIL_QUEUE['aws']['region'], aws_access_key_id=settings.EMAIL_QUEUE['aws']['key'], aws_secret_access_key=settings.EMAIL_QUEUE['aws']['secret'])
                self._email_queue = sqs_conn.get_queue(settings.EMAIL_QUEUE['aws']['queue'])
                if self._email_queue is None:
                    self._email_queue = sqs_conn.create_queue(settings.EMAIL_QUEUE['aws']['queue'])
        except Exception as e:
            raise e


    def enqueue_email(self ,send_from, send_to, subject, body,attachments, cc=None, **extras):
        try:
            self.send_from = send_from
            self.send_to = send_to
            self.subject = subject
            self.body = body
            self.cc = cc
            self.extras = extras
            self.attachments = attachments
            self._enqueue_email()
        except Exception as e:
            raise e

    def payload_builder(self, **kwargs):
        try:
            self._payload = {
                "from": self.send_from,
                "to": self.send_to,
                "subject": self.subject,
                "body": self.body,
                "cc": [] if self.cc is None else self.cc,
                "attachments": [] if self.attachments is None else self._upload_attachments_to_s3()
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
            info_logger.info("Email queued to: " + str(self.send_to) + " with subject: " + self.subject)
            self.post_enqueue_send()
        except Exception as e:
            self.on_enqueue_error()
            error_logger.error("", exc_info=True, extra={})
            info_logger.info("Email skipped to: " + self.send_to + " with subject: " + self.subject)
            raise  e

    def dequeue_email(self):
        try:
            self._dequeue_email()
        except Exception as e:
            raise e

    def pre_dequeue(self, **kwargs):
        pass

    def post_dequeue(self, **kwargs):
        pass

    def on_dequeue_error(self, **kwargs):
        pass

    def _dequeue_email(self):
        if not settings.ENABLE_EMAIL_QUEUE:
            return

        try:
            self._establish_aws_connection()
        except Exception as e:
            raise e

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
                        attachments = message_body.get('attachments')
                        if self._process_email(**{
                            "send_from" : from_email,
                            "send_to" : to_email,
                            "subject": subject,
                            "body" : body,
                            "cc" : cc,
                            "attachments" : attachments
                        }):
                            self.post_dequeue()
                            self._email_queue.delete_message(message)
                            info_logger.info("Email sent to: " + str(to_email) + " with subject: " + subject)
                    except Exception as e:
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

            if self._s3_conn is None:
                self._s3_conn = S3Connection(settings.EMAIL_QUEUE['aws']['key'], settings.EMAIL_QUEUE['aws']['secret'])
            bucket = self._s3_conn.get_bucket(settings.EMAIL_QUEUE['aws']['attachment_bucket'])


            attachments = kwargs.get('attachments')
            if attachments is not None:
                for attachment in attachments:
                    url = attachment.get('url')
                    contenttype = attachment.get('type')
                    if contenttype is not None:
                        with TemporaryFile() as f:
                            k = Key(bucket)
                            k.key = os.path.basename(urlparse.urlsplit(url).path)
                            k.get_contents_to_file(f)
                            f.seek(0)

                        # if contenttype == 'image':
                        #     img = open(url, 'rb').read()
                        #     imgMsg = MIMEImage(img)
                        #     imgMsg.add_header('Content-ID', '<image1>')
                        #     filename =  os.path.basename(urlparse.urlsplit(url).path)
                        #     imgMsg.add_header('Content-Disposition', 'attachment', filename=filename)
                        #     msg.attach(imgMsg)

                            content = f.read()
                            applicationMsg = MIMEApplication(content, contenttype)
                            applicationMsg.add_header('Content-ID', '<' + contenttype + '1' + '>')
                            filename = os.path.basename(urlparse.urlsplit(url).path)
                            applicationMsg.add_header('Content-Disposition', 'attachment', filename=filename)
                            msg.attach(applicationMsg)

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

    def _upload_attachments_to_s3(self):
        try:
            if self._s3_conn is None:
                self._s3_conn = S3Connection(settings.EMAIL_QUEUE['aws']['key'], settings.EMAIL_QUEUE['aws']['secret'])
            bucket = self._s3_conn.get_bucket(settings.EMAIL_QUEUE['aws']['attachment_bucket'])
            uploaded_attachments = []
            for attachment in self.attachments:
                k = Key(bucket)
                filename =  os.path.basename(urlparse.urlsplit(attachment.get('url')).path)
                k.key = filename
                k.set_contents_from_filename(attachment.get('url'))
                if settings.EMAIL_QUEUE['aws']['s3-url-endpoint'] is None:
                    s3_url_endpoint = "https://s3-" + settings.EMAIL_QUEUE['aws']['region'] + ".amazonaws.com/" + settings.EMAIL_QUEUE['aws']['attachment_bucket'] + '/'
                else:
                    s3_url_endpoint = settings.EMAIL_QUEUE['aws']['s3-url-endpoint']
                s3_uploaded_url = s3_url_endpoint + filename
                uploaded_attachment = copy.deepcopy(attachment)
                uploaded_attachment['url'] = s3_uploaded_url
                uploaded_attachments.append(uploaded_attachment)

            return uploaded_attachments
        except Exception as e:
            raise e




