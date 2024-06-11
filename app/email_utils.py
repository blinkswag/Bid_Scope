import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

def send_invitation_email(recipient_email, recipient_name):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Invitation to Bid Bot"
    msg['From'] = sender_email
    msg['To'] = recipient_email

    text = f"""
    Hi {recipient_name},

    You are invited to join Bid Bot, a revolutionary new way to manage your bids and projects efficiently.

    Bid Bot is designed to assist bidders with their bid files by providing smart suggestions, organizing bid data, and improving the overall bidding process.

    Visit Bid Bot: https://bidbot.blinksigns.com/

    Best regards,
    The Bid Bot Team
    """

    html = f"""
    <html>
    <head></head>
    <body>
    <p>Hi {recipient_name},</p>
    <p>You are invited to join <b>Bid Bot</b>, a revolutionary new way to manage your bids and projects efficiently.</p>
    <p><b>Bid Bot</b> is designed to assist bidders with their bid files by providing smart suggestions, organizing bid data, and improving the overall bidding process.</p>
    <p>Visit Bid Bot: <a href="https://bidbot.blinksigns.com/">https://bidbot.blinksigns.com/</a></p>
    <p>Best regards,<br>
    The Bid Bot Team</p>
    </body>
    </html>
    """

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
