"""
超星学习通 API 模块
"""

from .fanyalogin import FanyaloginAPI
from .createqr import CreateQRCodeAPI
from .getauthstatus import GetAuthStatusAPI
from .sendcode import SendCodeAPI
from .phone_login import PhoneLoginAPI
from .register import RegisterAPI

__all__ = [
    'FanyaloginAPI',
    'CreateQRCodeAPI',
    'GetAuthStatusAPI',
    'SendCodeAPI',
    'PhoneLoginAPI',
    'RegisterAPI',
]
