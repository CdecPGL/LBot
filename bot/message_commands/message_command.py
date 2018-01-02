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
    # コマンドグループの実行順序。これが小さいと先に実行される。子クラスで定義し直すこと
    order = None
    # グループ名。子クラスで定義し直すこと
    name = None
    # 初期化時にグループを有効化するかどうか
    validate_in_initialize = False
    # コマンドの提案を有効にするかどうか
    enable_command_suggestion = False
    # コマンドの提案が有効の場合に、提案を自動的に補正するかどうか。有効の場合、提案が一つだけならそのコマンドが実行される。
    enable_auto_command_correction = False
    # コマンド提案時の単語一致率閾値
    suggestion_word_match_rate_threshold = 0.7

    @classmethod
    def add_command(cls, command_name, authority: UserAuthority):
        '''コマンドハンドラを追加するデコレータ。
        第一引数にコマンド送信元、第二引数以降にコマンドパラメータを取り、(返信,エラーリスト)を戻り値とする関数を登録する。
        返信がNoneの場合はコマンド失敗とみなす。'''
        def decorator(func):
            # __command_map変数を持っていなかったら追加する
            cls.command_map()[command_name] = (func, authority)
        return decorator

    @classmethod
    def command_map(cls):
        '''コマンドマップを取得する'''
        if not hasattr(cls, "_{}__command_map".format(cls.__name__)):
            setattr(cls, "_{}__command_map".format(cls.__name__), {})
        print(cls)
        return cls.__command_map

    def execute_command(self, command_name: str, command_source: CommandSource, command_param_list: [str])->(bool, str):
        '''コマンドを実行する。
        戻り値は(続けるかどうか,返信メッセージ)。'''
        command = normalize_command_string(command_name)
        command_map = self.__class__.command_map()

        # 指定コマンドがコマンドマップにない場合
        if command not in command_map:
            # コマンド文字列がから出ない場合は、設定に応じて提案したりする
            if command is not None:
                # コマンドの提案
                if self.enable_command_suggestion:
                    command_suggestions = [command_name for command_name in command_map.keys(
                    ) if difflib.SequenceMatcher(None, command, command_name).ratio() >= self.suggestion_word_match_rate_threshold]
                    if len(command_suggestions) == 1:
                        # コマンドの自動保管が有効なら提案コマンドをコマンドとする
                        if self.enable_auto_command_correction:
                            command = command_suggestions[0]
                        # そうでない場合は提案を返信する
                        else:
                            return False, "{}？もしかして{}の間違いかなぁ？".format(command, "「" + command_suggestions[0] + "」")
                    elif command_suggestions:
                        return False, "{}？もしかして{}のどれかの間違いかなぁ？".format(command, "、".join(["「" + command_sug + "」" for command_sug in command_suggestions]))
                    else:
                        return True, None
                else:
                    return True, None
            # 空の場合はコマンド実行しない
            else:
                return True, None

        command_func, command_authority = command_map[command]
        # 権限の確認
        user_authority = UserAuthority[command_source.user_data.authority]
        if not user_authority.check(command_authority):
            return False, "残念ながら権限がないよ。Youの権限：{}、コマンドの要求権限：{}。権限の変更はMasterユーザーに頼んでネ^_^".format(
                user_authority.name, command_authority.name)

        # コマンドの実行
        try:
            inspect.signature(command_func).bind(
                command_source, *command_param_list)
        except TypeError:
            sys.stderr.write(
                "コマンドの実行でエラーが発生。({})\n".format(sys.exc_info()[1]))
            return False, "コマンド引数の数が不正です。\n■「{}」コマンドの使い方\n{}".format(command, inspect.getdoc(command_func))
        reply, errors = command_func(
            command_source, *command_param_list)

        # 結果を返す
        if reply is None:
            errors.append("コマンド「{}」の実行に失敗しちゃった。。。".format(command))
        else:
            errors.append(reply)
        return False, "\n".join(errors)


class SystemMessageCommand(MessageCommandGroupBase):
    '''システムのメッセージコマンドグループ'''
    name = "システム"
    order = 0
    validate_in_initialize = True
    enable_command_suggestion = True
    enable_auto_command_correction = False
    suggestion_word_match_rate_threshold = 0.7


__command_group_order_map = {}
__command_group_list = {}


def get_ordered_valid_command_group_list():
    '''順番に並んだ有効なコマンドグループリストを取得する'''
    return [command_group for order, (is_valid, command_group) in sorted(__command_group_list.items(), key=lambda order_group: order_group[0]) if is_valid]


@SystemMessageCommand.add_command("使い方", UserAuthority.Watcher)
def help_command(command_source: CommandSource, target_command_name: str = None):
    '''使い方を表示します。コマンドの指定がない場合はコマンドの一覧を表示します。
    ■コマンド引数
    (1: 使い方を見たいコマンド名)'''
    # コマンドグループを優先度準に並び替える
    valid_command_group_list = get_ordered_valid_command_group_list()

    def generate_command_list_string():
        '''コマンドリスト文字列を生成'''
        result = '<コマンド一覧>'
        for command_group in valid_command_group_list:
            command_list = ["■{}(権限：{})".format(command_name, command_authority.name)
                            for command_name, (command_func, command_authority) in command_group.command_map().items()]
            result += "\n--{}コマンド--\n".format(command_group.name)
            result += "\n".join(command_list)
        return result

    # ターゲットが指定されていたらそのコマンドの詳細を表示
    if target_command_name:
        reply = None
        # コマンドグループの先頭から検索し、最初にヒットしたものを選ぶ
        for command_group in valid_command_group_list:
            if target_command_name in command_group.command_map():
                command_func, command_authority = command_group.command_map()[
                    target_command_name]
                reply = "<{}コマンド「{}」の使い方>\n■必要権限\n{}\n■説明\n{}".format(
                    command_group.name, target_command_name, command_authority.name, inspect.getdoc(command_func)), []
        if reply:
            return reply, []
        else:
            return "「{}」コマンドは存在しません。\n{}".format(target_command_name, generate_command_list_string()), []

    # 指定されていなかったらコマンドリストを表示
    else:
        reply = 'グループの場合は「#」を先頭に付けて、個人ラインの場合は何も付けずに、コマンドを指定して実行することができます。\n'
        reply += 'コマンドでない文字列を指定した場合はてきとうな返事を返します。'
        reply += 'また、「使い方」コマンドにコマンド名を指定することでそのコマンドの詳細説明を表示します。\n'
        reply += generate_command_list_string()
        return reply, []


def register_command_groups():
    '''コマンドグループを登録する'''
    command_groups = MessageCommandGroupBase.__subclasses__()
    for command_group_class in command_groups:
        command_group_order = command_group_class.order
        command_group_name = command_group_class.name
        __command_group_order_map[command_group_name] = command_group_order
        __command_group_list[command_group_order] = (
            command_group_class.validate_in_initialize, command_group_class())


def execute_message_command(command_name: str, command_source: CommandSource,  command_param_list: [str]):
    '''コマンドを実行する。戻り値は返信メッセージ。'''
    # コマンドグループを優先度準に並び替える
    valid_command_group_list = get_ordered_valid_command_group_list()

    for command_group in valid_command_group_list:
        # コマンド実行
        is_continue, reply = command_group.execute_command(
            command_name, command_source, command_param_list)
        # 続行しないなら最後の返信を返す
        if not is_continue:
            return reply
    # 最後まで来たらてきとうな返事を返す
    return generate_random_reply(command_name)
