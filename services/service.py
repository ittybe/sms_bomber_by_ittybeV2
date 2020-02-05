import random
import string

from stem import Signal
from stem.control import Controller

import logging

import aiohttp


class Service:
    user_agent = "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36"
    client = aiohttp.ClientSession()
    
    wait_new_ip = None
    is_ip_available = True
    # @staticmethod
    # async def close():
    #     if Service.client.session is not None:
    #         # apparently this is supposed to return a future?
    #         return Service.client.session.close()
    # signal TOR for a new connection
    @staticmethod
    def renew_connection(password):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=password)
            controller.signal(Signal.NEWNYM)
            # func check new num in some cases doesnt work
            # so we check vars here
            Service.wait_new_ip = controller.get_newnym_wait()
            Service.is_ip_available = controller.is_newnym_available()
    
    def __init__(self, phone, phone_code):
        self.phone = phone
        self.phone_code = phone_code
        self.formatted_phone = self.phone_code + self.phone

        self.client.headers = {"User-Agent": self.user_agent}

        self.username = self.password = "".join(
            random.choice(string.ascii_letters) for _ in range(12)
        )
        self.email = self.username + "@gmail.com"

        self.get = self.client.get
        self.post = self.client.post
        self.options = self.client.options
