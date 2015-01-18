from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives 
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from django.utils.html import strip_tags

settings.configure(TEMPLATE_DIRS=("/Users/simcen/Documents/Scripts/_mail/",), EMAIL_HOST="127.0.0.1", EMAIL_PORT=2525)
 
# Some generic stuff to parse with
username = "fry"
password = "password_yo"
full_name = "Philip J Fry"
 
content = get_template('django_email_template.html').render(
        Context({
            'username': username,
            'password': password,
            'full_name': full_name
        })
    )

text_content = strip_tags(content)

subject, from_email, to = 'hello', 'from@example.com', 'to@example.com'
msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
#msg.content_subtype = "html"
msg.attach_alternative(content, "text/html")
msg.send()