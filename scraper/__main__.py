import requests
import json
import os
import pandas as pd
from selectolax.parser import HTMLParser
import datetime

#  load environment variables
from dotenv import load_dotenv
import logging
from rich.logging import RichHandler
from rich import print


from meli.functions import request_meli
from suportebuy.functions import get_suportebuy



FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")


load_dotenv()

#  load the API key from the environment variable
SUPORTEBUY_USER = os.getenv("SUPORTEBUY_USER")
SUPORTEBUY_PASS = os.getenv("SUPORTEBUY_PASS")


# Create a session

logging.info(f"{datetime.datetime.now()} - Creating session")
session = requests.Session()

login_url = "https://sistema.suportebuy.com.br/centralDoFornecedor/loginScript.asp"

listing_url = "https://lista.mercadolivre.com.br/"

# Set the appropriate HTTP headers
session.headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:87.0) Gecko/20100101 Firefox/87.0",
    "Accept": "*/*",
    "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://www.mercadolivre.com.br",
    "Connection": "keep-alive",
    "Referer": "https://www.mercadolivre.com.br/",
}

logging.info(f"session headers: {session.headers}")
# get the _csrf token
logging.info(f"{datetime.datetime.now()} - Getting CSRF token")
session.get(
    "https://www.mercadolivre.com.br/navigation/addresses-hub?go=https%3A%2F%2Flista.mercadolivre.com.br%2F93384470&mode=embed",
)
CSRF_TOKEN = session.cookies.get_dict()["_csrf"]

logging.info(f"{datetime.datetime.now()} - CSRF token: {CSRF_TOKEN}")

zip_payload = {
    "_csrf": "NYUN3g2F-TYjyvRU0eMPMuOQ8L72JQ7V6tiI",
    "action": "zipcode",
    "hasAddresses": "false",
    "zipcode": "30550-500",
    "_csrf": CSRF_TOKEN,
}

logging.info(f"{datetime.datetime.now()} - payload: {zip_payload}")

logging.info(f"{datetime.datetime.now()} - Setting zip code")
meli_response = session.post(
    "https://www.mercadolivre.com.br/navigation/addresses-hub?go=https%3A%2F%2Flista.mercadolivre.com.br%2F93384470&mode=embed",
    data=zip_payload,
)

logging.info(f"{datetime.datetime.now()} meli response: {meli_response.text}")

# Perform login
login_payload = {
    "login": SUPORTEBUY_USER,
    "senha": SUPORTEBUY_PASS,
}

# clean headers
session.headers.clear()

logging.info(f"{datetime.datetime.now()} - Logging in")

# Check if login was successful (you need to inspect the response content to determine the appropriate condition)

selectors = [
    "#root-app > div > div.ui-search-main.ui-search-main--exhibitor.ui-search-main--only-products.ui-search-main--with-topkeywords.shops__search-main > section > ol",
    "#root-app > div > div.ui-search-main.ui-search-main--exhibitor.ui-search-main--without-header.ui-search-main--only-products.shops__search-main > section > ol",
    "#root-app > div > div.ui-search-main.ui-search-main--without-header.ui-search-main--only-products.shops__search-main > section > ol",
]


json_data = get_suportebuy(session, login_url, login_payload)

final_data = []


for query in json_data:

    for item in request_meli(session, query, listing_url, selectors):

        logging.info(f"{datetime.datetime.now()} - Appending item")

        logging.info(f"{datetime.datetime.now()} - {item}")

        final_data.append(item)


final_df = pd.DataFrame(final_data)


final_df.to_json("final_data.json", orient="records")




session.close()
