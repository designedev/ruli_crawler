# coding=utf-8:
import requests
from time import time
import urllib.request
from urllib.parse import urlparse
import asyncio
from bs4 import BeautifulSoup
import datetime
import re
import os
import random
import string
import json



FILE_LOCATED_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGES_VAULT_DIRECTORY_NAME = FILE_LOCATED_PATH + "/raw_vault"
IMAGES_DIRECTORY_NAME = FILE_LOCATED_PATH + "/images"
LOGS_DIRECTORY_NAME = FILE_LOCATED_PATH + "/logs"
CONFIG_DIRECTORY_NAME = FILE_LOCATED_PATH + "/config"
DCINSIDE_REFERER_URL = "https://gall.dcinside.com"


required_dirs = [IMAGES_VAULT_DIRECTORY_NAME, IMAGES_DIRECTORY_NAME, LOGS_DIRECTORY_NAME, CONFIG_DIRECTORY_NAME]

def init_dirs():
    for dir in required_dirs:
        make_dir(dir)

def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def make_random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))

def gex_max_article_id():
    try:
        id_file_r = open(CONFIG_DIRECTORY_NAME+"/max_id.txt", "r")
        max_id = id_file_r.read()
        id_file_r.close()
        return max_id
    except FileNotFoundError:
        print("id information file does not exist. set to default value(0)")
        return 0


def set_max_article_id(max_article_id):
    id_file_w = open(CONFIG_DIRECTORY_NAME+"/max_id.txt", "w+")
    id_file_w.write(str(max_article_id))
    id_file_w.close()

def get_html(url):
    html = ""
    resp = requests.get(url)
    if resp.status_code == 200:
        html = resp.text
    return html

def get_html_with_session(url):
    parsed = urlparse(url)
    domain = parsed.scheme + "://" + parsed.netloc
    print("domain : {}".format(domain))
    with requests.Session() as session:
        session.headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"}
        session.get(domain)
        response = session.get(url)
    if response.status_code == 200:
        html = response.text
    return html


def get_image_urls(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    content = soup.find("div", {"class" : "gallview_contents"})
    images = content.find_all("img")
    img_infos = list(map(lambda a: a["src"], images))
    return img_infos

def prepare_urls():
    # 각종 디렉토리 세팅.
    init_dirs()
    # 이전 작업에서 저장된 마지막 게시물 ID를 불러옴.
    max_id = gex_max_article_id()
    print('CURRENT MAX ID : ', max_id)

    urls = []
    URL = "https://gall.dcinside.com/board/lists/?id=iu_new"
    html = get_html_with_session(URL)
    soup = BeautifulSoup(html, 'html.parser')

    list_table = soup.find("table", {"class" : "gall_list"}) #아티클 테이블
    table_body = list_table.find("tbody")

    articles = table_body.find_all("tr", {"class" : "ub-content", "data-type" : "icon_pic"})

    id_tds = list_table.find_all("td", {"class" : "id"}) #id 정보 리스트
    article_ids = list(map(lambda a: int(a["data-no"]), articles))
    max_article_id = max(article_ids)

    # 이번 조회에서 얻은 마지막 게시물 ID를 저장함.
    valid_article_ids = list(filter(lambda x:x>int(max_id), article_ids))
    set_max_article_id(max_article_id)

    ARTICLE_URL_FORMAT = "https://gall.dcinside.com/board/view/?id=iu_new&no={}"
    for id in valid_article_ids:
        urls.append(ARTICLE_URL_FORMAT.format(id))
    return urls


def download_img(url):
    try:
        random_name = make_random_string(20)
        file_name = url.split("/").pop()
        if (len(file_name.split(".")) < 2 or (file_name.split(".")[1]).upper().startswith("PHP")): #확장자가 없거나 php로 불러오는 이미지는 랜덤 이름으로 저장.
            full_filename =  random_name + ".jpg"
        else:
            full_filename =  random_name +"." + file_name.split(".").pop()

        save_path = IMAGES_DIRECTORY_NAME + "/" + datetime.datetime.now().strftime("%Y-%m-%d")

        try:
            make_dir(save_path)
        except Exception as ex:
            print("directory creation error(maybe it already exists.), continue download.. ", ex)
            
        save_fullpath = save_path + "/" + full_filename

        opener = urllib.request.build_opener()
        opener.addheaders = [('Referer', DCINSIDE_REFERER_URL)]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url,
         save_fullpath)
        size = int(os.path.getsize(save_fullpath)/1024)
        return (save_fullpath, size)
    except Exception as ex:
        print(url + " Failed to download image..", ex)
        return 0

async def fetch(url):
    response = await loop.run_in_executor(None, get_html_with_session, url)    # run_in_executor 사용
    img_srcs = await loop.run_in_executor(None, get_image_urls, response)   # run in executor 사용
    return img_srcs

async def find_main(urls):
    futures = [asyncio.ensure_future(fetch(url)) for url in urls]   # 태스크(퓨처) 객체를 리스트로 만듦
    result = await asyncio.gather(*futures)                # 결과를 한꺼번에 가져옴
    return result

async def download_fetch(url_info):
    response = await loop.run_in_executor(None, download_img, url_info)    # run_in_executor 사용
    return response

async def download_main(url_infos):
    futures = [asyncio.ensure_future(download_fetch(url_info)) for url_info in url_infos]   # 태스크(퓨처) 객체를 리스트로 만듦
    result = await asyncio.gather(*futures)                # 결과를 한꺼번에 가져옴
    return result

try:

    find_begin = time()
    urls = prepare_urls()
    loop = asyncio.get_event_loop() # 이벤트 루프를 얻음
    image_urls = loop.run_until_complete(find_main(urls))   # main이 끝날 때까지 기다림
    find_end = time()
    download_begin = time()

    found_image_count = 0
    if (len(image_urls)) > 0 :
        flatten_image_url_infos = [item for sublist in image_urls for item in sublist]
        found_image_count = len(flatten_image_url_infos)
        print("{} IMAGE FOUND..".format(found_image_count))
        print(flatten_image_url_infos)
        downloaded_file_infos = loop.run_until_complete(download_main(flatten_image_url_infos))  # main이 끝날 때까지 기다림
        loop.close()
    else:
        print('no image.')
        loop.close()

    download_end = time()

    if (found_image_count > 0) :
        print('==============================================================')
        print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        print(' %d images found.'%(found_image_count))
        print('Searching time : {0:.3f} second'.format(find_end - find_begin))
        print('Download time : {0:.3f} second'.format(download_end - download_begin))
        print('==============================================================')

finally:
    print("Completed")