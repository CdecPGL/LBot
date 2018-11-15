
import discord

from bot.utilities import ServiceGroupKind
from lbot.authorities import UserAuthority
from lbot.exceptions import (GroupAlreadyExistError, GroupNotFoundError,
                             UserNotFoundError)

from ..models import DiscordUser, Group, ServiceGroup, User


def get_discord_fullname(discord_user: discord.User)->str:
    return f"{discord_user.name}#{discord_user.discriminator}"


def get_user_by_discord_user_id_from_database(discord_user_id: str)->User:
    '''DiscordのユーザーIDでデータベースからユーザーを取得する。ない場合は作成する'''
    try:
        return User.objects.get(discord_user__user_id__exact=discord_user_id)
    except User.DoesNotExist:
        raise UserNotFoundError(
            f"ユーザー(DiscordUserID: {discord_user_id})が見つかりませんでした。")


def get_group_by_discord_server_id_from_database(discord_server_id: str)->Group:
    '''DiscordサーバーIDでデータベースからグループを取得する'''
    try:
        return Group.objects.get(service_groups__kind__exact=ServiceGroupKind.DiscordServer.name, service_groups__id_in_service__exact=discord_server_id)
    except Group.DoesNotExist:
        raise GroupNotFoundError(
            f"グループ(DiscordServerID: {discord_server_id})が見つかりませんでした。")


def register_user_by_discord_user(discord_user: discord.User)->User:
    '''Discordユーザーでユーザーを登録する。戻り値は新しいユーザーデータ'''
    name = get_discord_fullname(discord_user)
    # Discordユーザーをデータベースに登録
    new_discord_user = DiscordUser.objects.create(
        user_id=discord_user.id, name=name)
    try:
        # ユーザをデータベースに登録
        counter = 1
        name_candidate = name
        # 重複がないように必要なら名前にインデックスを付ける
        while User.objects.filter(name=name_candidate).exists():
            name_candidate = name + str(counter)
            counter += 1
        new_user = User.objects.create(name=name_candidate, discord_user=new_discord_user,
                                       authority=UserAuthority.Watcher.name)
        print(
            f"ユーザー(DiscordID: {discord_user.id}, Name: {name})をデータベースに登録しました。")
        return new_user
    except Exception:
        new_discord_user.delete()
        raise


def register_user_by_discord_user_in_group(discord_user: discord.User, discord_server: discord.Server)->User:
    '''DiscordユーザーとDiscordサーバーでユーザーを登録する。
    Discordサーバーに紐付いたグループが作成されている必要があり、紐付いているグループにもユーザーが登録される。
    戻り値は新しいユーザーデータ。'''
    new_user = None
    new_discord_user = None
    try:
        name = get_discord_fullname(discord_user)
        # Discordユーザーをデータベースに登録
        new_discord_user = DiscordUser.objects.create(
            user_id=discord_user.id, name=name)
        # ユーザをデータベースに登録
        counter = 1
        name_candidate = name
        # 重複がないように必要なら名前にインデックスを付ける
        while User.objects.filter(name=name_candidate).exists():
            name_candidate = name + str(counter)
            counter += 1
        new_user = User.objects.create(name=name_candidate, discord_user=new_discord_user,
                                       authority=UserAuthority.Watcher.name)
        # グループにユーザーを登録
        group = get_group_by_discord_server_id_from_database(discord_server.id)
        group.members.add(new_user)
        group.save()
        print(
            f"ユーザー(DiscordID: {discord_user.id}, Name: {discord_user.name})をデータベースに登録しました。")
        return new_user
    except Exception:
        if new_discord_user:
            new_discord_user.delete()
        if new_user:
            new_user.delete()
        raise


def register_group_by_discord_server(discord_server: discord.Server)->Group:
    '''DiscordServerでグルうーぷを登録する。戻り値は新しいグループデータ。
    グループ名はグループ数から自動で「グループ**」と付けられる。'''
    # Discordグループをデータベースに登録
    if ServiceGroupKind.objects.filter(kind=ServiceGroupKind.DiscordServer.name, id_in_service=discord_server.id).exists():
        raise GroupAlreadyExistError(
            f"グループ(DiscordID: {discord_server.id})はすでにデータベースに登録されています。")
    else:
        new_service_group = ServiceGroupKind.objects.create(
            kind=ServiceGroupKind.DiscordServer.name, id_in_service=discord_server.id, name_in_service=discord_server.name)
    try:
        # ユーザをデータベースに登録
        total_group_count = Group.objects.count()
        # グループ名を自動で決定
        name_base = discord_server.name
        while Group.objects.filter(name=f"{name_base}{total_group_count}"):
            total_group_count += 1
        new_group = Group.objects.create(
            name=f"{name_base}{total_group_count}", discord_server=new_service_group)
        print(f"グループ(DiscordID: {discord_server.id})をデータベースに登録しました。")
        return new_group
    except Exception:
        new_service_group.delete()
        raise


def add_member_to_group_if_need(user: User, group: Group)->bool:
    '''ユーザーがグループに属しているか確認して、属していないなら登録する。
        戻り値は追加されたかどうか。'''
    if not group.members.filter(id=user.id).exists():
        print("ユーザー「{}」をグループ「{}」に登録。".format(user.name, group.name))
        group.members.add(user)
        group.save()
        return True
    else:
        return False
