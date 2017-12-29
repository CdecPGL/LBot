'''ユーティリティ関数'''


def unify_newline_code(text):
    '''改行コードを\\nに統一する'''
    return text.replace("\r\n", "\n").replace("\r", "\n")

def split_command_paramater_strig(command_parameter_string):
    '''コマンドのパラメータ文字列を分割する'''
    return [item for item in command_parameter_string.split("、").split(",") if item]
