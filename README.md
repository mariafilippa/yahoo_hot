# yahoo_hot
A crawler and a web interface to query the most popular products on Yahoo Buy.

## Requirements
Python 3.6+

Pipenv for package management and development environment

    pip install pipenv
    
    */this will install all relevant packages
    */in yahoo_hot folder
    pipenv install
    
    */create sqlite tables
    pipenv run python manage.py migrate

Packages used in this project(as described by Pipfile):

    aiohttp
    uvloop
    aiohttp-socks
    django
    lxml
    
## Crawler
Asynchronous crawler written with asyncio, aiohttp and uvloop.

Coroutine is chosen as it performs best when it comes to network I/O.

Without argument, the default behaviour is to obtain a public proxy list and alternate between these to send requests.

    pipenv run python crawler/yahoo_crawler.py
    
In the event where proxy efficiency is less than ideal, proxy could be turned off using --no_proxy argument.

    pipenv run python crawler/yahoo_crawler.py --no_proxy
    
To truncate all tables and start fresh,

    pipenv run python crawler/yhaoo_crawler.py --fresh
    
## Finding best selling products
The best selling products are found by dissecting the yahoo query parameters. With the parameter for recent hot sales and each category id found, it is now possible to precisely obtain the best selling products of each category according to offical numbers.

    ?cid=10&cid_path=1_7&clv=2&p=%2A&qt=product&sort=-sales
    
## Interface
Django web interface at localhost:8000

    pipenv run python manage.py runserver
