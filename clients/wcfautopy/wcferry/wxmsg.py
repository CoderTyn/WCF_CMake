# -*- coding: utf-8 -*-

import re
from datetime import datetime
import time
from wcferry import wcf_pb2


class WxMsg(dict):
    """微信消息

    Attributes:
        type (int): 消息类型，可通过 `get_msg_types` 获取
        id (str): 消息 id
        xml (str): 消息 xml 部分
        sender (str): 消息发送人
        roomid (str): （仅群消息有）群 id
        content (str): 消息内容
        thumb (str): 视频或图片消息的缩略图路径
        extra (str): 视频或图片消息的路径
    """

    def __init__(self, msg: wcf_pb2.WxMsg) -> None:
        super(WxMsg, self).__init__()
        self._is_self = msg.is_self
        self._is_group = msg.is_group
        self._type = msg.type
        self._id = msg.id
        self._ts = msg.ts
        self._sign = msg.sign
        self._xml = msg.xml
        self._sender = msg.sender
        self._roomid = msg.roomid
        self._content = msg.content
        self._thumb = msg.thumb
        self._extra = msg.extra
        self.__data = {'isSelf': True if self._is_self else False,
                       'isGroup': True if self._is_group else False,
                       'isPyq': True if self._type == 0 else False,
                       'data': {
                           'type': self._type,
                           'content': self._content,
                           'sender': self._sender,
                           'msgid': self._id,
                           'roomid': self._roomid if self._roomid else None,
                           'xml': self._xml,
                           'thumb': self._thumb if self._thumb else None,
                           'extra': self._extra if self._extra else None,
                           'time': int(time.time() * 1000),
                       }, 'revokmsgid': None, 'isRevokeMsg': False, }
        self.__revokmsg_p()

    def __revokmsg_p(self):
        rmsg = self.__data['data']['content']
        rev_type = re.findall('<sysmsg type="(.*?)"\s?', rmsg)
        rev_w = re.findall("<replacemsg><!\[CDATA\[(.*?)]]></replacemsg>", rmsg)
        if len(rev_type) == 0 or len(rev_w) == 0: return
        if rev_type[0] == 'revokemsg' and rev_w[0] == '你撤回了一条消息':
            self.__data['data']['content'] = rev_w[0]
            self.__data['isRevokeMsg'] = True
            self.__data['revokmsgid'] = re.findall('<newmsgid>(.*?)</newmsgid>', rmsg)[0]

    def __str__(self) -> str:
        return repr(self.__data)

    def __repr__(self) -> str:
        return repr(self.__data)

    def __getitem__(self, key):
        return self.__data[key]

    def __getattr__(self, item):
        if item in ['content', 'sender', 'roomid', 'xml', 'thumb', 'extra', 'type']:
            return self.__data['data'][item]
        if item == 'id':
            return self.__data['data']['msgid']
        if item == 'ts':
            return self._ts
        if item == 'sign':
            return self._sign

    def __setitem__(self, key, value):
        self.__data[key] = value

    def is_image(self) -> bool:
        """是否是图片"""
        return self.type == 3 and ('imgdatahash' in self.__data['data']['content'])

    def is_voice(self) -> bool:
        """是否是语音"""
        return self.type == 34 and ('voicemsg' in self.__data['data']['content'])

    def is_video(self) -> bool:
        """是否是视频"""
        return self.type == 43 and ('videomsg' in self.__data['data']['content'])

    def is_pyq(self) -> bool:
        return self.type == 0

    def from_self(self) -> bool:
        """是否自己发的消息"""
        return self._is_self == 1

    def from_group(self) -> bool:
        """是否群聊消息"""
        return self._is_group

    def is_at(self, wxid) -> bool:
        """是否被 @：群消息，在 @ 名单里，并且不是 @ 所有人"""
        if not self.from_group():
            return False  # 只有群消息才能 @

        if not re.findall(f"<atuserlist>.*({wxid}).*</atuserlist>", self.xml):
            return False  # 不在 @ 清单里

        if re.findall(r"@(?:所有人|all|All)", self.content):
            return False  # 排除 @ 所有人

        return True

    def is_text(self) -> bool:
        """是否文本消息"""
        return self.type == 1
