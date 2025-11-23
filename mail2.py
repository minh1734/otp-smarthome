import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(nguoinhan,noidung):
    taikhoan = "luisaccforwork@gmail.com"
    matkhau = "jfow ozvc tivl vqkq"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Test Email from Python"
    message["From"] = taikhoan
    message["To"] = nguoinhan

    text = noidung

    message.attach(MIMEText(text, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(taikhoan, matkhau)
        server.sendmail(taikhoan, nguoinhan, message.as_string())