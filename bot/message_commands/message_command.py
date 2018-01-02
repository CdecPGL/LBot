'''メッセージコマンド'''

import difflib
import inspect
import sys
import unicodedata

from bot.authorities import UserAuthority
from bot.models import Group, User
from bot.reply_generators import generate_random_reply


class CommandSource(object):
    '''コマンド送信元のデータ'''

    def __init__(self, user_data: User, group_data: Group):
        self.user_data = user_data
        self.group_data = group_data


def normalize_command_string(command_string):
    '''コマンド文字列を正規化する'''
    command_string = unicodedata.normalize('NFKC', command_string)
    return command_string


class MessageCommandGroupBase(object):
    '''メッセージコマンドグループの基底クラス
    コマンドグループはこれを継承し、クラス変数として"name"と"order"を定義すること。'''
    __command_map = {}

    def __init__(self):
        pass

    @classmethod
    def add_command(cls, command_name,  authority: UserAuthority):
        '''コマンドハンドラを追加するデコレータ。
        第一引数にコマンド送信元、第二引数以降にコマンドパラメータを取り、(返信,エラーリスト)を戻り値とする関数を登録する。
        返信がNoneの場合はコマンド失敗とみなす。'''
        def decorator(func):
            decorator.__doc__ = func.__doc__
            cls.__command_map[command_name] = (func, authority)
        return decorator

    @classmethod
    def command_map(cls):
        '''コマンドマップを取得する'''
        return cls.__command_map

    def execute_command(self, command_name: str, command_source: CommandSource, command_param_list: [str])->(bool, str):
        '''コマンドを実行する。
        戻り値は(続けるかどうか,返信メッセージ)。'''
        command = normalize_command_string(command_name)
        command_map = self.__class__.__command_map
        if command in command_map:
            command_func, command_authority = command_map[command]
            # 権限の確認
            user_authority = UserAuthority[command_source.user_data.authority]
            if user_authority.check(command_authority):
                try:
                    inspect.signature(command_func).bind(
                        command_source, *command_param_list)
                except TypeError:
                    sys.stderr.write(
                        "コマンドの実行でエラーが発生。({})\n".format(sys.exc_info()[1]))
                    return False, "コマンド引数の数が不正です。\n■「{}」コマンドの使い方\n{}".format(command, inspect.getdoc(command_func))
                reply, errors = command_func(
                    command_source, *command_param_list)
            else:
                reply = None
                errors = ["残念ながら権限がないよ。Youの権限：{}、コマンドの要求権限：{}。権限の変更はMasterユーザーに頼んでネ^_^".format(
                    user_authority.name, command_authority.name)]
            # 結果を返す
            if reply is None:
                errors.append("コマンド「{}」の実行に失敗しちゃった。。。".format(command))
            else:
                errors.append(reply)
            return False, "\n".join(errors)
        elif command is not None:
            command_suggestions = [command_name for command_name in command_map.keys(
            ) if difflib.SequenceMatcher(None, command, command_name).ratio() >= 0.7]
            if len(command_suggestions) == 1:
                return False, "{}？もしかして{}の間違いかなぁ？".format(command, "「" + command_suggestions[0] + "」")
            elif command_suggestions:
                return False, "{}？もしかして{}のどれかの間違いかなぁ？".format(command, "、".join(["「" + command_sug + "」" for command_sug in command_suggestions]))
            else:
                return True, None
        else:
            return True, None


__command_group_order_map = {}
__command_group_list = {}


def register_command_groups():
    '''コマンドグループを登録する'''
    global __command_group_list, __command_group_order_map
    print("{}, {}".format("1", MessageCommandGroupBase.__subclasses__()))
    command_groups = MessageCommandGroupBase.__subclasses__()
    for command_group_class in command_groups:
        command_group_order = command_group_class.order
        command_group_name = command_group_class.name
        __command_group_order_map[command_group_name] = command_group_order
        __command_group_list[command_group_order] = (
            True, command_group_class())


def execute_message_command(command_name: str, command_source: CommandSource,  command_param_list: [str]):
    '''コマンドを実行する。戻り値は返信メッセージ。'''
    # コマンドグループを優先度準に並び替える
    command_group_list = [is_valid_command_grou for order, is_valid_command_grou in sorted(
        __command_group_list.items(), key=lambda order_group: order_group[0])]
    for is_valid, command_group in command_group_list:
        # コマンドグループが無効なら飛ばす
        if not is_valid:
            continue
        # コマンド実行
        is_continue, reply = command_group.execute_command(
            command_name, command_source, command_param_list)
        # 続行しないなら最後の返信を返す
        if not is_continue:
            return reply
    # 最後まで来たらてきとうな返事を返す
    return generate_random_reply(command_name)
