from django.conf import settings
from twilio.base.exceptions import TwilioException
from twilio.rest import Client
import random

class MessageHandler:
    phone_number = None
    message = None
    
    def __init__(self, phone_number, message):
        self.phone_number = str(phone_number)
        self.message = message

    def sent_activation_sms(self):
        # Send OTP on phone
        client = Client(settings.TWILIO_ACCOUNT_SIDD,settings.TWILIO_AUTH_TOKENN)

        try:
            message = client.messages.create(
                body=self.message,
                from_='+12705181845',
                to=self.phone_number
            )
            print("Message sent successfully. SID:", message.sid)
            return message.sid
        except TwilioException as e:
            print("Error sending message:", str(e))

