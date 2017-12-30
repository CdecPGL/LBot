'''ユーティリティ関数'''

import re


def unify_newline_code(text: str)->str:
    '''改行コードを\\nに統一する'''
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_command_paramater_strig(command_parameter_string: str)->[str]:
    '''コマンドのパラメータ文字列を分割する'''
    return [item for item in re.split(r"、|,", command_parameter_string) if item]
