import discord
import re
import threading
import asyncio
import os

_MENTION_REG = re.compile("<@([0-9]|!)+>")
_DISCORD_TOKEN_ENVIRONMENT_VAR_NAME = "LBOT_DISCORD_TOKEN"
_DISCORD_THREAD = None


class LBotClient(discord.Client):
    async def on_ready(self):
        print('ログインしました')

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
        token = os.environ()[_DISCORD_TOKEN_ENVIRONMENT_VAR_NAME]
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


def start_client_in_other_thread():
    _DISCORD_THREAD = threading.Thread(target=run_client)
    _DISCORD_THREAD.start()

# def stop_client():
#     if _DISCORD_THREAD:
#         _DISCORD_THREAD.join()
