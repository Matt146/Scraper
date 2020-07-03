#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urlparse
import threading
import time
import os
import string
import random

LOCK = threading.Lock()
LINK_SEARCH_DEPTH = 1

def remove_values_from_list(the_list, val):
    return [value for value in the_list if value != val]

clicked_links = []
data = {}

def value_in_list(the_list, val):
    s = set(the_list)
    if s in the_list:
        return True
    return False

#################################
# Index links
#################################
def get_backlinks(response):
    # Parse the response for all the <a> tags
    soup = BeautifulSoup(response.text, 'lxml')
    elems = soup.find_all("a")

    # Then, get the href for the a tags
    links = []
    for elem in elems:
        links.append(elem.get("href"))

    # Now, go through every single link and format it
    # properly
    count = 0
    for link in links:
        if link == None:
            remove_values_from_list(links, link)
            continue
        if link[0] == "#":
            remove_values_from_list(links, link)
            continue
        if link[0] == "/":
            domain = urlparse(response.url).netloc
            links[count] = "https://" + domain + link
        count += 1

    return list(set(links))

# Downloads the data and puts it in the data list.
# Then, returns all the backlinks in the text
def download_data_from_link_list(links):
    backlinks = []
    for link in links:
        if value_in_list(links, link) == False:
            try:
                r = requests.get(link)
                backlinks_tmp = get_backlinks(r)
                print("[ + ]" + link)
                with LOCK:
                    path = urlparse(r.url).path
                    data[path] = r.text
                    for backlink in backlinks_tmp:
                        backlinks.append(backlink)
                    clicked_links.append(link)
            except Exception as e:
                print("[Error] Unable to reach {}".format(link))
    return backlinks

def sanitize_input_path(path):
    if path[0] == "/":
        return path[1:]
    return path

def gen_rand_str(strlen: int):
    letters = string.ascii_lowercase + string.ascii_uppercase + "0123456789"
    data = ""
    for x in range(strlen):
        data += random.choice(letters)
    return data

def file_writer_daemon():
    while True:
        try:
            keys_to_delete = []
            for k in data:
                if not os.path.exists("Data-Dump"):
                    os.makedirs("Data-Dump")
                print(k)
                f = open("Data-Dump/" + gen_rand_str(25) + ".dwnld", "w")
                f.write(data[k])
                f.close()
                keys_to_delete.append(k)
            with LOCK:
                for key in keys_to_delete:
                    del data[key]
        except Exception as e:
            print("[Error] {}".format(e))
        time.sleep(3)

if __name__ == "__main__":
    website = input("What is the target website: ")
    search_depth = input("Type in the recursion depth for which you want to traverse links: ")
    LINK_SEARCH_DEPTH = search_depth
    threading.Thread(target=file_writer_daemon, args=[]).start()
    resp = requests.get(website)
    backlinks = get_backlinks(resp)
    backlinks_new = download_data_from_link_list(backlinks)
    for x in range(LINK_SEARCH_DEPTH):
        backlinks_new = download_data_from_link_list(backlinks_new)
    print("[ * ] Completed download... You may exit with Ctrl+C")