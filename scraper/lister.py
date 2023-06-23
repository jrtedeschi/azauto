import pandas as pd
import os
import json
import requests
import datetime

#  load environment variables
from dotenv import load_dotenv
import logging
from rich.logging import RichHandler
from rich import print

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")


with open("data.json") as json_file:
    data = json.load(json_file)


df = pd.DataFrame(data)

df = (
    df.groupby(["Número", "Modelo / ano", "produto"])["link_produto"]
    .count()
    .reset_index()
)

print(df)
