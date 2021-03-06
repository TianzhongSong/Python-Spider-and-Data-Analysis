# -*- coding: utf-8 -*-
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from time import sleep
import re
import pymongo


def get_one_page(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except RequestException:
        return None


def parse_one_page(html):
    soup = BeautifulSoup(html, 'lxml')
    items = soup.select('.item')
    for item in items:
        yield item.a['href']


def parse_one_drama(html, id):
    drama = BeautifulSoup(html, 'lxml')
    name = drama.find(property="v:itemreviewed").string
    content = drama.find(class_="subject clearfix").find(id="info")
    try:
        directors = content.span.a.string
        for node in content.span.a.next_siblings:
            directors += node.string
    except AttributeError:
        directors = 'unkonw'
    try:
        count = 0
        screenWriter = ''
        for node in content.span.next_siblings:
            if count == 2:
                screenWriter = node.a.string
                for sub_node in node.a.next_siblings:
                    screenWriter += sub_node.string
            count += 1
    except AttributeError:
        screenWriter = 'unkonw'

    try:
        actors = content.find(class_="actor").find(class_="attrs").a.string
        for node in content.find(class_="actor").find(class_="attrs").a.next_siblings:
            actors += node.string
    except AttributeError:
        actors = 'unkonw'

    try:
        drama_types = content.find_all(property="v:genre")
        drama_type = drama_types[0].string
        if len(drama_types) > 1:
            for i in range(1, len(drama_types)):
                drama_type = drama_type + '/' + drama_types[i].string
    except AttributeError:
        drama_type = 'unkonw'

    try:
        pattern = re.compile('<div\sclass="article".*?"v:genre".*?<br/>.*?</span>' +
                             '(.*?)<br/>.*?</span>(.*?)<br/>.*?"v:average">(.*?)<.*?' +
                             '"v:votes">(\d+)<', re.S)
        items = re.findall(pattern, html)
        region = items[0][0]
        language = items[0][1]
        score = items[0][2]
        voted = items[0][3]
    except AttributeError:
        region = 'unkonw'
        language = 'unkonw'
        score = 'unkonw'
        voted = 'unkonw'

    id += 1
    yield {
        '_id': id,
        u'剧名': name,
        u'导演': directors,
        u'编剧': screenWriter,
        u'主演': actors,
        u'类型': drama_type,
        u'地区': region,
        u'语言': language,
        u'评分': score,
        u'总评分人数': voted
    }, id


if __name__ == "__main__":
    client = pymongo.MongoClient('mongodb://localhost:27017')
    db_name = 'douban_meiju'
    db = client[db_name]
    collection_set01 = db['set01']
    prefix = u'https://movie.douban.com/tag/美剧?start='
    index = 0
    for i in range(144):
        print(i)
        url = prefix + str(i*20) + '&type=T'
        html = get_one_page(url)
        for page in parse_one_page(html):
            drama_html = get_one_page(page)
            sleep(1)
            for item, index in parse_one_drama(drama_html, index):
                collection_set01.save(item)
