#!/usr/bin/python
import http.client
import os
import re
import sys
import datetime
import time
import urllib.request
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup


class Crawler:
    def __init__(self, website, c_depth, c_pause, out_path, logs, verbose):
        self.website = website
        self.c_depth = c_depth
        self.c_pause = c_pause
        self.out_path = out_path
        self.logs = logs
        self.verbose = verbose

    def excludes(self, link):
        now = datetime.datetime.now().strftime("%y%m%d")
        if link is None:
            return True
        elif '#' in link:
            return True
        elif link.startswith('http') and not link.startswith(self.website):
            file_path = self.out_path + '/' + now + '_ext-links.txt'
            with open(file_path, 'a+', encoding='UTF-8') as lst_file:
                lst_file.write(str(link) + '\n')
            return True
        elif link.startswith('tel:'):
            file_path = self.out_path + '/' + now + '_telephones.txt'
            with open(file_path, 'a+', encoding='UTF-8') as lst_file:
                lst_file.write(str(link) + '\n')
            return True
        elif link.startswith('mailto:'):
            file_path = self.out_path + '/' + now + '_mails.txt'
            with open(file_path, 'a+', encoding='UTF-8') as lst_file:
                lst_file.write(str(link) + '\n')
            return True
        elif re.search('^.*\\.(pdf|jpg|jpeg|png|gif|doc)$', link, re.IGNORECASE):
            file_path = self.out_path + '/' + now + '_files.txt'
            with open(file_path, 'a+', encoding='UTF-8') as lst_file:
                lst_file.write(str(link) + '\n')
            return True

    def canonical(self, link):
        if link.startswith(self.website):
            return link
        elif link.startswith('/'):
            if self.website[-1] == '/':
                final_link = self.website[:-1] + link
            else:
                final_link = self.website + link
            return final_link
        elif re.search('^.*\\.(html|htm|aspx|php|doc|css|js|less)$', link,
                       re.IGNORECASE):
            if self.website[-1] == '/':
                final_link = self.website + link
            else:
                final_link = self.website + "/" + link
            return final_link

    def write_log(self, log):
        log_path = self.out_path + '/crawler.log'
        now = datetime.datetime.now()
        if self.logs is True:
            open(log_path, 'a+')
            if self.logs is True and os.access(log_path, os.W_OK) is False:
                print(f"## Unable to write to {self.out_path}/log.txt - Exiting")
                sys.exit(2)
            with open(log_path, 'a+', encoding='UTF-8') as log_file:
                log_file.write(str(now) + " [crawler.py] " + log)
                log_file.close()

    def crawl(self):
        lst = set()
        ord_lst = []
        ord_lst.insert(0, self.website)
        ord_lst_ind = 0

        print(f"## Crawler started from {self.website} with "
              f"{str(self.c_depth)} depth crawl, and {str(self.c_pause)} "
              f"second(s) delay.")

        for index in range(0, int(self.c_depth)):
            for item in ord_lst:
                html_page = http.client.HTTPResponse
                if ord_lst_ind > 0:
                    try:
                        if item is not None:
                            html_page = urllib.request.urlopen(item)
                    except (HTTPError, URLError) as error:
                        self.write_log(f"[INFO] ERROR: Domain or link seems to be unreachable: {str(item)} | "
                                       f"Message: {error}\n")
                        continue
                else:
                    try:
                        html_page = urllib.request.urlopen(self.website)
                        ord_lst_ind += 1
                    except (HTTPError, URLError) as error:
                        self.write_log(f"[INFO] ERROR: Domain or link seems to be unreachable: {str(item)} | "
                                       f"Message: {error}\n")
                        ord_lst_ind += 1
                        continue

                try:
                    soup = BeautifulSoup(html_page, features="html.parser")
                except TypeError:
                    print(f"## Soup Error Encountered:: couldn't parse "
                          f"ord_list # {ord_lst_ind}::{ord_lst[ord_lst_ind]}")
                    continue

                for link in soup.findAll('a'):
                    link = link.get('href')
                    if self.excludes(link):
                        continue
                    ver_link = self.canonical(link)
                    if ver_link is not None:
                        lst.add(ver_link)

                for link in soup.findAll('area'):
                    link = link.get('href')
                    if self.excludes(link):
                        continue
                    ver_link = self.canonical(link)
                    if ver_link is not None:
                        lst.add(ver_link)

                ord_lst = ord_lst + list(set(lst))
                ord_lst = list(set(ord_lst))

                page_code = html_page.status
                url_visited = f"[{str(page_code)}] {str(item)} \n"
                self.write_log("[INFO] Parsed: " + url_visited)

                if self.verbose:
                    sys.stdout.write(" -- Results: " + str(len(ord_lst)) + "\r")
                    sys.stdout.flush()

                if (ord_lst.index(item) != len(ord_lst) - 1) and float(self.c_pause) > 0:
                    time.sleep(float(self.c_pause))

            print(f"## Step {str(index + 1)} completed "
                  f"with: {str(len(ord_lst))} result(s)")

        return ord_lst


