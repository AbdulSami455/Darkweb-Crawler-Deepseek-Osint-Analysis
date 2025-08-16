#!/usr/bin/python
import io
import os
import urllib.error
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from urllib.error import URLError
from http.client import InvalidURL
from http.client import IncompleteRead
from bs4 import BeautifulSoup
from pathlib import Path

from modules.checker import url_canon


def text(response=None):
    soup = BeautifulSoup(response, features="lxml")
    for s in soup(['script', 'style']):
        s.decompose()
    return ' '.join(soup.stripped_strings)


def check_yara(raw=None, yara=0):
    try:
        import yara as _yara
    except OSError:
        print("YARA module error: Try installing yara-python or disable -y")

    file_path = os.path.join('res/keywords.yar')
    if raw is not None:
        if yara == 1:
            raw = text(response=raw).lower()
        file = os.path.join(file_path)
        rules = _yara.compile(file)
        matches = rules.match(data=raw)
        if len(matches) != 0:
            print("YARA: Found a match!")
        return matches


def input_file_to_folder(input_file, output_path, yara=None):
    i = 0
    file = io.TextIOWrapper
    try:
        file = open(input_file, 'r')
    except IOError as err:
        print(f"Error: {err}\n## Can't open: {input_file}")

    for line in file:
        try:
            page_name = line.rsplit('/', 1)
            cl_page_name = str(page_name[1])
            cl_page_name = cl_page_name[:-1]
            if len(cl_page_name) == 0:
                output_file = "index.htm"
            else:
                output_file = cl_page_name
        except IndexError as error:
            print(f"Error: {error}")
            continue

        try:
            content = urllib.request.urlopen(line, timeout=10).read()
            if yara is not None:
                full_match_keywords = check_yara(content, yara)
                if len(full_match_keywords) == 0:
                    print('No matches found.')
                    continue
            filename = Path(output_path + "/" + output_file)
            if filename.is_file():
                i += 1
                filename = output_path + "/" + output_file + "(" + str(i) + ")"
            with open(filename, 'wb') as results:
                results.write(content)
            print(f"# File created on: {os.getcwd()}/{filename}")
        except HTTPError as e:
            print(f"Error: {e.code}, cannot access: {e.url}")
            continue
        except InvalidURL:
            print(f"Invalid URL: {line}, \n Skipping...")
            continue
        except IncompleteRead:
            print(f"IncompleteRead on {line}")
            continue
        except IOError as err:
            print(f"Error: {err}\nCan't write on file: {output_file}")
    file.close()


def input_file_to_terminal(input_file, yara):
    try:
        with open(input_file, 'r') as file:
            for line in file:
                website = url_canon(line, 0)
                try:
                    content = urllib.request.urlopen(website).read()
                except (HTTPError, URLError, InvalidURL) as err:
                    print(f"## ERROR: {err}. URL: " + website)
                    continue
                if yara is not None:
                    full_match_keywords = check_yara(raw=content, yara=yara)
                    if len(full_match_keywords) == 0:
                        print(f"No matches in: {line}")
                print(content)
    except IOError as err:
        print(f"ERROR: {err}\n## Not valid file. File tried: " + input_file)


def url_to_folder(website, output_file, output_path, yara):
    try:
        output_file = output_path + "/" + output_file
        content = urllib.request.urlopen(website).read()
        if yara is not None:
            full_match_keywords = check_yara(raw=content, yara=yara)
            if len(full_match_keywords) == 0:
                print(f"No matches in: {website}")
        with open(output_file, 'wb') as file:
            file.write(content)
        print(f"## File created on: {os.getcwd()}/{output_file}")
    except (HTTPError, URLError, InvalidURL) as err:
        print(f"HTTPError: {err}")
    except IOError as err:
        print(f"Error: {err}\n Can't write on file: {output_file}")


def url_to_terminal(website, yara):
    try:
        content = urllib.request.urlopen(website).read()
        if yara is not None:
            full_match_keywords = check_yara(content, yara)
            if len(full_match_keywords) == 0:
                print(f"No matches in: {website}")
                return
        print(content)
    except (HTTPError, URLError, InvalidURL) as err:
        print(f"Error: ({err}) {website}")
        return


def extractor(website, crawl, output_file, input_file, output_path, selection_yara):
    if len(input_file) > 0:
        if crawl:
            input_file_to_folder(input_file, output_path, selection_yara)
        else:
            input_file_to_terminal(input_file, selection_yara)
    else:
        if len(output_file) > 0:
            url_to_folder(website, output_file, output_path, selection_yara)
        else:
            url_to_terminal(website, selection_yara)


