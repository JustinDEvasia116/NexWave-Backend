from django.conf import settings
from twilio.rest import Client
import random

class MessageHandler:
    phone_number = None
    otp = None

    def __init__(self, phone_number, otp):
        self.phone_number = "+91" + str(phone_number)
        self.otp = otp

    def sent(self):
        print("ACCOUNT_SIDD:", settings.TWILIO_ACCOUNT_SIDD)
        print("AUTH_TOKENN:", settings.TWILIO_AUTH_TOKENN)
       
