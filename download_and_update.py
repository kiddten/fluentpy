import asyncio
from itertools import groupby
from operator import itemgetter
from random import randint
from urllib.parse import urlparse

import aiohttp
import lxml.html
from loguru import logger


class Response:

    def __init__(self, initial_url, resolved_url, body):
        self.initial_url = initial_url
        self.resolved_url = resolved_url
        self.header = self.get_header(body)

    def get_header(self, body):
        if 'pdf' in self.resolved_url.lower():
            return 'PDF'
        doc = lxml.html.fromstring(body)
        title = doc.find(".//title")
        if title is None:
            return 'No title here :('
        title = title.text.strip()
        title = title.replace('\n', ' ')
        return title

    def __str__(self):
        return f'{self.initial_url} - {self.resolved_url} - {self.header}'


async def fetch(session, url, sem=None, offset=False):
    sem = sem or asyncio.Semaphore(20)
    if offset:
        logger.debug('Sleeping a little due to same domain')
        await asyncio.sleep(randint(1, 7))
    async with sem:
        logger.debug(f'Fetching {url} ..')
        try:
            response = await session.get(url, timeout=20)
        except Exception:
            logger.exception(f'Error with {url}')
            raise
        txt = await response.text()
        logger.debug(f'Done with {url}')
        return Response(url, str(response.url), txt)


async def fetch_all(session, urls):
    domains = set()
    sem = asyncio.Semaphore(100)
    tasks = []
    for url in urls:
        parsed_url = urlparse(url)
        tasks.append(fetch(session, url, sem, parsed_url.netloc in domains))
        domains.add(parsed_url.netloc)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for index, url in enumerate(urls):
        status = results[index] if isinstance(results[index], Exception) else 'OK'
        print(f'{url}: {status} >> {results[index]}')
    return results


@logger.catch()
def build_markdown_extended(links):
    fluent = open('fluentpy3.md', 'w')
    fluent_errors = open('fluentpy3_errors.md', 'w')
    fluent.write('## Table of Contents\n')
    for k, _ in groupby(links, itemgetter(1)):
        kk = k.lower().replace(' ', '-').replace(':', '')
        fluent.write(f'- [{k}](#{kk})\n')
    for k, g in groupby(links, itemgetter(1)):
        fluent.write(f'### {k}\n')
        fluent_errors.write(f'### {k}\n')
        for unit in g:
            if not unit[2]:
                fluent_errors.write(f' * {unit[0]}\n')
            else:
                fluent.write(f' * [{unit[2].header}]({unit[2].resolved_url})\n')
        fluent.write('\n')
    fluent.close()


async def main():
    with open('links_toc.txt', 'r') as _:
        data = [el.strip().split(':-:') for el in _.readlines()]
    data = [item for item in data if 'unknown' not in item[1].lower()]
    async with aiohttp.ClientSession() as session:
        results = await fetch_all(session, [i[0] for i in data])
    session = aiohttp.ClientSession()
    logger.debug('Going to retry failed urls..')
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            url = data[i][0]
            logger.debug(f'Trying to get {url} again and slowly')
            try:
                new_result = await fetch(session, url)
            except Exception:
                logger.exception(f'Request for {url} failed again')
            else:
                results[i] = new_result
            await asyncio.sleep(1)
    await session.close()
    for item, result in zip(data, results):
        item.append(result if not isinstance(result, Exception) else None)
    build_markdown_extended(data)


if __name__ == '__main__':
    asyncio.run(main())
