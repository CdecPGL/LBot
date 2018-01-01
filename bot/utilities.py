'''ユーティリティ関数'''

import datetime
import re

TIMEZONE_JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')


def get_datetime_with_jst(year, month, day, hour=0, minuit=0, second=0, milisecond=0):
    '''日本時間で時間を取得'''
    return datetime.datetime(year, month, day, hour, minuit, second, milisecond, tzoneinfo=TIMEZONE_JST)


def unify_newline_code(text: str)->str:
    '''改行コードを\\nに統一する'''
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_command_paramater_strig(command_parameter_string: str)->[str]:
    '''コマンドのパラメータ文字列を分割する'''
    return [item for item in re.split(r"、|,", command_parameter_string) if item]


def convert_datetime_to_string(date_time: datetime.datetime):
    '''日時を文字列に変換する'''
    return date_time.strftime('%Y/%m/%d %H:%M:%S')
