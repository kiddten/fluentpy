import pickle

from itertools import groupby
from operator import itemgetter


links = pickle.load(open('links.b', 'rb'))

# print(len(links))
# for el in links:
#     print(el)

sources = set([el[1] for el in links])

with open('sources.txt', 'w') as _:
    for s in sorted(sources):
        _.write(s + '\n')
# pretty_chapters = [el for el in sources if 'chapter' in el.lower()]
# pretty_chapters_dict = {el.split(':')[0]: el for el in pretty_chapters}
# print(pretty_chapters_dict)
# for pc in pretty_chapters_dict:
#     print pc


with open('toc.txt', 'r') as toc:
    content = toc.readlines()


def intme(item):
    try:
        return int(item)
    except ValueError:
        return item

clear_content = []
for el in content:
    if '. .' in el:
        line = [intme(e.strip()) for e in el.strip().split('.') if e != ' ']
        if isinstance(line[0], int):
            clear_content.append(('Chapter {}: {}'.format(line[0], line[1]), line[2]))
        else:
            clear_content.append(tuple(line))
        # print(clear_content[-1])

# clear_content:
# ('the python data model', 3)
# ('an array of sequences', 19)


# def prettify(item):
#     try:
#         return pretty_chapters_dict[item.split(':')[0]]
#     except KeyError:
#         return item

# clear_content_dict = {el[1]: prettify(el[0]) for el in clear_content}

pretty_chapters = [el[0] for el in clear_content if 'chapter' in el[0].lower()]
pretty_chapters_dict = {el.split(':')[0]: el for el in pretty_chapters}

# for pc, v in pretty_chapters_dict.items():
#     print pc, v

clear_content_dict = {el[1]: el[0] for el in clear_content}
# print(clear_content_dict)
# for pc, v in clear_content_dict.items():
#     print pc, v


preface_pages = ['xv', 'xxi', 'xxiii']

pages = sorted(clear_content_dict.keys())


def find_chapter(page_num):
    for i, el in enumerate(pages):
        if el == page_num:
            return el
        elif el > page_num:
            return pages[i - 1]
    else:
        return el


def pre_append(el, suffix, put_to):
    if (el, suffix) not in put_to:
        put_to.append((el, suffix))

clear_list = []
for el in links:
    page = intme(el[1])
    if isinstance(page, int):
        # print(page)
        # clear_list.append((el[0], clear_content_dict[find_chapter(page)]))
        pre_append(el[0], clear_content_dict[find_chapter(page)], clear_list)
    elif 'chapter' in page.lower():
        # clear_list.append((el[0], pretty_chapters_dict[page.split(':')[0]]))
        pre_append(el[0], pretty_chapters_dict[page.split(':')[0]], clear_list)
    elif 'preface' in page.lower():
        # clear_list.append((el[0], 'Preface'))
        pre_append(el[0], 'Preface', clear_list)
    elif 'afterword' in page.lower():
        # clear_list.append((el[0], 'Afterword'))
        pre_append(el[0], 'Afterword', clear_list)
    elif 'jargon' in page.lower():
        # clear_list.append((el[0], 'Python jargon'))
        pre_append(el[0], 'Python jargon', clear_list)
    elif page in preface_pages:
        # clear_list.append((el[0], 'Preface'))
        pre_append(el[0], 'Preface', clear_list)
    else:
        clear_list.append((el[0], 'UNKNOWN ' + page))
    # if el[0] in [el[0] for el in clear_list]:
        # print('!!' * 17)
        # print(el[0])

print(len(clear_list), len(links))
# for el in clear_list:
#     print(el)s
print len(set([el[0] for el in clear_list]))

# for el in clear_list:
# print el

import requests
import lxml.html


def header(link):
    try:
        r = requests.get(link)
        doc = lxml.html.fromstring(r.text)
        header = doc.find(".//title").text.encode('utf-8')
        return header
    except:
        return


def build_markdown(links):
    groups = []
    with open('fluentpy.md', 'w') as fluent:
        for k, g in groupby(links, itemgetter(1)):
            fluent.write('###{}\n'.format(k))
            for unit in g:
                fluent.write(' * {}\n'.format(unit[0]))
                # fluent.write(' *[{0}]({1})\n'.format(header(unit[0]), unit[0]))
            fluent.write('\n')
            # groups.append(list(g))
    # print(len(groups))

build_markdown(clear_list)
