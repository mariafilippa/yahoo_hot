import argparse
import re
import random
import sqlite3

import asyncio
import aiohttp
from aiohttp.client_exceptions import ClientOSError, ServerDisconnectedError
import uvloop
from aiohttp_socks import SocksConnector
from lxml import html

from proxy_pool import get_best_proxies


regex_id = re.compile('[0-9]+')
regex_price = re.compile('[0-9,]+')
headers = {'Host': 'tw.search.buy.yahoo.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'}


async def get_categories(conn, zone, zone_id):
    categories = zone.xpath('ul/li/a')
    for category in categories:
        name = category.text
        cid = regex_id.search(category.attrib['href'])[0]
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO web_interface_category (id, name, cid, done, zone_id) VALUES ((SELECT id FROM web_interface_category WHERE name = ?), ?, ?, ?, ?)',
                  (name, name, cid, 0, zone_id))
    print(zone_id, ' done!')

async def get_zones(session, conn, proxies):
    proxy = random.choice(proxies) if proxies else None
    response = await session.get('https://tw.buy.yahoo.com/help/helper.asp?p=sitemap', proxy=proxy)
    body = await response.text()
    tree = html.document_fromstring(body)
    zones = tree.xpath("//div[@id='cl-sitemap']/div[@class='module yui3-g'][1]/div/ul/li")
    tasks = []
    for zone in zones:
        name = zone.xpath('h3/a')[0].text
        cid = regex_id.search(zone.xpath('h3/a')[0].attrib['href'])[0]
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO web_interface_category (id, name, cid, done) VALUES ((SELECT id FROM web_interface_category WHERE name = ?), ?, ?, ?)',
                  (name, name, cid, 0))
        zone_id = c.lastrowid
        print(zone_id, ': ', name)
        tasks.append(get_categories(conn, zone, zone_id))
    await asyncio.gather(*tasks)
    conn.commit()

async def get_products(session, conn, url, cid, proxies):
    proxy = random.choice(proxies) if proxies else None
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        response = await session.get(url, headers=headers, proxy=proxy, timeout=timeout)
        body = await response.text()
    except:
        return
    tree = html.document_fromstring(body)
    products = tree.xpath("//ul[@class='gridList']/li/a")
    c = conn.cursor()
    for product in products:
        url = product.attrib['href']
        name = product.xpath("span/span[contains(@class, 'title')]")[0].text
        try:
            price = regex_price.search(product.xpath("span/span[contains(@class, 'price')]")[0].text)[0]
        except:
            continue
        # print(name, price, url, cid)
        c.execute('INSERT OR REPLACE INTO web_interface_product (id, name, price, url, category_id) VALUES ((SELECT id FROM web_interface_product WHERE name = ? and category_id = ?), ?, ?, ?, ?)',
                  (name, cid, name, price, url, cid))
    c.execute('UPDATE web_interface_category SET done = 1 WHERE id = ?', (cid,))
    conn.commit()
    print(cid, ' sub_cat done! Proxy: ', proxy)

async def get_urls(session, conn, proxies):
    url = 'https://tw.search.buy.yahoo.com/search/shopping/product?'
    query = 'cid={0}&clv={1}&p=%2A&qt=product&sort=-sales&cid_path={2}'
    c = conn.cursor()
    c.execute('SELECT id, cid FROM web_interface_category WHERE zone_id IS NULL')
    for zid in c.fetchall():
        tasks = []
        c2 = conn.cursor()
        c2.execute('SELECT id FROM web_interface_category WHERE id = ? AND done = 0', (str(zid[0]),))
        if c2.fetchone():
            tasks.append(get_products(session, conn, url+query.format(zid[1], 1, ''), zid[0], proxies))

        c2.execute('SELECT id, cid FROM web_interface_category WHERE zone_id = ? AND done = 0', (str(zid[0]),))
        for cid in c2.fetchall():
            tasks.append(get_products(session, conn, url+query.format(cid[1], 2, '1_{}'.format(zid[1])), cid[0], proxies))

        await asyncio.gather(*tasks)
        print(zid[1], ' zone done!')

async def main(no_proxy=False):
    while True:
        try:
            with sqlite3.connect('db.sqlite3') as conn:
                # connector = SocksConnector.from_url('socks5://127.0.0.1:9050')
                # async with aiohttp.ClientSession(connector=connector) as session:
                    # response = await session.get('http://icanhazip.com')
                async with aiohttp.ClientSession() as session:
                    if no_proxy:
                        proxies = None
                    else:
                        proxies = await get_best_proxies(session)
                    await get_zones(session, conn, proxies)
                    await get_urls(session, conn, proxies)
                    # await get_products(session, conn, 'abc', 1)
        except ClientOSError as err:
            print(err)
            asyncio.sleep(2)
        except ServerDisconnectedError as err:
            print(err)
            asyncio.sleep(2)
        else:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--fresh', action='store_true')
    parser.add_argument('--no_proxy', action='store_true')
    args = parser.parse_args()
    if args.fresh:
        with sqlite3.connect('db.sqlite3') as conn:
            conn.execute('DELETE FROM web_interface_category')
            conn.execute('DELETE FROM web_interface_product')

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(no_proxy=args.no_proxy))
    loop.close()
