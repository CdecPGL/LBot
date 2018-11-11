'''LINE関連のAPI'''

import os
import sys

import linebot

api = None
channel_secret = None


def set_up_line():
    '''LINEのセットアップを行う'''
    global channel_secret, api
    try:
        access_token = os.environ["LBOT_LINE_ACCESS_TOKEN"]
        channel_secret = os.environ["LBOT_LINE_CHANNEL_SECRET"]
        api = linebot.LineBotApi(access_token)
    except KeyError:
        sys.stderr.write(
            'LINEにアクセスするためには環境変数としてLINE_SCCESS_TOKENとLINE_CHANNEL_SECRETが必要です。')
