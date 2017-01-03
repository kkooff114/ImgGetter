from pathlib import Path
from urllib import error
from urllib import request
import time
import json

from bs4 import BeautifulSoup

base_url = "http://www.dzdwl.com"
url = "http://www.dzdwl.com/dsmv/index.html"


def _create_dir(name):
    """
    根据传入的目录名创建一个目录，这里用到了 python3.5 引入的 pathlib 库。
    """
    directory = Path(name)
    if not directory.exists():
        directory.mkdir(parents=True)
    return directory


# 从home页面获取列表的下属页面的链接
def _get_homepage_list_href(home_url):
    try:
        with request.urlopen(home_url) as res:
            soup = BeautifulSoup(res.read().decode(errors='ignore'), 'html.parser')  # 解析html
            tag = soup.find_all('a', class_='preview')  # 获取列表页面下属详情页面的超链接

            hrefs = []
            for child in tag:
                hrefs.append(base_url + child['href'])  # 获取img的链接

            return hrefs

    except error.HTTPError as err:
        print("error:{url} {code} {msg}".format(url=home_url, code=err.code, msg=err.msg))
        return []


# 从一个详情页获取图片url
def _get_img_url_from_page(detail_url):
    try:
        with request.urlopen(detail_url) as res:
            soup = BeautifulSoup(res.read().decode(errors='ignore'), 'html.parser')  # 解析html
            tcontent = soup.find('div', class_='tcontent')

            imgs = []
            if tcontent:
                imgs = tcontent.find_all('img')

            img_urls = []
            for img in imgs:

                # 如果有'lazysrc'属性, 优先加载
                if 'lazysrc' in img.attrs:
                    img_urls.append(img['lazysrc'])
                elif 'src' in img.attrs:
                    img_urls.append(img['src'])

            return img_urls

    except error.HTTPError as err:
        print("error:{url} {code} {msg}".format(url=detail_url, code=err.code, msg=err.msg))
        return []


def _download_img(urls, dir):
    for url in urls:
        photo_name = url.rsplit('/', 1)[-1]

        save_path = dir / photo_name
        print('download 图片 {url}'.format(url=url))

        try:
            req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

            with request.urlopen(req) as res, save_path.open('wb') as f:
                f.write(res.read())
                print('已下载图片：{dir_name}/{photo_name}，请求的 URL 为：{url}'
                      .format(dir_name=dir, photo_name=photo_name, url=url))

        except error.HTTPError as err:
            print("error {code} {msg}".format(code=err.code, msg=err.msg))
            continue


# 获得所有列表页面
def get_home_pages():
    home_page_url_check_list = []

    # 文本需已经存在, 并且里面有'[]'
    with open('/Users/LJW/Pictures/python/gif/url_check_list.txt', 'r') as f:
        home_page_url_check_list = json.load(f)

        # 如果文本为空, 则初始化;
        if len(home_page_url_check_list) == 0:
            home_pages_url = [url]
            for i in range(100):
                _home_url = "http://www.dzdwl.com/dsmv/index_{index}.html".format(index=i)
                home_pages_url.append(_home_url)

                obj = {'url': _home_url, 'checked': 'no', 'hasDownload': 'no'}  # 是否重复, 是否已经下载
                home_page_url_check_list.append(obj)

            with open('/Users/LJW/Pictures/python/gif/url_check_list.txt', 'w') as f:
                json.dump(home_page_url_check_list, f)

                # for url_checked in home_page_url_check_list:
                #     if url_checked['repeat'] == 'no' and url_checked['hasDownload'] == 'no':
                #         _url.append(url_checked['url'])

    return home_page_url_check_list


# 去重
def distinct_home_page(home_pages):
    print("待去重url数量: {url_count}".format(url_count=len(home_pages)))

    with open('/Users/LJW/Pictures/python/gif/url_check_status.txt', 'r') as f:
        url_check_status = json.load(f)
        now1 = int(time.time())

        for home in home_pages:

            home_url = home['url']

            if home['checked'] == 'yes':
                print("{url} 已经检查过了, 忽略home_page...".format(url=home_url))
                continue;

            print("start check home page {url}".format(url=home_url))
            detail_pages_urls = _get_homepage_list_href(home_url)

            for detail in detail_pages_urls:
                img_urls = _get_img_url_from_page(detail)

                print("start check detail page {url} ...".format(url=detail))
                if len(img_urls) > 0 and url_check_status.get(img_urls[0]) is None:
                    print("start check detail page {url} 不存在".format(url=detail))
                    url_check_status[img_urls[0]] = detail

                # 保存check status
                with open('/Users/LJW/Pictures/python/gif/url_check_status.txt', 'wt') as f:  # 使用wt, 覆盖掉原来的文本
                    json.dump(url_check_status, f)

            # 保存check 到 url list
            home['checked'] = 'yes'
            with open('/Users/LJW/Pictures/python/gif/url_check_list.txt', 'wt') as f:
                json.dump(home_pages, f)

            print("end check home page {url}".format(url=home_url))

        now2 = int(time.time())
        print("去重花费时间为 {time}".format(time=(now2 - now1)))


# 1. 生成url文本
def generat_url_text():
    home_page = get_home_pages()  # 待下载的home_page
    print("长度{count}".format(count=len(home_page)))

    # 去重home_page
    distinct_home_page(home_page)


# 2. 转换待下载的文本
def url_check_status():
    with open('/Users/LJW/Pictures/python/gif/url_check_status.txt', 'r') as f:
        url_check_status = json.load(f)

        new_file = {}
        for key in url_check_status:
            new_file[url_check_status[key]] = {'hasDownload': 'no'}

    with open('/Users/LJW/Pictures/python/gif/url_download_list.txt', 'wt') as f:  # 使用wt, 覆盖掉原来的文本
        json.dump(new_file, f)


def startDownload():
    root_dir = _create_dir('/Users/LJW/Pictures/python/gif')  # 保存图片的根目录

    with open('/Users/LJW/Pictures/python/gif/url_download_list.txt', 'r') as f:
        download_list = json.load(f)

        for download_url in download_list:

            if download_list[download_url]['hasDownload'] == 'yes':
                print("{url} 已下载, 忽略...".format(url=download_url))
                continue;

            print("{url} 开始...".format(url=download_url))
            # 开始下载一个页面的所以图片
            img_urls = _get_img_url_from_page(download_url)

            d = download_url.replace('/', '_');
            download_dir = _create_dir(root_dir / d)
            _download_img(img_urls, dir=download_dir)

            # 保存下载状态
            download_list[download_url]['hasDownload'] = 'yes'
            with open('/Users/LJW/Pictures/python/gif/url_download_list.txt', 'wt') as f:  # 使用wt, 覆盖掉原来的文本
                json.dump(download_list, f)

            print("{url} 结束...".format(url=download_url))


if __name__ == '__main__':
    # generat_url_text()

    # url_check_status()

    startDownload()



    # detail_pages_list = _get_homepage_list_href(url)
    #
    # dir_name = 0
    # for detail in detail_pages_list:
    #     print('start home page>>>   {detail}'.format(detail=detail))
    #     imgUrls = _get_img_url_from_page(detail)
    #
    #     download_dir = _create_dir(root_dir / str(dir_name))
    #
    #     _download_img(imgUrls, dir=download_dir)
    #
    #     dir_name += 1
