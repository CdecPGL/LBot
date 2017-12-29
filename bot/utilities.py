'''ユーティリティ関数'''


def unify_newline_code(text):
    '''改行コードを\\nに統一する'''
    return text.replace("\r\n", "\n").replace("\r", "\n")
