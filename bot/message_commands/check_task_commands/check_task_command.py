'''タスク確認時コマンド'''

from bot.authorities import UserAuthority

from ..message_command import CommandSource, MessageCommandGroupBase


class CheckTaskMessageCommandGroup(MessageCommandGroupBase):
    '''標準のメッセージコマンドグループ'''
    name = "タスク確認"
    order = 50
    validate_in_initialize = False
    enable_command_suggestion = True
    enable_auto_command_correction = True
    suggestion_word_match_rate_threshold = 0.8


@CheckTaskMessageCommandGroup.add_command("できる", UserAuthority.Watcher)
def participate_command(command_source: CommandSource, target_task_number: str = None)->(str, [str]):
    '''タスクに参加できることを伝えます。
    ■コマンド引数
    (1: 対象のタスク番号。対象タスクが一つしかない場合は省略可能)'''
    pass


@CheckTaskMessageCommandGroup.add_command("できない", UserAuthority.Watcher)
def absent_command(command_source: CommandSource, target_task_number: str = None):
    '''タスクに参加できないことを伝えます。
    ■コマンド引数
    (1: 対象のタスク番号。対象タスクが一つしかない場合は省略可能)'''
    pass
