'''ユーティリティ関数'''

import datetime
import re

# 日本時間
TIMEZONE_JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
# デフォルトのタイムゾーン
TIMEZONE_DEFAULT = TIMEZONE_JST


def unify_newline_code(text: str)->str:
    '''改行コードを\\nに統一する'''
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_command_paramater_strig(command_parameter_string: str)->[str]:
    '''コマンドのパラメータ文字列を分割する'''
    return [item for item in re.split(r"、|,", command_parameter_string) if item]


def convert_datetime_in_default_timezone_to_string(date_time: datetime.datetime):
    '''日時をデフォルトのタイムゾーンで文字列に変換する'''
    return date_time.astimezone(TIMEZONE_DEFAULT).strftime('%Y/%m/%d %H:%M:%S')
