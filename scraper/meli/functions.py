import requests
import json
import os
import pandas as pd
from selectolax.parser import HTMLParser
import datetime
import logging
from rich.logging import RichHandler
from rich import print


FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)


def check_selector(parser, selectors):
    """Check if selector is present in page, if not, try the next one, if none is found, return None"""
    for selector in selectors:
        if parser.css_first(selector):
            return selector
        else:
            logging.info(f"{datetime.datetime.now()} - Selector {selector} not found")
            continue

    logging.error(f"{datetime.datetime.now()} - No selector found")
    return "None"


def request_meli(session, query, listing_url, selectors):
    """Make request to mercadolivre and return data"""

    logging.info(f"{datetime.datetime.now()} - Querying: {query['produto']}")

    # make request to mercadolivre using full product name
    if query["produto_ref"] is None:
        query_url = listing_url + query["produto"]
        r = session.get(query_url)
        logging.info(f"{datetime.datetime.now()} - URL {query_url}")
    else:
        query_url = listing_url + query["produto_ref"]
        r = session.get(query_url)
        logging.info(f"{datetime.datetime.now()} - URL {query_url}")
    parser = HTMLParser(r.text)
    logging.info(f"{datetime.datetime.now()} - Parsing data")
    selector = check_selector(parser, selectors)
    if selector is "None":
        logging.error(f"{datetime.datetime.now()} - No results found")
        yield query | {"link_produto": None, "titulo": None, "preco": None}

    try:
        items_list = parser.css_first(selector)
        items_list = items_list.css("li")
        logging.info(f"{datetime.datetime.now()} - Found {len(items_list)} items")
        for i, item in enumerate(items_list):
            if (
                item.attributes.get("class")
                != "ui-search-layout__item shops__layout-item"
            ):
                pass
            if item.css_first("a"):
                link = item.css_first("a").attributes["href"]
                logging.info(f"{datetime.datetime.now()} - Link: {link}")
                title = item.css_first("a").attributes["title"]
                logging.info(f"{datetime.datetime.now()} - Item {i+1}: {title}")
                price = item.css_first("span.price-tag-fraction").text()
                if item.css_first("span.price-tag-cents"):
                    cents = item.css_first("span.price-tag-cents").text()
                    price = price + "," + cents
                logging.info(f"{datetime.datetime.now()} - Price: {price}")
                # get query dict and append data in new row
                row = query | {
                    "link_produto": link,
                    "titulo": title,
                    "preco": price,
                }
                # append row to json
                yield row
            else:
                logging.info(f"{datetime.datetime.now()} - Item {i+1} is an ad")

    except Exception as e:
        logging.error(f"{datetime.datetime.now()} - Error: {e}")

        yield query | {"link_produto": None, "titulo": None, "preco": None}
