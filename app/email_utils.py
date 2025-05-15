import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()  # ensure env vars are loaded

SMTP_SERVER = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT"))
SMTP_USER = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS")

def send_verification_email(to_email: str, verification_link: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify your account"
    message["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>"
    message["To"] = to_email

    html_content = f"""
    <html>
      <body>
        <p>Hello,</p>
        <p>Thank you for registering. Please verify your email by clicking the link below:</p>
        <a href="{verification_link}">Verify Email</a>
        <p>If you did not sign up, please ignore this email.</p>
      </body>
    </html>
    """

    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        # Use SMTP with STARTTLS on port 587
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM_ADDRESS, to_email, message.as_string())
        print(f"✅ Verification email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send verification email: {e}")
