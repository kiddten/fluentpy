import asyncio
from itertools import groupby
from operator import itemgetter

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


async def fetch(session, url, sem):
    async with sem:
        logger.debug(f'Fetching {url} ..')
        try:
            response = await session.get(url)
        except Exception:
            logger.exception(f'Error with {url}')
            raise
        txt = await response.text()
        logger.debug(f'Done with {url} ..')
        return Response(url, str(response.url), txt)


async def fetch_all(session, urls):
    sem = asyncio.Semaphore(100)
    results = await asyncio.gather(*[fetch(session, url, sem) for url in urls], return_exceptions=True)
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
    for item, result in zip(data, results):
        item.append(result if not isinstance(result, Exception) else None)
    build_markdown_extended(data)


if __name__ == '__main__':
    asyncio.run(main())
