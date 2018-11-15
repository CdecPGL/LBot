'''LINE関連のUtility関数群'''

from bot.utilities import ServiceGroupKind, ServiceUserKind
from lbot.authorities import UserAuthority
from lbot.exceptions import (GroupAlreadyExistError, GroupNotFoundError,
                             UserNotFoundError)

from ..models import Group, ServiceGroup, ServiceUser, User
from .settings import api as line_api


def get_user_by_line_user_id_from_database(line_user_id: str)->User:
    '''LINEのユーザーIDでデータベースからユーザーを取得する。ない場合は作成する'''
    try:
        return User.objects.get(service_users__id_in_service__exact=line_user_id)
    except User.DoesNotExist:
        raise UserNotFoundError(
            "ユーザー(LineUserID: {})が見つかりませんでした。".format(line_user_id))


def get_group_by_line_group_id_from_database(line_group_id: str)->Group:
    '''LINEのグループIDでデータベースからグループを取得する'''
    try:
        return Group.objects.get(service_groups__id_in_service__exact=line_group_id)
    except Group.DoesNotExist:
        raise GroupNotFoundError(
            "グループ(LineGroupID: {})が見つかりませんでした。".format(line_group_id))


def register_user_by_line_user_id(line_user_id: str)->User:
    '''LINEユーザーIDでユーザーを登録する。戻り値は新しいユーザーデータ'''
    user_profile = line_api.get_profile(line_user_id)
    name = user_profile.display_name
    # LINEユーザーをデータベースに登録
    new_service_user = ServiceUser.objects.create(
        id_in_service=line_user_id, name_in_service=name)
    try:
        # ユーザをデータベースに登録
        counter = 1
        name_candidate = name
        # 重複がないように必要なら名前にインデックスを付ける
        while User.objects.filter(name=name_candidate).exists():
            name_candidate = name + str(counter)
            counter += 1
        new_user = User.objects.create(
            name=name_candidate, authority=UserAuthority.Watcher.name)
        new_service_user.belonging_user = new_user
        new_service_user.save()
        print("ユーザー(LineID: {}, Name: {})をデータベースに登録しました。".format(line_user_id, name))
        return new_user
    except Exception:
        new_service_user.delete()
        raise


def register_user_by_line_user_id_in_group(line_user_id: str, line_group_id: str)->User:
    '''LINEユーザーIDとLINEグループIDででユーザーを登録する。
    LINEIDに紐付いたグループが作成されている必要があり、紐付いているグループにもユーザーが登録される。
    戻り値は新しいユーザーデータ。'''
    new_user = None
    new_service_user = None
    try:
        user_profile = line_api.get_group_member_profile(
            line_group_id, line_user_id)
        name = user_profile.display_name
        # LINEユーザーをデータベースに登録
        new_service_user = ServiceUser.objects.create(
            id_in_service=line_user_id, name_in_service=name)
        # ユーザをデータベースに登録
        counter = 1
        name_candidate = name
        # 重複がないように必要なら名前にインデックスを付ける
        while User.objects.filter(name=name_candidate).exists():
            name_candidate = name + str(counter)
            counter += 1
        new_user = User.objects.create(
            name=name_candidate, authority=UserAuthority.Watcher.name)
        new_service_user.belonging_user = new_user
        new_service_user.save()
        # グループにユーザーを登録
        group = get_group_by_line_group_id_from_database(line_group_id)
        group.members.add(new_user)
        group.save()
        print("ユーザー(LineID: {}, Name: {})をデータベースに登録しました。".format(line_user_id, name))
        return new_user
    except Exception:
        if new_service_user:
            new_service_user.delete()
        if new_user:
            new_user.delete()
        raise


def register_group_by_line_group_id(line_group_id: str)->Group:
    '''LINEユーザーIDでグループを登録する。戻り値は新しいグループデータ。
    グループ名はグループ数から自動で「グループ**」と付けられる。'''
    # LINEグループをデータベースに登録
    if ServiceGroupKind.objects.filter(kind=ServiceGroupKind.LINEGroup.name, id_in_service=line_group_id).exists():
        raise GroupAlreadyExistError(
            f"グループ(LINEGroupID: {discord_server.id})はすでにデータベースに登録されています。")
    else:
        new_service_group = ServiceGroupKind.objects.create(
            kind=ServiceGroupKind.LINEGroup.name, id_in_service=line_group_id, name_in_service="不明")
    try:
        # ユーザをデータベースに登録
        total_group_count = Group.objects.count()
        # グループ名を自動で決定
        while Group.objects.filter(name="グループ{}".format(total_group_count)):
            total_group_count += 1
        new_group = Group.objects.create(name="グループ{}".format(
            total_group_count))
        new_service_group.belonging_group = new_group
        new_service_group.save()
        print("グループ(LineID: {})をデータベースに登録しました。".format(line_group_id))
        return new_group
    except Exception:
        new_service_group.delete()
        raise


def add_member_to_group_if_need(user: User, group: Group)->bool:
    '''ユーザーがグループに属している確認して、属していないなら登録する。
        戻り値は追加されたかどうか。'''
    if not group.members.filter(id=user.id).exists():
        print("ユーザー「{}」をグループ「{}」に登録。".format(user.name, group.name))
        group.members.add(user)
        group.save()
        return True
    else:
        return False
