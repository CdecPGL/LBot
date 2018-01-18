'''LINE関連のAPI'''

import os
import sys

import linebot

try:
    ACCESS_TOKEN = os.environ["LBOT_LINE_ACCESS_TOKEN"]
    CHANNEL_SECRET = os.environ["LBOT_LINE_CHANNEL_SECRET"]
except KeyError:
    ACCESS_TOKEN = None
    CHANNEL_SECRET = None
    sys.stderr.write(
        'LINEにアクセスするためには環境変数としてLINE_SCCESS_TOKENとLINE_CHANNEL_SECRETが必要です。')


api = linebot.LineBotApi(ACCESS_TOKEN)
