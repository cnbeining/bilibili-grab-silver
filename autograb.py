#!/usr/bin/env python
#coding:utf-8
# Author:  Beining --<i#cnbeining.com>
# Purpose: Auto grab silver of Bilibili
# Created: 10/22/2015
# https://www.cnbeining.com/
# https://github.com/cnbeining

import sys
import os
import requests
import json
import getopt
from json import loads
import datetime
import time
import logging
import traceback
import glob

APPKEY = '85eb6835b0a1034e'
SECRETKEY = '2ad42749773c441109bdc0191257a664'
VER = '0.98.86'

# Dual support
try:
    input = raw_input
except NameError:
    pass

#----------------------------------------------------------------------
def get_new_task_time_and_award(headers):
    """dict->tuple of int
    time_in_minutes, silver"""
    str2Hash = 'appkey={APPKEY}&platform=ios{SECRETKEY}'.format(APPKEY = APPKEY, SECRETKEY = SECRETKEY)
    url = 'http://live.bilibili.com/mobile/freeSilverCurrentTask?appkey={APPKEY}&platform=ios&sign={sign}'.format(APPKEY = APPKEY, sign = calc_sign(str2Hash))
    response = requests.get(url, headers=headers)
    a = loads(response.content.decode('utf-8'))
    if a['code'] == 0:
        return (a['data']['minute'], a['data']['silver'])

#----------------------------------------------------------------------
def send_heartbeat(headers):
    """"""
    str2Hash = 'appkey={APPKEY}&platform=ios{SECRETKEY}'.format(APPKEY = APPKEY, SECRETKEY = SECRETKEY)
    url = 'http://live.bilibili.com/mobile/freeSilverHeart?appkey={APPKEY}&platform=ios&sign={sign}'.format(APPKEY = APPKEY, sign = calc_sign(str2Hash))
    response = requests.get(url, headers=headers)
    #print(url)
    response = requests.get(url, headers=headers)
    a = loads(response.content.decode('utf-8'))
    if response.status_code != 200 or a['code'] != 0:
        #print('WARNING: Unable to send heartbeat!')
        #print(a['msg'])
        #NO ONE GIVES A FUCK ABOUT THIS SHIT
        return False
    else:
        return True

#----------------------------------------------------------------------
def get_award(headers):
    """dict, str->int/str"""
    freeSilverAward
    str2Hash = 'appkey={APPKEY}&platform=ios{SECRETKEY}'.format(APPKEY = APPKEY, SECRETKEY = SECRETKEY)
    url = 'http://live.bilibili.com/mobile/freeSilverAward?appkey={APPKEY}&platform=ios&sign={sign}'.format(APPKEY = APPKEY, sign = calc_sign(str2Hash))
    response = requests.get(url, headers=headers)
    a = loads(response.content.decode('utf-8'))
    if response.status_code != 200 or a['code'] != 0:
        print('WARNING: Unable to obtain!')
        print(a['msg'])
        return (int(a['code']))
    else:
        return int(a['data']['awardSilver'])

#----------------------------------------------------------------------
def read_cookie(cookiepath):
    """str->list
    Original target: set the cookie
    Target now: Set the global header"""
    #print(cookiepath)
    try:
        cookies_file = open(cookiepath, 'r')
        cookies = cookies_file.readlines()
        cookies_file.close()
        # print(cookies)
        return cookies
    except Exception:
        print('Cannot read cookie, may affect some videos...')
        return ['']

#----------------------------------------------------------------------
def usage():
    """"""
    print("""Auto-grab

    -h: help:
    This.

    -c: cookies:
    location of cookies

    -l: Default: INFO
    INFO/DEBUG
    """)

#----------------------------------------------------------------------
def main(headers = {}):
    """"""
    time_in_minutes, silver = get_new_task_time_and_award(headers)
    print('ETA: {time_in_minutes} minutes, silver: {silver}'.format(time_in_minutes = time_in_minutes, silver = silver))
    now = datetime.datetime.now()
    picktime = now + datetime.timedelta(minutes = time_in_minutes) + datetime.timedelta(seconds = 10)  #safer for BS
    while 1:
        if datetime.datetime.now() <= picktime:
            send_heartbeat(headers)
            time.sleep(61)
        else:
            break
    award = get_award(headers)
    #if award == -400 or award == -99:  #incorrect captcha/not good to collect
    if award < 0:  #error?
        for i in range(10):
            award = get_award(headers)
            if award == True:
                break
            else:
                print('Fuck, retry #{i}'.format(i = i))
                time.sleep(5)
    print('Award: {award}'.format(award = award))
    return award

if __name__=='__main__':
    argv_list = []
    argv_list = sys.argv[1:]
    cookiepath,uploader,LOG_LEVEL = '', '', ''
    try:
        opts, args = getopt.getopt(argv_list, "hc:l:",
                                   ['help', "cookie=", "log="])
    except getopt.GetoptError:
        usage()
        exit()
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            exit()
        if o in ('-c', '--cookie'):
            cookiepath = a
        if o in ('-l', '--log'):
            try:
                LOG_LEVEL = str(a)
            except Exception:
                LOG_LEVEL = 'INFO'
    logging.basicConfig(level = logging_level_reader(LOG_LEVEL))
    if cookiepath == '':
        cookiepath = './bilicookies'
    if not os.path.exists(cookiepath):
        print('Unable to open the cookie\'s file!')
        print('Please put your cookie in the file \"bilicookies\" or set a path yourself')
        exit()
    cookies = read_cookie(cookiepath)[0]
    headers = {
        'dnt': '1',
        'accept-encoding': 'gzip, deflate, sdch',
        'accept-language': 'en-CA,en;q=0.8,en-US;q=0.6,zh-CN;q=0.4,zh;q=0.2',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.16 Safari/537.36',
        'accept': 'image/webp,image/*,*/*;q=0.8',
        'authority': 'live.bilibili.com',
        'cookie': cookies,
    }
    while 1:
        try:
            main(headers)
        except KeyboardInterrupt:
            exit()