import logging
import os
from smtplib import SMTPRecipientsRefused

from redmail import EmailSender, EmailHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

EMAIL_SERVER_HOST = os.environ.get('EMAIL_SERVER_HOST')
EMAIL_SERVER_PORT = int(os.environ.get('EMAIL_SERVER_PORT'))
EMAIL_ENCODE = os.environ.get('EMAIL_ENCODE')
EMAIL_FOR_SEND = os.environ.get('EMAIL_FOR_SEND')

print(EMAIL_SERVER_HOST, EMAIL_SERVER_PORT, EMAIL_ENCODE, EMAIL_FOR_SEND)

attachments = {
    "main.py": Path("main.py"),
    "myfile.html": "<h1>Content of a HTML attachment</h1>"
}

EMAIL_MESSAGE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
</head>
<body>
<h1>Тестовое</h1>
<p>Some</p>
</body>
</html>
"""

# Configure an email sender
email = EmailSender(
    host=EMAIL_SERVER_HOST, port=EMAIL_SERVER_PORT, use_starttls=False
)

print(email.connect())

# Send an email
# try:
msg = email.send(
    sender=EMAIL_FOR_SEND,
    receivers=[FAKE_EMAIL_FOR_SEND, EMAIL_FOR_SEND],
    subject="Тестовый email",
    html=EMAIL_MESSAGE,
    attachments=attachments,
    body_images={"myimg": "static/prrda2-640x400.jpg"},
    body_params={
        "friend": "Jack"
    }
)
# except SMTPRecipientsRefused as error:
#     print(f"{error=}")

# print(f"{msg.as_string()=}")
# print(f"{msg.=}")
print(email.get_receivers([EMAIL_FOR_SEND, FAKE_EMAIL_FOR_SEND]))
# print(email.)
