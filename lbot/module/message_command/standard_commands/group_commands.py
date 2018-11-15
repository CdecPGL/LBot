'''グループ関連のメッセージコマンド'''

from bot.models import Group, User

from .... import database_utilities as db_util
from ....authorities import UserAuthority
from ....exceptions import GroupNotFoundError
from ..message_command import CommandSource
from .standard_command import StandardMessageCommandGroup


def check_group_edit_authority(user: User, group: Group):
    '''ユーザーにグループの編集権限があるかどうか。
    Masterユーザーかグループ管理者ならあるとみなす。'''
    return UserAuthority[user.authority] == UserAuthority.Master or group.managers.filter(id__exact=user.id).exists()


def check_group_watch_authority(user: User, group: Group):
    '''ユーザーにグループの閲覧権限があるかどうか。
    編集権限を持っているか、参加者であるならあるとみなす。'''
    if check_group_edit_authority(user, group):
        return True
    else:
        return group.members.filter(id=user.id).exists()


@StandardMessageCommandGroup.add_command("どこ", UserAuthority.Watcher)
def check_group_command(command_source: CommandSource, target_group_name: str = None):
    '''グループの情報を表示します。
    Master権限を持つユーザーか、グループの管理者と参加者のみ表示できます。
    グループからコマンドを実行した場合はそのグループの情報しか見られません。
    ■コマンド引数
    (1: 対象のグループ名。デフォルトは送信グループ)'''
    try:
        if target_group_name:
            # グループで指定グループが現在のグループでない場合は拒否
            if command_source.group_data and target_group_name != command_source.group_data.name:
                return None, ["グループ内では他のグループの情報を見ることはできません。"]
            else:
                group = db_util.get_group_by_name_from_database(
                    target_group_name)
        else:
            if command_source.group_data:
                group = command_source.group_data
            else:
                return "個人のトークルーム。", []

        if check_group_watch_authority(command_source.user_data, group):
            repply = "<グループ情報>\n"
            repply += "■グループ名\n{}\n".format(group.name)
            repply += "■LINEグループ\n{}\n".format(
                "あり" if group.line_group else "なし")
            repply += "■Asanaチーム\n{}\n".format(
                "あり" if group.asana_team else "なし")
            repply += "■Discordサーバー\n{}\n".format(
                "あり" if group.discord_server else "なし")
            repply += "■各種サービスのグループ：\n"
            for service_group in group.service_groups.all():
                reply += f"{service_group.name_in_service}({service_group.kind})\n"
            if group.members.exists():
                members_str = "、".join(
                    [member.name for member in group.members.all()])
            else:
                members_str = "なし"
            repply += "■メンバー\n{}".format(members_str)
            return repply, []
        else:
            return None, ["グループ「{}」の閲覧権限がない。Master権限を持つユーザーか、グループの管理者と参加者のみ表示できる。".format(target_group_name)]
    except GroupNotFoundError:
        return None, ["グループ「{}」が見つからない。".format(target_group_name)]


@StandardMessageCommandGroup.add_command("グループ名変更", UserAuthority.Editor)
def change_group_name_command(command_source: CommandSource, new_group_name: str)->(str, [str]):
    '''現在いるグループの名前を変更します。
    Masterユーザーかグループの管理者のみ変更可能です。
    グループ外での実行はできません。
    ■コマンド引数
    1: 新しいグループ名'''
    # グループが送信元か確認
    if not command_source.group_data:
        return None, ["このコマンドはグループ内でしか使えません。"]
    # 送信元のグループ名を変更
    group = command_source.group_data
    if check_group_edit_authority(command_source.user_data, group):
        if Group.objects.filter(name=new_group_name).exists():
            return None, ["グループ名「{}」はすでに存在するっ！".format(new_group_name)]
        else:
            old_group_name = group.name
            group.name = new_group_name
            group.save()
            return "グループ「{}」の名前を「{}」に変更しました。".format(old_group_name, new_group_name), []
    else:
        return None, ["グループ「{}」の変更権限がない！　グループの変更はMasterユーザーか管理者にしかできないっ！".format(group.name)]


# @StandardMessageCommandGroup.add_command("グループ統合", UserAuthority.Master)
# def integrate_group_command(command_source: CommandSource, target_group_name: str)->(str, [str]):
#     '''現在いるグループを他のグループに統合します。
#     Masterユーザーのみ実行可能です。
#     グループ外での実行はできません。
#     ■コマンド引数
#     1: 統合相手のグループ名'''
#     # グループが送信元か確認
#     if not command_source.group_data:
#         return None, ["このコマンドはグループ内でしか使えません。"]
#     return None, ["未実装"]


# グループ設定
'''グループ設定を変更します。
    Editor権限以上のユーザーでないとグループ管理者にはなれません。
    グループ管理者がいなくなるような変更は行えません。
    Masterユーザーかグループの管理者のみ変更可能です。'''
