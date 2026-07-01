#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Tencent official WeCom callback crypto (Python 3 port, vendored).

Source: sbzhu/weworkapi_python (Tencent official sample), Python 3 adaptation.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import random
import socket
import struct
import time
import xml.etree.ElementTree as ET
from Crypto.Cipher import AES

from services.fiqa_api.wecom.crypto import ierror

logger = logging.getLogger(__name__)


class FormatException(Exception):
    pass


def throw_exception(message: str, exception_class: type[Exception] = FormatException) -> None:
    raise exception_class(message)


class SHA1:
    """Compute WeCom message signatures."""

    def getSHA1(self, token, timestamp, nonce, encrypt):
        try:
            sortlist = [token, timestamp, nonce, encrypt]
            sortlist.sort()
            sha = hashlib.sha1()
            sha.update("".join(sortlist).encode())
            return ierror.WXBizMsgCrypt_OK, sha.hexdigest()
        except Exception as exc:
            logger.error("wecom_sha1_error_v1 error=%s", exc)
            return ierror.WXBizMsgCrypt_ComputeSignature_Error, None


class XMLParse:
    AES_TEXT_RESPONSE_TEMPLATE = """<xml>
<Encrypt><![CDATA[%(msg_encrypt)s]]></Encrypt>
<MsgSignature><![CDATA[%(msg_signaturet)s]]></MsgSignature>
<TimeStamp>%(timestamp)s</TimeStamp>
<Nonce><![CDATA[%(nonce)s]]></Nonce>
</xml>"""

    def extract(self, xmltext):
        try:
            xml_tree = ET.fromstring(xmltext)
            encrypt = xml_tree.find("Encrypt")
            return ierror.WXBizMsgCrypt_OK, encrypt.text
        except Exception as exc:
            logger.error("wecom_xml_extract_error_v1 error=%s", exc)
            return ierror.WXBizMsgCrypt_ParseXml_Error, None

    def generate(self, encrypt, signature, timestamp, nonce):
        resp_dict = {
            "msg_encrypt": encrypt,
            "msg_signaturet": signature,
            "timestamp": timestamp,
            "nonce": nonce,
        }
        return self.AES_TEXT_RESPONSE_TEMPLATE % resp_dict


class PKCS7Encoder:
    block_size = 32

    def encode(self, text):
        text_length = len(text)
        amount_to_pad = self.block_size - (text_length % self.block_size)
        if amount_to_pad == 0:
            amount_to_pad = self.block_size
        pad = chr(amount_to_pad)
        return text + (pad * amount_to_pad).encode()

    def decode(self, decrypted):
        pad = ord(decrypted[-1])
        if pad < 1 or pad > 32:
            pad = 0
        return decrypted[:-pad]


class Prpcrypt:
    def __init__(self, key):
        self.key = key
        self.mode = AES.MODE_CBC

    def encrypt(self, text, receiveid):
        text = text.encode()
        text = self.get_random_str() + struct.pack("I", socket.htonl(len(text))) + text + receiveid.encode()
        pkcs7 = PKCS7Encoder()
        text = pkcs7.encode(text)
        cryptor = AES.new(self.key, self.mode, self.key[:16])
        try:
            ciphertext = cryptor.encrypt(text)
            return ierror.WXBizMsgCrypt_OK, base64.b64encode(ciphertext)
        except Exception as exc:
            logger.error("wecom_encrypt_aes_error_v1 error=%s", exc)
            return ierror.WXBizMsgCrypt_EncryptAES_Error, None

    def decrypt(self, text, receiveid):
        try:
            cryptor = AES.new(self.key, self.mode, self.key[:16])
            plain_text = cryptor.decrypt(base64.b64decode(text))
        except Exception as exc:
            logger.error("wecom_decrypt_aes_error_v1 error=%s", exc)
            return ierror.WXBizMsgCrypt_DecryptAES_Error, None
        try:
            pad = plain_text[-1]
            content = plain_text[16:-pad]
            xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
            xml_content = content[4 : xml_len + 4]
            from_receiveid = content[xml_len + 4 :]
        except Exception as exc:
            logger.error("wecom_decrypt_buffer_error_v1 error=%s", exc)
            return ierror.WXBizMsgCrypt_IllegalBuffer, None

        if from_receiveid.decode("utf8") != receiveid:
            return ierror.WXBizMsgCrypt_ValidateCorpid_Error, None
        return 0, xml_content

    def get_random_str(self):
        return str(random.randint(1000000000000000, 9999999999999999)).encode()


class WXBizMsgCrypt:
    def __init__(self, sToken, sEncodingAESKey, sReceiveId):
        try:
            self.key = base64.b64decode(sEncodingAESKey + "=")
            assert len(self.key) == 32
        except Exception:
            throw_exception("[error]: EncodingAESKey unvalid !", FormatException)
        self.m_sToken = sToken
        self.m_sReceiveId = sReceiveId

    def VerifyURL(self, sMsgSignature, sTimeStamp, sNonce, sEchoStr):
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, sTimeStamp, sNonce, sEchoStr)
        if ret != 0:
            return ret, None
        if signature != sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None
        pc = Prpcrypt(self.key)
        ret, sReplyEchoStr = pc.decrypt(sEchoStr, self.m_sReceiveId)
        return ret, sReplyEchoStr

    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        pc = Prpcrypt(self.key)
        ret, encrypt = pc.encrypt(sReplyMsg, self.m_sReceiveId)
        encrypt = encrypt.decode("utf8")
        if ret != 0:
            return ret, None
        if timestamp is None:
            timestamp = str(int(time.time()))
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, timestamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        xml_parse = XMLParse()
        return ret, xml_parse.generate(encrypt, signature, timestamp, sNonce)

    def DecryptMsg(self, sPostData, sMsgSignature, sTimeStamp, sNonce):
        xml_parse = XMLParse()
        ret, encrypt = xml_parse.extract(sPostData)
        if ret != 0:
            return ret, None
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.m_sToken, sTimeStamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        if signature != sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None
        pc = Prpcrypt(self.key)
        ret, xml_content = pc.decrypt(encrypt, self.m_sReceiveId)
        return ret, xml_content
