'''その他のメッセージコマンド'''

from ....authorities import UserAuthority
from ....utilities import TIMEZONE_DEFAULT
from ..message_command import CommandSource
from .standard_command import StandardMessageCommandGroup


@StandardMessageCommandGroup.add_command("議事録開始", UserAuthority.Editor)
@StandardMessageCommandGroup.add_command("議事録終了", UserAuthority.Editor)
@StandardMessageCommandGroup.add_command("テスト", UserAuthority.Master)
def test_command(command_source: CommandSource, *params)->(str, [str]):
    '''テストコマンド'''
    reply = '<送信者>\n'
    reply += f'UserID: {command_source.user_data.id}\n'
    reply += f'UserName: {command_source.user_data.name}\n'
    reply += '<送信元グループ>\n'
    if command_source.group_data:
        reply += f'GroupID: {command_source.group_data.id}\n'
        reply += f'GroupName: {command_source.group_data.name}\n'
        for service_group in command_source.group_data.service_groups.all():
            reply += f'ServiceGroup: {service_group.name_in_service}({service_group.id_in_service}@{service_group.kind})\n'
    else:
        reply += "なし"
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
