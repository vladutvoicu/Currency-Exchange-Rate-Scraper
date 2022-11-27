import pymongo
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bs4 import BeautifulSoup
import requests
import time
import json

load_dotenv(".env")
uri = os.getenv("MONGODB_URI")

client = MongoClient(uri)
db = client["currencyexchangerates"]
collection = db["rates"]
cursor = collection.find({})

def scheduled_job():
    url = "http://www.floatrates.com/daily/EUR.xml"
    result = requests.get(url).text
    doc = BeautifulSoup(result, 'html.parser')
    items = doc.find_all("item")

    update_date = items[0].pubdate.string

    rates_dict = {}
    for index in range(len(items)):
        rates_dict[f"{items[index].targetcurrency.string}"] = float(items[index].exchangerate.string.replace(",",""))

    sorted_list = sorted(rates_dict.items(), key=lambda x: x[1])

    rates_dict = {}
    for i in range(len(sorted_list)):
        rates_dict[f"{sorted_list[i][0]}"] = float("{:.6f}".format(sorted_list[i][1]))

    rates = {}
    for index in range(len(sorted_list)):
        currency = sorted_list[index][0]

        if currency == "CHF":
            rates["EUR"] = rates_dict

        time.sleep(1)
        url = f"http://www.floatrates.com/daily/{currency}.xml"
        result = requests.get(url).text
        doc = BeautifulSoup(result, 'html.parser')
        items = doc.find_all("item")

        rates_dict = {}
        for index in range(len(items)):
            rates_dict[f"{items[index].targetcurrency.string}"] = float(items[index].exchangerate.string.replace(",",""))

        sorted_list = sorted(rates_dict.items(), key=lambda x: x[1])

        rates_dict = {}
        for i in range(len(sorted_list)):
            rates_dict[f"{sorted_list[i][0]}"] = float("{:.6f}".format(sorted_list[i][1]))

        rates[f"{currency}"] = rates_dict

        rates["DATE"] = update_date

    collection.update_one({"_id":0}, {"$set":{"currencies": rates}})
            

    url = "https://www.coindesk.com/data/"
    result = requests.get(url).text
    doc = BeautifulSoup(result, 'html.parser')
    cards_grid = doc.find(class_="price-liststyles__CardGrid-ouhin1-1 eeDfav")
    cards = cards_grid.find_all("a")

    rates = {}
    rates_dict = {}
    for i in range(0, len(cards)):
        try:
            currency = cards[i].find(class_="typography__StyledTypography-owin6q-0 fUOSEs").text
            rate = cards[i].find(class_="typography__StyledTypography-owin6q-0 brrRIQ").text.replace("$", "")
            
            rates_dict[currency] = rate.replace(",", "")
            rates["USD"] = rates_dict
        except:
            break

    for doc in cursor:
        usd_rates = doc["currencies"]["USD"]

    for key, value in usd_rates.items():
        rates_dict_ = {}
        for key_, value_ in rates_dict.items():
            rates_dict_[key_] = "{:.6f}".format(float(str(value).replace(",", "")) * float(str(value_).replace(",", "")))
        rates[key] = rates_dict_

    rates["DATE"] = update_date

    collection.update_one({"_id":0}, {"$set":{"crypto": rates}})

scheduled_job()