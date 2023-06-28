from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import random

class MessageHandler:
    phone_number = None
    otp = None

    def __init__(self, phone_number, otp):
        self.phone_number = "+91" + str(phone_number)
        self.otp = otp

    def sent_otp_on_phone(self):
        # Send OTP on phone
        client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)

        try:
            message = client.messages.create(
                body='Your OTP for login is ' + str(self.otp),
                from_='+12705181845',
                to=self.phone_number
            )
            print("Message sent successfully. SID:", message.sid)
        except TwilioRestException as e:
            print("Error sending message:", str(e))

