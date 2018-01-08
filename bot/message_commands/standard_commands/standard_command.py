'''標準のコマンド'''

from ..message_command import MessageCommandGroupBase


class StandardMessageCommandGroup(MessageCommandGroupBase):
    '''標準のメッセージコマンドグループ'''
    name = "標準"
    order = 100
    validate_in_initialize = True
    enable_command_suggestion = True
    enable_auto_command_correction = False
    suggestion_word_match_rate_threshold = 0.7
