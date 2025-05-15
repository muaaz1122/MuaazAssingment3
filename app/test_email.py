import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_test_email(to_email: str):
    sender_email = "fawaz.anwar121@gmail.com"  # Your Gmail address
    sender_password = "sitp dakc luet wjaw"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Test Email from FastAPI Project"
    message["From"] = sender_email
    message["To"] = to_email

    html_content = """
    <html>
      <body>
        <p>This is a <strong>test email</strong> sent from your FastAPI project.</p>
      </body>
    </html>
    """
    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        print(f"✅ Email successfully sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    recipient = input("Enter recipient email:")
    send_test_email(recipient)