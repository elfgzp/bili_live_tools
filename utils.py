# -*- coding: utf-8 -*-

import re
import requests

LOGIN_CHECK_URL = 'http://api.live.bilibili.com/User/getUserInfo'
SEND_URL = 'http://live.bilibili.com/msg/send'
TV_URL = 'http://api.live.bilibili.com/gift/v2/smalltv/join'
QUERY_RAFFLE_URL = 'http://api.live.bilibili.com/activity/v1/Raffle/check'
RAFFLE_NOTICE_URL = 'http://api.live.bilibili.com/activity/v1/Raffle/notice'
RAFFLE_URL = 'http://api.live.bilibili.com/activity/v1/Raffle/join'
QUERY_FREE_SILVER = 'http://api.live.bilibili.com/FreeSilver/getCurrentTask'
GET_FREE_SILVER = 'http://api.live.bilibili.com/FreeSilver/getAward'
CAPTCHA_URL = 'http://api.live.bilibili.com/freeSilver/getCaptcha'
IP_PORT_REGEX = '[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}:[0-9]{1,5}'


def get_proxy():
    try:
        proxy = requests.get("http://127.0.0.1:5010/get/").content
    except:
        return False
    else:
        if re.match(IP_PORT_REGEX, proxy):
            return proxy
        else:
            return False


def get_room_info(room_id):
    try:
        payload = {'id': room_id}
        response = requests.request(
            url='http://api.live.bilibili.com/room/v1/Room/room_init',
            method='GET',
            params=payload
        )
    except Exception as e:
        pass
    else:
        response = response.json()
        if response['code'] == 0 and response['msg'] == 'ok':
            return response['data']
        else:
            return {}
