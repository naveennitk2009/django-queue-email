=====
Queue Email
=====

Queue Email is a small app which lets any django project to send emails which are queued to AWS SQS.
Queue Email also provides a command which can be run to process those emails from the SQS queue every 0.05s .

Setup
-----------
1. Add to requirements.pip of your project::
    
    git+https://github.com/grofers/django-queue-email.git

2. Install the app::
    
    pip install -r requirements.pip

Quick start
-----------

1. Add "queue_email" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'queue_email',
    )

2. Add following to your settings.py::

    EMAIL_QUEUE = {
        'aws' : {
            'region': AWS_REGION,
            'key': AWS_KEY,
            'secret': AWS_SECRET,
            'queue': SQS_EMAIL_QUEUE,
            'attachment_bucket' : EMAIL_ATTACHMENT_S3_BUCKET, #required if you are planning to send emails with attachments
            's3-url-endpoint' : None #This is the endpoint after attachment files gets uploaded to s3. This is required for sqs to pick up and process while sending the mail
                                    #This by default is "https://s3-" + settings.EMAIL_QUEUE['aws']['region'] + ".amazonaws.com/" + settings.EMAIL_QUEUE['aws']['attachment_bucket'] + '/'
        },
        'logger' : {
            'error': Error_Logger,
            'info' : Info_Logger
        }
    }

    EMAIL_HOST = EMAIL_SMTP_HOST
    EMAIL_PORT = EMAIL_SMTP_PORT
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD
    DEFAULT_EMAIL_ID = DEFAULT_EMAIL_ID #will be used in case of DEBUG is true

3. Add this to your settings file to enable equeue of emails and process of emails from queue::

    ENABLE_EMAIL_QUEUE = False

4. Import Email class::

    from queue_email.email import Email

5. Enqueue emails::

    Email().enqueue_email(send_from, send_to, subject, body, attachements, cc=None, **extras)
    
    send_from : Email id of the sender <String>
    send_to : List of Email id of the receiver [<String>]
    subject : Subject of the email <String>
    body : Body of email <String>
    cc : List of cc email ids [<String>]
    attachments: List of attachment dict [<Attachment Dict>] . <Attachment dict> is { 'url' : <Local absoulte path of the attachment>, 'type' : <Type of attachment like pdf, png, jpg, xls, doc, etc>}
    extras : Extras that can be sent. It can be used in case you are thinking of extending the functionality of the class method. <Dict>


6. Extending/Overriding methods that can be used::
    
    In some cases you might want to extend or override the functionality of methods used in Email class.
    
    Following methods are available -
    
    a. enqueue_email(send_from, send_to, subject, body, cc=None, **extras)
        Call when queue an email.
    
    b. payload_builder(**kwargs)
        This method builds the payload message that will be sent.
    
    c. pre_enqueue_send(**kwargs)
        This gets called before the email is enqueued.
    
    d. post_enqueue_send(**kwargs)
        This gets called after the email is enqueued.
    
    e. on_enqueue_error(**kwargs)
        This gets called when enqueue error happens.
    
    f. dequeue_email()
        Call when deque an email.
    
    g. pre_dequeue(**kwargs)
        This gets called when dequeue starts in chunks of 5 emails.
    
    h. post_dequeue(**kwargs)
        This gets called when dequeue completes and emails are processed in chunks of 5 emails.
    
    i. on_dequeue_error(**kwargs)
        This gets called when dequeue error happens.


7. Run email dequeue listener command ::

    python manage.py process_email
