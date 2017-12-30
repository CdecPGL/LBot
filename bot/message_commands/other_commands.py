'''その他のメッセージコマンド'''

from bot.authorities import UserAuthority
from bot.message_commands.message_command import (CommandSource,
                                                  add_command_handler)


@add_command_handler("議事録開始", UserAuthority.Editor)
@add_command_handler("議事録終了", UserAuthority.Editor)
@add_command_handler("テスト", UserAuthority.Master)
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
