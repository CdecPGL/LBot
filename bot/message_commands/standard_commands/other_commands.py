'''その他のメッセージコマンド'''

from ...authorities import UserAuthority
from ...utilities import TIMEZONE_DEFAULT
from ..message_command import CommandSource
from .standard_command import StandardMessageCommandGroup


@StandardMessageCommandGroup.add_command("議事録開始", UserAuthority.Editor)
@StandardMessageCommandGroup.add_command("議事録終了", UserAuthority.Editor)
@StandardMessageCommandGroup.add_command("テスト", UserAuthority.Master)
def test_command(command_source: CommandSource, *params)->(str, [str]):
    '''テストコマンド'''
    reply = '<送信者>\n'
    reply += 'LineUserID: {}\n'.format(
        command_source.user_data.line_user.user_id)
    reply += 'Name: {}\n'.format(command_source.user_data.name)
    reply += '<送信元グループ>\n'
    if command_source.group_data:
        line_group_id = command_source.group_data.line_group.group_id
        group_name = command_source.group_data.name if command_source.group_data.name else '未設定'
    else:
        line_group_id = "なし"
        group_name = "なし"
    reply += 'LineGroupID: {}\n'.format(line_group_id)
    reply += 'Name: {}\n'.format(group_name)
    reply += '<コマンド引数>\n'
    reply += "\n".join(["{}: {}".format(idx + 1, param)
                        for idx, param in enumerate(params)])
    return reply, []


@StandardMessageCommandGroup.add_command("タイムゾーン確認", UserAuthority.Watcher)
def check_timezone(command_source: CommandSource):
    '''現在のデフォルトタイムゾーンを表示します。
    タスクなどの日時の設定時に特に指定しなければ、デフォルトタイムゾーンが用いられます。
    また、日時の憑依にもデフォルトタイムゾーンが用いられます。
    ■コマンド引数
    なし'''
    return "■デフォルトタイムゾーン\n{}".format(TIMEZONE_DEFAULT), []
