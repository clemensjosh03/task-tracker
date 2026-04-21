import smtplib
from email.mime.text import MIMEText

EMAIL = "clemensjosh03@gmail.com"
PASSWORD = "dxjxyaxnljugqvek"

def send_email(to_email, subject, html_content):
    msg = MIMEText(html_content, "html")  # 👈 IMPORTANT (HTML mode)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
