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
from base64 import b64encode
import shutil
import getopt
from json import loads
import datetime
import time
import base64,hmac,hashlib
import re

#----------------------------------------------------------------------
def generate_16_integer():
    """None->str"""
    from random import randint
    return str(randint(1000000000000000, 9999999999999999))

#----------------------------------------------------------------------
def safe_to_eval(string_this):
    """"""
    pattern = re.compile(r'^[\d\+\-\s]+$')
    match = pattern.match(string_this)
    if match:
        return True
    else:
        return False

#----------------------------------------------------------------------
def get_new_task_time_and_award(headers):
    """dict->tuple of int
    time_in_minutes, silver"""
    random_r = generate_16_integer()
    url = 'http://live.bilibili.com/FreeSilver/getCurrentTask?r=0.{random_r}'.format(random_r = random_r)
    response = requests.get(url, headers=headers)
    a = loads(response.content)
    if a['code'] == 0:
        return (a['data']['minute'], a['data']['silver'])

#----------------------------------------------------------------------
def get_captcha_from_live(headers, uploader = 'i'):
    """dict,str->str
    get the captcha link"""
    import shutil
    random_t = generate_16_integer()  #save for later
    url = 'http://live.bilibili.com/FreeSilver/getCaptcha?t=0.{random_t}'.format(random_t = random_t)
    response = requests.get(url, stream=True, headers=headers)
    if uploader == 't':  #tietuku
        result = uploadImageToTietuku(response.raw)
    elif uploader == 'i':  #imgur
        result = image_to_imgur_link(response.raw)
    return result

#----------------------------------------------------------------------
def uploadImageToTietuku(file):
    """rawfile->str
    http://www.01responsible.com/2015/05/%E8%B4%B4%E5%9B%BE%E5%BA%93python%E4%B8%8A%E4%BC%A0%E4%BB%A3%E7%A0%81/"""
    URL = "http://up.tietuku.com/"
    jsoncode = ('{\"deadline\":%s,\"aid\":%s}') % (int(time.time())+60,1145722)
    encodedParam = base64.urlsafe_b64encode(jsoncode)
    sign = hmac.new("da39a3ee5e6b4b0d3255bfef95601890afd80709",encodedParam,hashlib.sha1).digest()
    encodedSign = base64.urlsafe_b64encode(sign)
    Token = "98bf82eb7ddcb735e77d7e6c71b723c83265e560" + ':' + encodedSign + ':' + encodedParam
    a = requests.post(URL, {"Token":Token},files={"file":file})
    return str(json.loads(a.content)['linkurl'])

#----------------------------------------------------------------------
def image_to_imgur_link(file_this):
    """rawfile->str"""
    import requests
    import json
    from base64 import b64encode
    url = 'https://api.imgur.com/3/image.json'
    headers = {"Authorization": "Client-ID 4c5addf77336c2d"}
    j1 = requests.post(
        url, 
        headers = headers,
        data = {
            'image': b64encode(file_this.read()),
            'type': 'base64',
        }
    )
    info = json.loads(j1.text.decode('utf-8'))
    #status_this = str(info['status'])
    #print(info)
    link_this = str(info['data']['link'])
    return link_this

#----------------------------------------------------------------------
def image_link_ocr(image_link):
    """"""
    from baiduocr import BaiduOcr
    
    API_KEY = 'c1ff362dc90585fed08e80460496eabd'
    client = BaiduOcr(API_KEY, 'test')  # 使用个人免费版 API，企业版替换为 'online'
    
    res = client.recog(image_link, service='Recognize', lang='CHN_ENG')
    
    return res['retData'][0]['word']

#----------------------------------------------------------------------
def send_heartbeat(headers):
    """"""
    random_t = generate_16_integer()
    url = 'http://live.bilibili.com/freeSilver/heart?r=0.{random_t}'.format(random_t = random_t)
    #print(url)
    response = requests.get(url, headers=headers)
    a = loads(response.content)
    if response.status_code != 200 or a['code'] != 0:
        print('WARNING: Unable to send heartbeat!')
        print(a['msg'])
    else:
        return True

#----------------------------------------------------------------------
def get_award(headers, captcha):
    """dict, str->int/str"""
    random_t = generate_16_integer()
    url = 'http://live.bilibili.com/freeSilver/getAward?r=0.{random_t}&captcha={captcha}'.format(random_t = random_t, captcha = captcha)
    response = requests.get(url, headers=headers)
    a = loads(response.content)
    if response.status_code != 200 or a['code'] != 0:
        print('WARNING: Unable to obtain!')
        print(a['msg'])
        return False
    else:
        return int(a['data']['awardSilver'])

#----------------------------------------------------------------------
def read_cookie(cookiepath):
    """str->list
    Original target: set the cookie
    Target now: Set the global header"""
    print(cookiepath)
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
def captcha_wrapper(headers, uploader):
    """"""
    captcha_link = get_captcha_from_live(headers, uploader)
    captcha_text = image_link_ocr(captcha_link).encode('utf-8')
    answer = ''
    if safe_to_eval(captcha_text):
        try:
            answer = eval(captcha_text)  #+ -
        except NameError:
            answer = ''
    if answer == '':  #error or cannot be eval
        print('WARNING: Cannot automatic the process due to security concerns')
        print('OCR result: {captcha_text}'.format(captcha_text = captcha_text))
        answer = raw_input('please type the result by yourself: ')
    return answer

#----------------------------------------------------------------------
def usage():
    """"""
    print("""Auto-grab
    
    -h: help:
    This.
    
    -c: cookies:
    location of cookies
    
    -u: Uploader:
    t: Tietuku
    i: Imgur
    """)

#----------------------------------------------------------------------
def main(headers = {}, uploader='i'):
    """"""
    time_in_minutes, silver = get_new_task_time_and_award(headers)
    print('ETA: {time_in_minutes} minutes, silver: {silver}'.format(time_in_minutes = time_in_minutes, silver = silver))
    now = datetime.datetime.now()
    picktime = now + datetime.timedelta(minutes = time_in_minutes)
    while 1:
        if datetime.datetime.now() <= picktime:
            send_heartbeat(headers)
            time.sleep(30)
        else:
            break
    answer = captcha_wrapper(headers, uploader)
    award = get_award(headers, answer)
    if award == -400 or award == -99:  #incorrect captcha/not good to collect
        for i in range(10):
            captcha_wrapper(headers, uploader)
            award = get_award(headers, answer)
            if award == True:
                break
            else:
                time.sleep(5)
    print('Award: {award}'.format(award = award))
    return award

if __name__=='__main__':
    argv_list = []
    argv_list = sys.argv[1:]
    cookiepath,uploader = '', ''
    try:
        opts, args = getopt.getopt(argv_list, "hc:u:",
                                   ['help', "cookie=", "uploader="])
    except getopt.GetoptError:
        usage()
        exit()
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            exit()
        if o in ('-c', '--cookie'):
            cookiepath = a
            print('aasd')
        if o in ('-u', '--uploader'):
            uploader = a
    if cookiepath == '':
        cookiepath = './bilicookies'
    if not os.path.exists(cookiepath):
    	print('Unable to open the cookie\'s file!')
    	print('Please put your cookie in the file \"bilicookies\" or set a path yourself')
    	exit()
    if uploader == '':
        uploader = 'i'
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
        main(headers, uploader)
