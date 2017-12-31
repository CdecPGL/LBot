'''メッセージによるコマンド関連'''

import inspect
import sys

from bot.authorities import UserAuthority
from bot.models import Group, User
from bot.reply_generators import generate_random_reply


class CommandSource(object):
    '''コマンド送信元のデータ'''

    def __init__(self, user_data: User, group_data: Group):
        self.user_data = user_data
        self.group_data = group_data


__command_map = {}


def add_command_handler(command_name, authority):
    '''コマンドハンドラを追加するデコレータ。
    第一引数にコマンド送信元、第二引数以降にコマンドパラメータを取り、(返信,エラーリスト)を戻り値とする関数を登録する。
    返信がNoneの場合はコマンド失敗とみなす。'''
    def decorator(func):
        decorator.__doc__ = func.__doc__
        __command_map[command_name] = (func, authority)
    return decorator


@add_command_handler("使い方", UserAuthority.Watcher)
def help_command(command_source: CommandSource, target_command_name: str = None)->(str, [str]):
    '''使い方を表示します。コマンドの指定がない場合はコマンドの一覧を表示します。
    ■コマンド引数
    (1: 使い方を見たいコマンド名)'''
    # コマンド一覧の作成
    command_list = ["■{}(権限：{})".format(command_name, command_authority.name)
                    for command_name, (command_func, command_authority) in __command_map.items()]
    # ターゲットが指定されていたらそのコマンドの詳細を表示
    if target_command_name:
        if target_command_name in __command_map:
            command_func, command_authority = __command_map[target_command_name]
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


def execute_command(command: str, command_source: CommandSource, params: [str]):
    '''コマンド実行。返信メッセージを返す'''
    if command in __command_map:
        command_func, command_authority = __command_map[command]
        # 権限の確認
        user_authority = UserAuthority[command_source.user_data.authority]
        if user_authority.check(command_authority):
            try:
                inspect.signature(command_func).bind(command_source, *params)
            except TypeError:
                sys.stderr.write(
                    "コマンドの実行でエラーが発生。({})\n".format(sys.exc_info()[1]))
                return "コマンド引数の数が不正です。\n■「{}」コマンドの使い方\n{}".format(command, inspect.getdoc(command_func))
            reply, errors = command_func(command_source, *params)
        else:
            reply = None
            errors = ["残念ながら権限がないよ。Youの権限：{}、コマンドの要求権限：{}。権限の変更はMasterユーザーに頼んでネ^_^".format(
                user_authority.name, command_authority.name)]
        # 結果を返す
        if reply is None:
            errors.append("コマンド「{}」の実行に失敗しちゃった。。。".format(command))
        else:
            errors.append(reply)
        return "\n".join(errors)
    elif command is not None:
        command_suggestions = [command_name for command_name in __command_map.keys(
        ) if command_name.find(command) >= 0]
        if len(command_suggestions) > 1:
            return "{}？もしかして{}の間違いかなぁ？".format(command, "「" + command_suggestions[0] + "」")
        elif command_suggestions:
            return "{}？もしかして{}のどれかの間違いかなぁ？".format(command, "、".join(["「" + command_sug + "」" for command_sug in command_suggestions]))
        else:
            return generate_random_reply(command)
    else:
        return "コマンドが指定されていません"
