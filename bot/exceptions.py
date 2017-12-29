'''例外クラス群'''


class UserNotFoundError(Exception):
    '''ユーザーが見つからなかった時の例外'''

    def __init__(self, message=""):
        super(UserNotFoundError, self).__init__()
        self.message = message


class GroupNotFoundError(Exception):
    '''グループが見つからなかった時の例外'''

    def __init__(self, message=""):
        super(GroupNotFoundError, self).__init__()
        self.message = message
