'''ユーティリティ関数'''

import datetime
import re

# 日本時間
TIMEZONE_JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
# デフォルトのタイムゾーン
TIMEZONE_DEFAULT = TIMEZONE_JST
# メンテナンスモード
ENABLE_MAINTENANCE_MODE = False


def unify_newline_code(text: str)->str:
    '''改行コードを\\nに統一する'''
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_command_paramater_strig(command_parameter_string: str)->[str]:
    '''コマンドのパラメータ文字列を分割する'''
    return [item for item in re.split(r"、|,", command_parameter_string) if item]


def remove_from_comma_separeted_string(command_separated_string: str, item: str):
    '''カンマ区切り文字列から指定した要素を除去する'''
    items = split_command_paramater_strig(command_separated_string)
    if item in items:
        items.remove(item)
    return ",".join(items)


def add_to_comma_separeted_string(command_separated_string: str, item: str):
    '''カンマ区切り文字列に指定した要素を追加する'''
    items = split_command_paramater_strig(command_separated_string)
    if item not in items:
        items.append(item)
    return ",".join(items)


def convert_datetime_in_default_timezone_to_string(date_time: datetime.datetime):
    '''日時をデフォルトのタイムゾーンで文字列に変換する'''
    return date_time.astimezone(TIMEZONE_DEFAULT).strftime('%Y/%m/%d %H:%M:%S')
