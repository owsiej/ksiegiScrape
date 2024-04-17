# Scrape BOT

> BOT used to scrape official polish land registers.

## Table of Contents

- [General Info](#general-information)
- [Technologies Used](#technologies-used)
- [Setup](#setup)
- [Features](#features)

## General Information

- BOT scrape polish land registers from official government side and save that data to database.

## Technologies Used

Main techs used in app are:

- Python 3.11
- Scrapy
- Scrapy/Splash
- MongoDb

All versions you can check in [requirement.txt file](https://github.com/owsiej/ksiegiScrape/blob/main/requirements.txt).

## Setup

To make it run:

- install [Python 3.11](https://www.python.org/downloads/release/python-3110/)
- install [pip](https://pip.pypa.io/en/stable/installation/)
- install all requirements in main dir using

```
$ pip install -r requirements.txt
```

- make .env file in `./ksiegi` and create following environment variables:

```
MONGO_URL=
MONGO_DATABASE_NAME=
MONGO_DATABASE_COLLECTION_NAME=
SPLASH_URL=
LOG_FILE=
```

- run Splash HTTP API (more info [here](https://github.com/scrapy-plugins/scrapy-splash)) using:

```
$ docker run -p 8050:8050 scrapinghub/splash
```

- go to `./ksiegi` and run:

```
$ scrapy crawl ksiegiW
```

In `./ksiegi/ksiegi/spiders/ksiegiW_spider.py` in line 105 you can change division code of land registers and in line 109 you can set range of number of land registers to scrape.

## Features

- scrape data of land registers from given range
- use lua script to interact with JavaScript page
- scraped data is saved to database
- all errors logs are saved in .csv file
