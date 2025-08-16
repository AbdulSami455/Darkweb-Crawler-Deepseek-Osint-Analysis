#!/usr/bin/python

import os
import re
import subprocess
import sys
from json import load
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen


def url_canon(website, verbose):
    if not website.startswith("http://") and not website.startswith("https://"):
        website = "https://" + website
        if verbose:
            print(("## URL fixed: " + website))
    return website


def extract_domain(url, remove_http=True):
    uri = urlparse(url)
    if remove_http:
        domain_name = f"{uri.netloc}"
    else:
        domain_name = f"{uri.scheme}://{uri.netloc}"
    return domain_name


def folder(website, verbose):
    parsed = urlparse(website)
    if parsed.scheme != '':
        output_folder = "output/" + urlparse(website).netloc
    else:
        output_folder = "output/" + website
    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
        except FileExistsError:
            if verbose:
                print(f"## Folder exists already: {website}")
    if verbose:
        print(f"## Folder created: {website}")
    return output_folder


def check_tor(verbose):
    try:
        check_for_tor = subprocess.check_output(['ps', '-e'])
    except (subprocess.CalledProcessError, FileNotFoundError):
        # In Docker containers or when ps command is not available, skip the check
        if verbose:
            print("## TOR process check skipped (container environment)")
        return

    def find_whole_word(word):
        return re.compile(r'\b({0})\b'.format(word),
                          flags=re.IGNORECASE).search

    if find_whole_word('tor')(str(check_for_tor)):
        if verbose:
            print("## TOR is ready!")
    else:
        if verbose:
            print("## TOR is NOT running locally (using remote proxy)")


def check_ip():
    api_address = 'https://api.ipify.org/?format=json'
    try:
        my_ip = load(urlopen(api_address))['ip']
        print(f'## Your IP: {my_ip}')
    except HTTPError as err:
        error = sys.exc_info()[0]
        print(f"Error: {error} \n## IP cannot be obtained. \n## Is {api_address} up? \n## HTTPError: {err}")


