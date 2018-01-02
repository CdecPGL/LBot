'''ユーザー関連のメッセージコマンド'''

import bot.database_utilities as db_util
from bot.authorities import UserAuthority
from bot.exceptions import UserNotFoundError
from bot.models import User

from ..message_command import CommandSource
from .standard_command import StandardMessageCommandGroup


@StandardMessageCommandGroup.add_command("ユーザー名変更", UserAuthority.Editor)
def change_user_name_command(command_source: CommandSource, target_user_name: str, new_user_name: str):
    '''ユーザーの詳細を表示します。
    Master権限を持つユーザーか、本人のみ実行できます。
    ■コマンド引数
    1: 対象ユーザー名
    2: 新しいユーザー名'''
    if command_source.user_data.name == target_user_name:
        target_user = command_source.user_data
    elif UserAuthority[command_source.user_data.authority] == UserAuthority.Master:
        target_user = db_util.get_user_by_name_from_database(target_user_name)
    else:
        return None, ["ユーザ名は本人かMasterユーザーにしか変更できないんだよね。"]
    if User.objects.filter(name=new_user_name).exists():
        return None, ["ユーザー名「{}」は別の人が使ってるよ".format(new_user_name)]
    target_user.name = new_user_name
    target_user.save()
    return "ユーザー「{}」の名前を「{}」に変更しましたよ。".format(target_user_name, new_user_name), []


@StandardMessageCommandGroup.add_command("だれ", UserAuthority.Watcher)
def check_user_command(command_source: CommandSource, target_user_name: str = None):
    '''ユーザーの情報を表示します。
    Master権限を持つユーザーか、本人のみ表示できます。
    コマンド引数
    (1: 対象のユーザー名。デフォルトは送信者)'''
    try:
        if target_user_name:
            user = db_util.get_user_by_name_from_database(target_user_name)
        else:
            user = command_source.user_data
            target_user_name = command_source.user_data.name
        # 権限確認(エラーメッセージの表示優先度的にここでチェックする)
        if command_source.user_data.name != target_user_name and UserAuthority[command_source.user_data.authority] != UserAuthority.Master:
            return None, ["ユーザ情報は本人かMasterユーザーにしか表示できないんだよね。"]
        repply = "<ユーザー情報>\n"
        repply += "■ユーザー名\n{}\n".format(user.name)
        repply += "■権限\n{}\n".format(user.authority)
        repply += "■LINEユーザー\n{}\n".format(
            user.line_user.name if user.line_user else "なし")
        repply += "■Asanaユーザー\n{}\n".format(
            user.asana_user.name if user.asana_user else "なし")
        # 管理グループ
        if user.managing_groups.exists():
            managing_groups_str = "、".join(
                [group.name for group in user.managing_groups.all()])
        else:
            managing_groups_str = "なし"
        repply += "■管理グループ\n{}\n".format(managing_groups_str)
        # 管理タスク
        if user.managing_tasks.exists():
            managing_tasks_str = "、".join(
                [task.name for task in user.managing_tasks.all()])
        else:
            managing_tasks_str = "なし"
        repply += "■管理タスク\n{}\n".format(managing_tasks_str)
        # 参加グループ
        if user.belonging_groups.exists():
            belonging_groups_str = "、".join(
                [group.name for group in user.belonging_groups.all()])
        else:
            belonging_groups_str = "なし"
        repply += "■参加グループ\n{}\n".format(belonging_groups_str)
        # 参加タスク
        if user.belonging_tasks.exists():
            belonging_tasks_str = "、".join(
                [task.name for task in user.belonging_tasks.all()])
        else:
            belonging_tasks_str = "なし"
        repply += "■参加タスク\n{}".format(belonging_tasks_str)
        return repply, []
    except UserNotFoundError:
        return None, ["ユーザー「{}」はいないっぽい。".format(target_user_name)]


@StandardMessageCommandGroup.add_command("ユーザー権限変更", UserAuthority.Master)
def change_user_authority_command(command_source: CommandSource, target_user_name: str, target_authority: str):
    '''ユーザーの権限を変更します。
    Master権限を持つユーザーがいなくなるような変更は行えません。
    管理しているタスクかグループがあるユーザーをWatcher権限にすることはできません。
    ■コマンド引数
    1: 対象のユーザー名
    2: 権限。「Master」、「Editor」、「Watcher」のいずれか'''
    try:
        user = db_util.get_user_by_name_from_database(target_user_name)
        try:
            current_authority = UserAuthority[user.authority]
            target_authority = UserAuthority[target_authority]
        except KeyError:
            return None, ["指定された権限「{}」は存在しないよ。".format(target_authority)]
        # 変更の必要があるか確認
        if current_authority == target_authority:
            return "変更は必要ないよ。", []
        # Masterユーザーの数を確認
        if current_authority == UserAuthority.Master:
            if User.objects.filter(authority__exact=UserAuthority.Master.name).count() == 1:
                return None, ["Masterユーザーがいなくなっちゃうよ。"]
        # 管理タスクとグループの確認
        if target_authority == UserAuthority.Watcher:
            if user.managing_tasks.exists():
                return [None, "ユーザー「{}」には管理しているタスクがあるので「{}」権限には変更できないよ。".format(target_user_name, UserAuthority.Watcher.name)]
            if user.managing_groups.exists():
                return [None, "ユーザー「{}」には管理しているグループがあるので「{}」権限には変更できないよ。".format(target_user_name, UserAuthority.Watcher.name)]
        # 権限変更
        user.authority = target_authority.name
        user.save()
        return "ユーザー「{}」の権限を「{}」から「{}」に変更したよ。".format(target_user_name, current_authority.name, target_authority.name), []
    except UserNotFoundError:
        return None, ["指定されたユーザー「{}」はいないよ。".format(target_user_name)]
