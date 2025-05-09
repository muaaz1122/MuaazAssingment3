import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_verification_email(recipient_email, verification_link):
    sender_email = "your_email@gmail.com"
    sender_password = "your_email_password"

    # Email content
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Verify Your Email Address"

    body = f"""
    Hello,

    Please click the link below to verify your email address:
    {verification_link}

    Best regards,
    Your Project Team
    """
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
            print(f"✅ Verification email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Error sending verification email: {e}")
