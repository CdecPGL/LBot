import asyncio
import fcntl
import os
import re
import threading
import traceback

import discord

from lbot.exceptions import GroupNotFoundError, UserNotFoundError
from lbot.module.message_analysis import analyse_message_and_execute_command

from . import utilities as discord_utils

_MENTION_REG = re.compile("<@([0-9]|!)+>")
_DISCORD_TOKEN_ENVIRONMENT_VAR_NAME = "LBOT_DISCORD_TOKEN"
_DISCORD_THREAD = None
_DISCORD_CLIENT_THREAD_NAME = "discord_client"
_DISCORD_CLIENT_START_LOCK_FILE = "discord_client_start_lock"


class LBotClient(discord.Client):
    async def on_ready(self):
        print('Discordにログインしました')

    async def on_message(self, message):
        if self.is_replyable_message(message):
            log = f"送信者：{message.author}\n"
            log += f"サーバー：{message.server}\n"
            log += f"チャンネル：{message.channel}\n"
            log += f"内容：{self.remove_mentions_from_text(message.content)}\n"
            print(f"<Discordでメッセージを受信>\n{log}")

            sender = message.author
            server = message.server
            channel = message.channel

            # メッセージ送信グループをデータベースから検索し、なかったら作成
            try:
                try:
                    source_group = discord_utils.get_group_by_discord_server_id_from_database(
                        server.id)
                except GroupNotFoundError:
                    source_group = discord_utils.register_group_by_discord_server(
                        server)
                # メッセージ送信者をデータベースから検索し、なかったら作成
                try:
                    source_user = discord_utils.get_user_by_discord_user_id_from_database(
                        sender.id)
                    # グループへメンバーが登録されているか確認し必要なら登録
                    if source_group:
                        if discord_utils.add_member_to_group_if_need(source_user, source_group):
                            # メンバーの追加を通知
                            await self.send_message(
                                channel, f"このグループ「{source_group.name}」にユーザー「{source_user.name}」を追加しました。")
                except UserNotFoundError:
                    if source_group:
                        source_user = discord_utils.register_user_by_discord_user_in_group(
                            sender, server)
                        # メンバーの追加を通知
                        await self.send_message(
                            channel, f"このグループ「{source_group.name}」にユーザー「{source_user.name}」を追加しました。")
                    else:
                        source_user = discord_utils.register_user_by_discord_user(
                            sender)
                        # ユーザーの登録を通知
                        await self.send_message(
                            channel, f"「{source_user.name}」をユーザー登録しました。")
                # メッセージ解析とコマンド実行、その返信を行う
                cleaned_message = self.remove_mentions_from_text(
                    message.content)
                cleaned_message = cleaned_message.strip()
                if cleaned_message:
                    is_success, reply = analyse_message_and_execute_command(
                        cleaned_message, source_user, source_group)
                else:
                    reply = "なんか言って"
                if reply:
                    await self.send_message(channel, f"{sender.mention}\n{reply}")
            except Exception as e:
                traceback.print_exc()
                try:
                    await self.send_message(
                        channel, f"内部で未処理のエラーが発生。詳細はログを見てね☆\n{e}")
                except:
                    pass
                raise e

    def is_replyable_message(self, message):
        '''返信可能なメッセージかどうか'''
        if self.user == message.author:
            return False
        elif self.user not in message.mentions:
            return False
        elif message.channel.is_private:
            return False
        elif message.type != discord.MessageType.default:
            return False
        else:
            return True

    @staticmethod
    def remove_mentions_from_text(text):
        '''テキストからメンション指定を取り除く'''
        res = ""
        for line in text.split("\n"):
            if not _MENTION_REG.match(line):
                res += line + "\n"
        res.strip("\n")
        return res

    @staticmethod
    def update_members():
        pass


def run_client(dont_use_default_pool=False):
    try:
        token = os.environ[_DISCORD_TOKEN_ENVIRONMENT_VAR_NAME]
    except KeyError:
        print(
            f'環境変数"{_DISCORD_TOKEN_ENVIRONMENT_VAR_NAME}"が設定されていないため、Discord関連の機能は無効になります。')
        return
    # メインスレッド以外では標準のイベントループが用意されないようなので新しく作成する
    if dont_use_default_pool:
        client = LBotClient(loop=asyncio.new_event_loop())
    else:
        client = LBotClient()
    client.run(token)


def is_discord_client_running():
    '''Discordクライアントが実行されているかどうか'''
    return any([t.is_alive() and t.name == _DISCORD_CLIENT_THREAD_NAME for t in threading.enumerate()])


def start_client_in_other_thread():
    '''別スレッドでDiscordクライアントを開始する。
    同一プロセス内ですでに開始されている場合は何もしない。別プロセスで開始されている場合は新たなクライアントが開始される。'''
    # Djangoの複数プロセスから同時に呼ばれた場合に同時に実行されるのを防ぐために、ファイルによる排他ロックを行う
    with open(_DISCORD_CLIENT_START_LOCK_FILE, "w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        if is_discord_client_running():
            print("すでにDiscordクライアントが実行中のため、新たなクライアントを開始しませんでした。")
        else:
            _DISCORD_THREAD = threading.Thread(
                target=run_client, args=[True], name=_DISCORD_CLIENT_THREAD_NAME)
            _DISCORD_THREAD.start()
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
