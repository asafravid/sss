'''Make sure to turn on less secure apps on from youur Gmail's settings under security section before executing this script.'''

import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

emailfrom = '"DEV_FINWIZ"'
emailto = "Email ID of the receiver"                #enter emai id here of receiver
fileToSend = "Auto generated Dataset\Ticker.csv"    #choose file to attach with mail
username = "Sender's Email ID here"                 #your email id through which mail will be sent
password = "Sender's Password here"                 #your id password here

msg = MIMEMultipart()
msg["From"] = emailfrom
msg["To"] = emailto
msg["Subject"] = "Screener Output"
msg.preamble = "Testing...."

ctype, encoding = mimetypes.guess_type(fileToSend)
if ctype is None or encoding is not None:
    ctype = "application/octet-stream"

maintype, subtype = ctype.split("/", 1)

if maintype == "text":
    fp = open(fileToSend)
    # Note: we should handle calculating the charset
    attachment = MIMEText(fp.read(), _subtype=subtype)
    fp.close()
elif maintype == "image":
    fp = open(fileToSend, "rb")
    attachment = MIMEImage(fp.read(), _subtype=subtype)
    fp.close()
elif maintype == "audio":
    fp = open(fileToSend, "rb")
    attachment = MIMEAudio(fp.read(), _subtype=subtype)
    fp.close()
else:
    fp = open(fileToSend, "rb")
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(fp.read())
    fp.close()
    encoders.encode_base64(attachment)
attachment.add_header("Content-Disposition", "attachment", filename=fileToSend)
msg.attach(attachment)


server = smtplib.SMTP("smtp.gmail.com:587")
server.starttls()
server.login(username,password)
server.sendmail(emailfrom, emailto, msg.as_string())
print("Success")
server.quit()





















'''import smtplib

s=smtplib.SMTP("smtp.gmail.com",587)

s.starttls()

s.login("devjuneja43@gmail.com","devjuneja#24")

message="Yo, demo mail from dj!"

s.sendmail("devjuneja43@gmail.com","devjuneja43@gmail.com",message)

s.quit()'''