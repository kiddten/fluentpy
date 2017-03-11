# user python3 to run that script

import requests
import lxml.html

from concurrent import futures
from itertools import groupby
from operator import itemgetter


def header(text, pdf=False):
    if pdf:
        return 'PDF'
    doc = lxml.html.fromstring(text)
    # print(text)
    with open('test_title', 'w') as _:
        _.write(text.decode('utf-8'))
    title = doc.find(".//title")
    if title is None:
        return 'No title here :('
    return title.text.strip()


def check_url(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        resp.raise_for_status()
    if resp.history:
        return resp.content, resp.url
    return resp.content, None


def process_url(url):
    text, resolved_url = check_url(url)
    try:
        head = header(text, pdf='pdf' in url or 'pdf' in str(resolved_url))
    except ValueError:
        return Response(
            url,
            success=False,
            error='Extracting header error!',
            resolved_url=resolved_url
        )
    else:
        return Response(url, header=head, resolved_url=resolved_url)


with open('tmp.txt', 'r') as _:
    data = [el.strip().split(':-:') for el in _.readlines()]

# [[url, chapter], [url, chapter] ..]


class Response():

    def __init__(self, initial_url, success=True, header=None, error=None, resolved_url=None):
        self.initial_url = initial_url
        self.success = success
        self.header = header
        self.error = error
        self.resolved_url = resolved_url


def decode(entities, key):
    for entity in entities:
        try:
            value = ''.join(entity)
        except TypeError:
            continue
        if key == value:
            return entity


def prettify_urls(entities):
    with futures.ThreadPoolExecutor(max_workers=50) as executor:
        todo = {}
        for entity in entities:
            future = executor.submit(
                process_url,
                entity[0]
            )
            # todo.append(future)
            todo[future] = ''.join(entity)
        # print(todo)
        done_iter = futures.as_completed(todo)
        for future in done_iter:
            entity = decode(entities, todo[future])
            # print(entity)
            try:
                res = future.result()
            except requests.exceptions.HTTPError as exc:  # <15>
                error_msg = 'HTTP {res.status_code} - {res.reason}'
                error_msg = error_msg.format(res=exc.response)
                # print(error_msg)
                resp = Response(entity[0], success=False, error=error_msg)
                print(resp.initial_url, resp.error)
            except requests.exceptions.ConnectionError as exc:
                # print('Connection error')
                resp = Response(entity[0], success=False,
                                error='Connection error')
                print(resp.initial_url, resp.error)
            except requests.exceptions.InvalidSchema:
                # print('InvalidSchema')
                resp = Response(entity[0], success=False,
                                error='InvalidSchema')
                print(resp.initial_url, resp.error)
            else:
                # print(' '.join(res))
                resp = res
                if resp.resolved_url:
                    print(
                        'Redirected from {resp.initial_url} to {resp.resolved_url}'.format(resp=resp))
                # print(resp.initial_url, resp.header)
            entity.append(resp)
    # print('REPORT###:')
    # for el in entities:
    #     if not el[2].success:
    #         print(el[0], el[2].error)


def build_markdown(links):
    with open('fluentpy3.md', 'w') as fluent:
        for k, g in groupby(links, itemgetter(1)):
            fluent.write('###{}\n'.format(k))
            for unit in g:
                fluent.write(' * {}\n'.format(unit[0]))
            fluent.write('\n')


def build_markdown_extended(links):
    fluent = open('fluentpy3.md', 'w')
    fluent_errors = open('fluentpy3_errors.md', 'w')
    for k, g in groupby(links, itemgetter(1)):
        fluent.write('###{}\n'.format(k))
        fluent_errors.write('###{}\n'.format(k))
        for unit in g:
            if not unit[2].error:
                url = unit[2].resolved_url if unit[2].resolved_url else unit[0]
                fluent.write(' * [{}]({})\n'.format(unit[2].header, url))
            else:
                fluent_errors.write(' * {}\n'.format(unit[0]))
        fluent.write('\n')
        fluent_errors.write('\n')
    fluent.close()
    fluent_errors.close()

prettify_urls(data)
build_markdown_extended(data)
