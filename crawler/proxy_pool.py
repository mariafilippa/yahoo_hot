import time

import asyncio
import aiohttp
import uvloop
from lxml import html

url = 'https://free-proxy-list.net/anonymous-proxy.html'
test_sites = ['https://tw.yahoo.com/',
              'https://tw.buy.yahoo.com/',
              'https://tw.bid.yahoo.com/',
              'https://tw.mall.yahoo.com/']

async def get_proxies(session):
    response = await session.get(url)
    body = await response.text()
    tree = html.document_fromstring(body)
    proxies = tree.xpath("//table[@id='proxylisttable']/tbody/tr")

    proxy_list = []
    for proxy in proxies:
        ip = proxy.xpath('td[1]')[0].text
        port = proxy.xpath('td[2]')[0].text
        proxy_list.append('http://{}:{}'.format(ip, port))
    return proxy_list

async def test_proxy(session, proxy):
    timeout = aiohttp.ClientTimeout(total=5)
    tasks = [session.get(site, proxy=proxy, timeout=timeout) for site in test_sites]
    start = time.time()
    try:
        await asyncio.gather(*tasks)
        now = time.time()
        if now - start < 5:
            return proxy
    except Exception as err:
        # print(err)
        pass

async def get_best_proxies(session):
    proxy_list = await get_proxies(session)

    tasks = [test_proxy(session, proxy) for proxy in proxy_list]
    best_proxies = await asyncio.gather(*tasks)
    best_proxies = [proxy for proxy in best_proxies if proxy is not None]
    print('elite list:')
    print(best_proxies)
    return best_proxies

async def main():
    async with aiohttp.ClientSession() as session:
        await get_best_proxies(session)
        response = await session.get('http://icanhazip.com/', proxy=None)
        body = await response.text()
        tor_ip = body.strip()
        print(f'tor ip: {tor_ip}')


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
