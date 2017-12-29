'''権限に関するクラスなどを定義したファイル'''

from enum import Enum


class UserAuthority(Enum):
    '''ユーザー権限種類'''
    # 全ての操作が可能
    Master = 0
    # 編集が可能
    Editor = 1
    # 閲覧のみ可能
    Watcher = 2

    def check(self, required)->bool:
        '''権限が満たされているか確認'''
        return self.value <= required.value
