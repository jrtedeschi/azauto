import requests
import json
import os
import pandas as pd
from selectolax.parser import HTMLParser
import datetime

#  load environment variables
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

#  load the API key from the environment variable
SUPORTEBUY_USER = os.getenv("SUPORTEBUY_USER")
SUPORTEBUY_PASS = os.getenv("SUPORTEBUY_PASS")


# Create a session

logging.info(f"{datetime.datetime.now()} - Creating session")
session = requests.Session()

login_url = "https://sistema.suportebuy.com.br/centralDoFornecedor/loginScript.asp"


zip_payload = {
    "_csrf": "NYUN3g2F-TYjyvRU0eMPMuOQ8L72JQ7V6tiI",
    "action": "zipcode",
    "hasAddresses": "false",
    "zipcode": "30550-500",
}

logging.info(f"{datetime.datetime.now()} - Setting zip code")
session.post(
    "https://www.mercadolivre.com.br/navigation/addresses-hub?go=https%3A%2F%2Flista.mercadolivre.com.br%2F93384470&mode=embed",
    data=zip_payload,
)


# Perform login
login_payload = {
    "login": SUPORTEBUY_USER,
    "senha": SUPORTEBUY_PASS,
}
logging.info(f"{datetime.datetime.now()} - Logging in")
response = session.get(login_url, params=login_payload)

# Check if login was successful (you need to inspect the response content to determine the appropriate condition)
if response.status_code == 200:
    # Continue with the session
    logging.info(f"{datetime.datetime.now()} - Login successful")
    # Example: Access another page after login
    other_page_url = "https://sistema.suportebuy.com.br/centralDoFornecedor/com/processos/default.asp"
    response = session.get(other_page_url)

    tree = HTMLParser(response.text)
    table = tree.css_first("table")

    # make a json template iterating through table head
    df = pd.read_html(table.html)[0]
    # iterate through table to get the links
    table_links = []
    quotes = []
    logging.info(f"{datetime.datetime.now()} - found {len(table.css('tr'))} rows")

    for row in table.css("tr"):
        if row.css_matches("a"):
            quote_url = (
                "https://sistema.suportebuy.com.br/centralDoFornecedor/com/processos/"
                + row.css("a")[1].attributes["href"]
            )
            table_links.append(quote_url)
            # follow url
            response = session.get(quote_url)
            quote_tree = HTMLParser(response.text)
            quote_table = quote_tree.css_first("table")
            logging.info(f"{datetime.datetime.now()} - {quote_url}")
            quote_df = pd.read_html(quote_table.html)[0]
            quote_df = (
                quote_df.rename(
                    columns={
                        "Produto Referência": "produto",
                        "Qtde. Solicitada": "qtd_solicitada",
                    }
                )[["produto", "qtd_solicitada"]]
                # regexp to get the text after `EMBLEMA DA PORTA TRAS DIR Ref: 100207595`
                .assign(produto_ref=lambda x: x["produto"].str.extract(r"Ref: (.*)"))
            )
            json_quote = quote_df.to_json(orient="records")
            quotes.append(json_quote)

    df["links"] = table_links
    df["quotes"] = quotes
    df["data"] = datetime.datetime.now()
    df.to_csv("data.csv", index=False)

else:
    print("Login failed.")

# Don't forget to close the session when you're done
session.close()
