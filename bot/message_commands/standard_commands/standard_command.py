'''標準のコマンド'''

import inspect

from bot.authorities import UserAuthority

from ..message_command import CommandSource, MessageCommandGroupBase


class StandardMessageCommandGroup(MessageCommandGroupBase):
    '''標準のメッセージコマンドグループ'''
    name = "標準"
    order = 0

    def __init__(self):
        super(StandardMessageCommandGroup, self).__init__()
        # コマンドの提案を有効にするかどうか
        self.enable_command_suggestion = False
        # コマンドの提案が有効の場合に、提案を自動的に補正するかどうか
        self.enable_auto_command_correction = False


@StandardMessageCommandGroup.add_command("使い方", UserAuthority.Watcher)
def help_command(command_source: CommandSource, target_command_name: str = None)->(str, [str]):
    '''使い方を表示します。コマンドの指定がない場合はコマンドの一覧を表示します。
    ■コマンド引数
    (1: 使い方を見たいコマンド名)'''
    command_map = StandardMessageCommandGroup.command_map()
    # コマンド一覧の作成
    command_list = ["■{}(権限：{})".format(command_name, command_authority.name)
                    for command_name, (command_func, command_authority) in command_map.items()]
    # ターゲットが指定されていたらそのコマンドの詳細を表示
    if target_command_name:
        if target_command_name in command_map:
            command_func, command_authority = command_map[target_command_name]
            return "<「{}」コマンドの使い方>\n■必要権限\n{}\n■説明\n{}".format(target_command_name, command_authority.name, inspect.getdoc(command_func)), []
        else:
            return "「{}」コマンドは存在しません。\n<コマンド一覧>\n{}".format(target_command_name, "\n".join(command_list)), []
    # 指定されていなかったらコマンドリストを表示
    else:
        reply = 'グループの場合は「#」を先頭に付けて、個人ラインの場合は何も付けずに、コマンドを指定して実行することができます。\n'
        reply += 'コマンドでない文字列を指定した場合はてきとうな返事を返します。'
        reply += 'また、「使い方」コマンドにコマンド名を指定することでそのコマンドの詳細説明を表示します。\n'
        reply += '<コマンド一覧>\n' + "\n".join(command_list)
        return reply, []
