import asyncio
import fcntl
import os
import re
import threading

import discord

_MENTION_REG = re.compile("<@([0-9]|!)+>")
_DISCORD_TOKEN_ENVIRONMENT_VAR_NAME = "LBOT_DISCORD_TOKEN"
_DISCORD_THREAD = None
_DISCORD_CLIENT_THREAD_NAME = "discord_client"
_DISCORD_CLIENT_START_LOCK_FILE = "discord_client_start_lock"


class LBotClient(discord.Client):
    async def on_ready(self):
        print('Discordにログインしました')

    async def on_message(self, message):
        # 送信元が自分でなく、宛先が自分なら返信する
        if self.user != message.author and self.user in message.mentions:
            print(message.content)
            reply = f'{message.author.mention}\n未実装……\n受信メッセージ：\n{self.remove_mentions_from_text(message.content)}'
            await self.send_message(message.channel, reply)

    @staticmethod
    def remove_mentions_from_text(text):
        '''テキストからメンション指定を取り除く'''
        res = ""
        for line in text.split("\n"):
            if not _MENTION_REG.match(line):
                res += line + "\n"
        res.strip("\n")
        return res


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
