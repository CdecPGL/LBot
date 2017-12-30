'''LINE関連のUtility関数群'''

from bot.authorities import UserAuthority
from bot.exceptions import GroupNotFoundError, UserNotFoundError
from bot.line.line_settings import api as line_api
from bot.models import Group, LineGroup, LineUser, User


def get_user_by_line_user_id_from_database(line_user_id):
    '''LINEのユーザーIDでデータベースからユーザーを取得する。ない場合は作成する'''
    try:
        return User.objects.get(line_user__user_id__exact=line_user_id)
    except User.DoesNotExist:
        raise UserNotFoundError(
            "ユーザー(LineUserID: {})が見つかりませんでした。".format(line_user_id))


def get_group_by_line_group_id_from_database(line_group_id):
    '''LINEのグループIDでデータベースからグループを取得する'''
    try:
        return Group.objects.get(line_group__group_id__exact=line_group_id)
    except Group.DoesNotExist:
        raise GroupNotFoundError(
            "グループ(LineGroupID: {})が見つかりませんでした。".format(line_group_id))


def register_user_by_line_user_id(line_user_id):
    '''LINEユーザーIDでユーザーを登録する。戻り値は新しいユーザーデータ'''
    user_profile = line_api.get_profile(line_user_id)
    name = user_profile.display_name
    # LINEユーザーをデータベースに登録
    new_line_user = LineUser.objects.create(user_id=line_user_id, name=name)
    # ユーザをデータベースに登録
    new_user = User.objects.create(name=name, line_user=new_line_user,
                                   authority=UserAuthority.Watcher.name)
    print("ユーザー(LineID: {}, Name: {})をデータベースに登録しました。".format(line_user_id, name))
    return new_user


def register_group_by_line_group_id(line_group_id):
    '''LINEユーザーIDでユーザーを登録する。戻り値は新しいユーザーデータ。
    グループ名はグループ数から自動で「グループ**」と付けられる。'''
    # LINEグループをデータベースに登録
    new_line_group = LineGroup.objects.create(group_id=line_group_id)
    # ユーザをデータベースに登録
    total_group_count = Group.objects.count()
    # グループ名を自動で決定
    while Group.objects.filter(name="グループ{}".format(total_group_count)):
        total_group_count += 1
    new_group = Group.objects.create(name="グループ{}".format(
        total_group_count), line_group=new_line_group)
    print("グループ(LineID: {})をデータベースに登録しました。".format(line_group_id))
    return new_group
