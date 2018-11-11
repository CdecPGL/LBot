from ..message_command import CommandSource, execute_message_command

_SENTENCE_MAX_LENGTH = 64


def analyse_message_and_execute_command(message_text, source_user, source_group):
    '''メッセージを解析してコマンドを実行する。

    return: (成否,返信メッセージ)。返信がない場合はNone
    exceptions: MessageAnalysisError
    '''
    # コマンドとパラメータの抽出
    command = None
    params = []
    if message_text:
        # 左右の空白は取り除く
        items = [item.strip() for item in message_text.split("\n")]
        # 文字列の長さが規定値を超えていたらリジェクト
        if any([len(item) > _SENTENCE_MAX_LENGTH for item in items]):
            return False, "長文は受け付けません(´ε｀ )"
        # コマンド文字列が空だったらリジェクト
        if not items or not items[0]:
            return "もうちょっと喋って？"
        command = items[0]
        if len(items) > 1:
            params = items[1:]
    # コマンドを実行し返信を送信。コマンドがない(自分宛てのメッセージではない)場合は返信しない
    reply = None
    if command:
        # コマンド実行
        command_source = CommandSource(source_user, source_group)
        reply = execute_message_command(
            command, command_source, params)
        # グループの時は宛先を表示
        if source_group:
            reply = "@{}\n{}".format(source_user.name, reply)
    return True, reply
