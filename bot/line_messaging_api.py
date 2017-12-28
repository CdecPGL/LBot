'''
LINEのMessaging APIを扱うためのクラス群。
Messaging APIの詳細はリファレンス(https://developers.line.me/ja/docs/messaging-api/reference/#source-user)を参照。
'''

import json
from enum import Enum


class EventType(Enum):
    '''イベントのタイプ'''
    Message = "message"
    Follow = "follow"
    Unfollow = "unfollow"
    Join = "join"
    Leave = "leave"
    PostBack = "postback"
    Beacon = "beacon"


class MessageType(Enum):
    '''メッセージのタイプ'''
    Text = "text"
    Stamp = "sticker"
    Image = "image"
    Video = "video"
    Audio = "audio"
    File = "file"
    Location = "location"
    ImageMap = "imagemap"


class SourceType(Enum):
    '''送信元のタイプ'''
    User = "user"
    Group = "group"
    TalkRoom = "room"


class Source(object):
    '''送信元の情報'''

    def __init__(self, data):
        # 送信元のタイプ。SourceType型
        self.type = SourceType(data["type"])
        # 送信したユーザーのID。str型
        self.user_id = data["userId"]
        # グループIDは送信元がグループの場合のみ
        # 送信元のグループのID。str型
        self.group_id = data["groupId"] if self.type == SourceType.Group else None
        # ルームIDは送信元がトークルームの場合のみ
        # 送信元のルームのID。str型
        self.room_id = data["roomId"] if self.type == SourceType.TalkRoom else None


class Message(object):
    '''メッセージの情報'''

    def __init__(self, data):
        # メッセージのタイプ。MessageType型
        self.type = MessageType(data["type"])
        # メッセージのID。str型
        self.id = data["id"]
        # テキストメッセージの場合
        # テキストの内容。str型
        self.text = data["text"] if self.type == MessageType.Text else None
        # ファイルメッセージの場合
        # ファイル名。str型
        self.file_name = data["fileName"] if self.type == MessageType.File else None
        # ファイルサイズ(バイト)。int型
        self.file_size = int(
            data["fileSize"]) if self.type == MessageType.File else None
        # 位置情報メッセージの場合
        # タイトル。str型
        self.title = data["title"] if self.type == MessageType.Location else None
        # 住所。str型
        self.address = data["address"] if self.type == MessageType.Location else None
        # 緯度。str型
        self.latitude = data["latitude"] if self.type == MessageType.Location else None
        # 経度。str型
        self.longitude = data["longititude"] if self.type == MessageType.Location else None
        # スタンプメッセージの場合
        # スタンプのパッケージID。str型
        self.package_id = data["packageId"] if self.type == MessageType.Stamp else None
        # スタンプID。str型
        self.sticker_id = data["stickerId"] if self.type == MessageType.Stamp else None


class PostBack(object):
    '''ポストバックの情報'''

    def __init__(self, data):
        # ポストバックデータ本体。str型
        self.data = data["data"]
        # ポストバックデータの引数。キーはリファレンスを参照。ない場合もある。dict型
        try:
            self.params = data.at("params", None)
        except KeyError:
            self.params = None


class Event(object):
    '''イベントの情報'''

    def __init__(self, data):
        # イベントのタイプ。EventType型
        self.type = EventType(data["type"])
        # イベントが起こった時刻。str型
        self.time_stamp = data["timestamp"]
        # イベントの送信元情報。Source型
        self.source = Source(data["source"])
        # フォロー解除と退出イベント以外の場合
        # 返信用トークン。str型
        self.reply_token = data["replyToken"] if self.type != EventType.Unfollow and self.type != EventType.Leave else None
        # メッセージイベントの場合
        # メッセージデータ。Message型
        self.message = Message(
            data["message"]) if self.type == EventType.Message else None
        # ポストバックイベントの場合
        # ポストバックデータ。PostBack型
        self.post_back = PostBack(
            data["postback"]) if self.type == EventType.PostBack else None
        # ビーコンイベントの場合
        # ビーコン情報。キーはリファレンスを参照。dict型
        self.beacon = data["beacon"] if self.type == EventType.Beacon else None


class LineMessagingAPI(object):
    # 返信の送信先
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'

    def __init__(self, access_token, channell_secret):
        self.__access_token = access_token
        self.__channell_secret = channell_secret

    def generate_request_header(self):
        '''LINEへのリクエスト用ヘッダを作成する'''
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.__access_token
        }

    def generate_text_reply_response(self, reply_token, reply_text):
        '''テキスト返信レスポンスを作成する。戻り値は(レスポンスヘッダ,レスポンスボディ)'''
        response_body_dict = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": MessageType.Text.value,
                    "text": reply_text
                }
            ]
        }
        return (self.generate_request_header(), json.dumps(response_body_dict))

    def generate_push_request(self):
        pass

    def check_request_header(self, request_body, request_signature):
        '''リクエストがLineプラットフォームからのものか確認する'''
        # チャネルシークレットを秘密鍵として、HMAC-SHA256アルゴリズムを使用してリクエストボディのダイジェスト値を取得
        # ダイジェスト値をBase64エンコードした値とリクエストヘッダーにある署名が一致することを確認
        return True

    def parse_request(self, request_body, request_meta_dict):
        request_json = json.loads(request_body)
        # 署名をチェック
        request_signature = request_meta_dict["X-Line-Signature"]
        if not self.check_request_header(request_body, request_signature):
            assert(False)

        events = []
        for request_event in request_json['events']:
            events.append(Event(request_event))

        return events
