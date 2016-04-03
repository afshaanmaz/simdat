#!/usr/bin/env python
# -*- coding: utf8 -*-

'''
This is a modified version of
https://github.com/hardikvasa/google-images-download

Before starting, prepare the download_args.json with the
keywords you want to search for. For example:
{
    "search_for": {
        "Australia": ["high resolution", "paintings"],
        "Pyramid of Giza": ["at night", "from top"]
    }
}


Do $python image_downloader.py -t without downloading, otherwise, images
will be downloaded to $PWD/images automaticall.
'''

import time
import os
import sys
import json
import urllib
import argparse


def parse_json(fname):
    """Parse the input profile

    @param fname: input profile path
    @return data: a dictionary with user-defined data for training

    """
    with open(fname) as data_file:
        data = json.load(data_file)
    return data

data = parse_json('download_args.json')
search_for = data['search_for']


def check_dir(dirpath):
    """Check if a directory exists, create one elsewise."""
    if not os.path.exists(dirpath):
        print("Creating %s" % dirpath)
        os.makedirs(dirpath)


def download_page(url):
    """Get contents from the download page"""

    url = url.encode('utf8')
    version = (3, 0)
    cur_version = sys.version_info
    user_agent = ''.join(['Mozilla/5.0 (X11; Linux i686) ',
                          'AppleWebKit/537.17(KHTML, like Gecko) ',
                          'Chrome/24.0.1312.27 Safari/537.17'])
    if 'useragent' in data:
        user_agent = data['useragent']

    # Python 3.0 or above
    if cur_version >= version:
        import urllib.request
        try:
            headers = {}
            headers['User-Agent'] = user_agent
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req)
            respData = str(resp.read())
            return respData
        except Exception as e:
            print(str(e))

    # Python is 2.x
    else:
        import urllib2
        try:
            headers = {}
            headers['User-Agent'] = user_agent
            req = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(req)
            page = response.read()
            return page
        except:
            return"Page Not found"


def _images_get_next_item(s):
    """Finding 'Next Image' from the given raw page"""

    start_line = s.find('rg_di')
    # If no links are found then give an error!
    if start_line == -1:
        end_quote = 0
        link = "no_links"
        return link, end_quote
    else:
        start_line = s.find('"class="rg_di"')
        start_content = s.find('imgurl=', start_line+1)
        end_content = s.find('&amp;', start_content+1)
        content_raw = str(s[start_content+7:end_content])
        return content_raw, end_content


def _images_get_all_items(page):
    """ Getting all links with the help of '_images_get_next_image'"""

    items = []
    while True:
        item, end_content = _images_get_next_item(page)
        if item == "no_links":
            break
        else:
            items.append(item)
            page = page[end_content:]
    return items


def main():
    parser = argparse.ArgumentParser(
        description="Simple tool to download images via Google Search."
        )
    parser.add_argument(
        "-t", "--test", action='store_true'
        )
    parser.add_argument(
        "-a", "--all", action='store_true',
        help="Seatch for all images instead of those in 24 hours."
        )
    args = parser.parse_args()

    t0 = time.time()
    results = {}
    testfile = urllib.URLopener()

    url_base = ''.join(['https://www.google.com/search?q=',
                        'REPLACEME',
                        '&espv=2&biw=1366&bih=667&',
                        'site=webhp&source=lnms&tbm=isch&sa=X',
                        '&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'])
    if not args.all:
        url_base = url_base + '&tbs=itp:photo,qdr:w'
    for search_keyword in search_for:
        results[search_keyword] = []
        print (" Item name = ", search_keyword)
        search = search_keyword.replace(' ', '%20')
        if len(search_for[search_keyword]) < 1:
            url = url_base.replace('REPLACEME', search)
            raw_html = (download_page(url))
            results[search_keyword] = _images_get_all_items(raw_html)
            continue
        for j in range(0, len(search_for[search_keyword])):
            pure_keyword = '%20' + search_for[search_keyword][j]
            pure_keyword = pure_keyword.replace(' ', '%20')
            url = url_base.replace('REPLACEME', search + pure_keyword)
            raw_html = (download_page(url))
            results[search_keyword] += _images_get_all_items(raw_html)

    if not args.test:
        for search_keyword in results:
            path = './images/' + search_keyword
            check_dir(path)
            os.chdir(path)
            items = results[search_keyword]
            for i in range(0, len(items)):
                url = items[i].encode('utf8')
                try:
                    print('  Downloading: ' + str(i+1) + '/' + str(len(items)))
                    filename = os.path.basename(url)
                    testfile.retrieve(url, filename)
                except IOError:
                    print(' Skipping ' + url)
                    pass
                except IndexError:
                    print(' Skipping ' + url)
                    pass
            os.chdir('../../')
    else:
        import json
        with open('./outputs.txt', 'w')as fp:
            json.dump(results, fp)

if __name__ == '__main__':
    main()
