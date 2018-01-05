'''LINE関連のUtility関数群'''

from ..authorities import UserAuthority
from ..exceptions import GroupNotFoundError, UserNotFoundError
from ..models import Group, LineGroup, LineUser, User
from .line_settings import api as line_api


def get_user_by_line_user_id_from_database(line_user_id: str)->User:
    '''LINEのユーザーIDでデータベースからユーザーを取得する。ない場合は作成する'''
    try:
        return User.objects.get(line_user__user_id__exact=line_user_id)
    except User.DoesNotExist:
        raise UserNotFoundError(
            "ユーザー(LineUserID: {})が見つかりませんでした。".format(line_user_id))


def get_group_by_line_group_id_from_database(line_group_id: str)->Group:
    '''LINEのグループIDでデータベースからグループを取得する'''
    try:
        return Group.objects.get(line_group__group_id__exact=line_group_id)
    except Group.DoesNotExist:
        raise GroupNotFoundError(
            "グループ(LineGroupID: {})が見つかりませんでした。".format(line_group_id))


def register_user_by_line_user_id(line_user_id: str)->User:
    '''LINEユーザーIDでユーザーを登録する。戻り値は新しいユーザーデータ'''
    user_profile = line_api.get_profile(line_user_id)
    name = user_profile.display_name
    # LINEユーザーをデータベースに登録
    new_line_user = LineUser.objects.create(user_id=line_user_id, name=name)
    try:
        # ユーザをデータベースに登録
        counter = 1
        name_candidate = name
        # 重複がないように必要なら名前にインデックスを付ける
        while User.objects.filter(name=name_candidate).exists():
            name_candidate = name + str(counter)
            counter += 1
        new_user = User.objects.create(name=name_candidate, line_user=new_line_user,
                                       authority=UserAuthority.Watcher.name)
        print("ユーザー(LineID: {}, Name: {})をデータベースに登録しました。".format(line_user_id, name))
        return new_user
    except Exception:
        new_line_user.delete()
        raise


def register_user_by_line_user_id_in_group(line_user_id: str, line_group_id: str)->User:
    '''LINEユーザーIDとLINEグループIDででユーザーを登録する。
    LINEIDに紐付いたグループが作成されている必要があり、紐付いているグループにもユーザーが登録される。
    戻り値は新しいユーザーデータ。'''
    new_user = None
    new_line_user = None
    try:
        user_profile = line_api.get_group_member_profile(
            line_group_id, line_user_id)
        name = user_profile.display_name
        # LINEユーザーをデータベースに登録
        new_line_user = LineUser.objects.create(
            user_id=line_user_id, name=name)
        # ユーザをデータベースに登録
        counter = 1
        name_candidate = name
        # 重複がないように必要なら名前にインデックスを付ける
        while User.objects.filter(name=name_candidate).exists():
            name_candidate = name + str(counter)
            counter += 1
        new_user = User.objects.create(name=name_candidate, line_user=new_line_user,
                                       authority=UserAuthority.Watcher.name)
        # グループにユーザーを登録
        group = get_group_by_line_group_id_from_database(line_group_id)
        group.members.add(new_user)
        group.save()
        print("ユーザー(LineID: {}, Name: {})をデータベースに登録しました。".format(line_user_id, name))
        return new_user
    except Exception:
        if new_line_user:
            new_line_user.delete()
        if new_line_user:
            new_user.delete()
        raise


def register_group_by_line_group_id(line_group_id: str)->Group:
    '''LINEユーザーIDでユーザーを登録する。戻り値は新しいユーザーデータ。
    グループ名はグループ数から自動で「グループ**」と付けられる。'''
    # LINEグループをデータベースに登録
    new_line_group = LineGroup.objects.create(group_id=line_group_id)
    try:
        # ユーザをデータベースに登録
        total_group_count = Group.objects.count()
        # グループ名を自動で決定
        while Group.objects.filter(name="グループ{}".format(total_group_count)):
            total_group_count += 1
        new_group = Group.objects.create(name="グループ{}".format(
            total_group_count), line_group=new_line_group)
        print("グループ(LineID: {})をデータベースに登録しました。".format(line_group_id))
        return new_group
    except Exception:
        new_line_group.delete()
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
