from twilio.rest import Client


class SMSSender:

    def __init__(
        self,
        account_sid,
        auth_token,
        from_number,
        to_number
    ):

        self.client = Client(
            account_sid,
            auth_token
        )

        self.from_number = from_number
        self.to_number = to_number

    def send(self, message):

        sms = self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=self.to_number
        )

        return sms.sid