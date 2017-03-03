# user python3 to run that script

import requests
import lxml.html

from concurrent import futures
from itertools import groupby
from operator import itemgetter


# links = [
#     'http://bit.ly/1FEOPPB',
#     'https://www.python.org/dev/peps/pep-0455/',
#     'http://bugs.python.org/issue18986',
#     'http://bit.ly/1Vm7OJ5',
#     'https://github.com/fluentpython/example-code',
#     'http://bugs.python.org/issue8743',
#     'http://hg.python.org/cpython/file/tip/Objects/dictobject.c',
# ]

def header(text):
    doc = lxml.html.fromstring(text)
    title = doc.find(".//title")
    if title is None:
        return 'No title here :('
    return title.text


def check_url(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        resp.raise_for_status()
    return resp.text


def process_url(entity):
    # try:
    text = check_url(entity[0])
    # except requests.exceptions.HTTPError as exc:
    #     raise
    # else:
    try:
        head = header(text)
    except ValueError:
        # print(entity)
        return Response(entity[0], success=False, error='Extracting header error!')
        # print(resp.initial_url, resp.error)
    else:
        return Response(entity[0], header=head)
        # entity.append(head)
    # return entity
    # entity.append(resp)


with open('tmp.txt', 'r') as _:
    data = [el.strip().split(':-:') for el in _.readlines()]

# [[url, chapter], [url, chapter] ..]


def build_markdown(links):
    with open('fluentpy3.md', 'w') as fluent:
        for k, g in groupby(links, itemgetter(1)):
            fluent.write('###{}\n'.format(k))
            for unit in g:
                fluent.write(' * {}\n'.format(unit[0]))
            fluent.write('\n')

# build_markdown(data)


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
                entity
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
                resp = Response(entity[0], success=False, error='Connection error')
                print(resp.initial_url, resp.error)
            except requests.exceptions.InvalidSchema:
                # print('InvalidSchema')
                resp = Response(entity[0], success=False, error='InvalidSchema')
                print(resp.initial_url, resp.error)
            else:
                # print(' '.join(res))
                resp = res
                # print(resp.initial_url, resp.header)
            entity.append(resp)
    print('REPORT###:')
    for el in entities:
        if not el[2].success:
            print(el[0], el[2].error)


prettify_urls(data)
# for el in data:
#     print(' '.join(el))
