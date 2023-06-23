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


def get_suportebuy(session, login_url, login_payload):
    response = session.get(login_url, params=login_payload)

    parser = HTMLParser(response.text)

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
                quote_df = quote_df.rename(
                    columns={
                        "Produto Referência": "produto",
                        "Qtde. Solicitada": "qtd_solicitada",
                    }
                )[["produto", "qtd_solicitada"]].assign(
                    produto_ref=lambda x: x["produto"].str.extract(r"Ref: (.*)")
                )
                logging.info(
                    f"{datetime.datetime.now()} - retrieved {len(quote_df)} items to be fetched"
                )
                json_quote = quote_df.to_json(orient="records")
                quotes.append(json_quote)

        df["links"] = table_links
        df["quotes"] = quotes
        df["data"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        df = (
            df.drop(columns=["Unnamed: 0", "Unnamed: 1", "Unnamed: 9", "Unnamed: 10"])
            .assign(quotes=lambda x: x.quotes.apply(json.loads))
            .explode("quotes")
            .assign(
                produto=lambda x: x.quotes.apply(lambda y: y.get("produto")),
                produto_ref=lambda x: x.quotes.apply(lambda y: y.get("produto_ref")),
                qtd_solicitada=lambda x: x.quotes.apply(
                    lambda y: y.get("qtd_solicitada")
                ),
            )
        )

        df.to_json("data.json", orient="records")

        logging.info(f"{datetime.datetime.now()} - data saved to data.json")

        json_data = json.loads(df.to_json(orient="records"))

    else:
        json_data = {
            "error": "Login failed",
        }

    return json_data
