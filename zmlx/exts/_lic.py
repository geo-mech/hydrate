from ctypes import (c_char_p, c_int, c_bool)

from zmlx.exts._dll import DllCore, core, make_c_char_p
from zmlx.exts._utils import app_data


class License:
    """管理软件的授权信息。

    该类用于管理软件的授权信息，包括获取授权信息、检查授权状态、生成授权码等功能。
    """

    def __init__(self, core_obj: DllCore):
        """初始化 License 对象。

        Args:
            core_obj: 核心模块对象，用于调用底层功能。
        """
        self.core = core_obj
        self.license_info_has_checked = False
        if self.core.has_dll():
            self.core.use(c_bool, 'lic_is_admin')
            self.core.use(c_int, 'lic_webtime')
            self.core.use(c_bool, 'lic_valid')
            self.core.use(c_char_p, 'lic_desc')
            self.core.use(c_char_p, 'lic_serial', c_bool, c_bool)
            self.core.use(c_char_p, 'lic_create', c_char_p)
            self.core.use(None, 'lic_load', c_char_p)

    @property
    def is_admin(self) -> bool:
        """检查当前计算机是否具有管理员权限。

        Returns:
            bool: 是否具有管理员权限。
        """
        if self.core.has_dll():
            return self.core.lic_is_admin()
        else:
            return False

    @property
    def webtime(self) -> int:
        """获取网络时间戳（非实际时间）。

        程序将使用此时间戳来判断软件是否已过期。

        Returns:
            int: 网络时间戳。
        """
        if self.core.has_dll():
            return self.core.lic_webtime()
        else:
            return 100101

    @property
    def valid(self) -> bool:
        """检查当前计算机是否具有有效的授权

        Returns:
            bool: 当前计算机是否具有有效的授权
        """
        if self.core.has_dll():
            return self.core.lic_valid()
        else:
            return False

    @property
    def desc(self) -> str:
        """获取授权信息的描述。

        Returns:
            str: 授权信息的描述。
        """
        if self.core.has_dll():
            return core.lic_desc().decode()
        else:
            return ''

    def get_serial(self, base64: bool = True, export_all: bool = False) -> str:
        """获取当前计算机的 USB 序列号，用于注册。

        Args:
            base64 (bool): 是否以 Base64 格式返回序列号。
            export_all (bool): 是否导出所有 USB 设备的序列号。

        Returns:
            str: USB 序列号。
        """
        if self.core.has_dll():
            return self.core.lic_serial(base64, export_all).decode()
        else:
            return ''

    def create(self, base64_serial: str) -> str:
        """根据 USB 序列号生成永久授权码。

        仅用于测试。

        Args:
            base64_serial (str): USB 序列号。

        Returns:
            str: 永久授权码。
        """
        if self.core.has_dll():
            return self.core.lic_create(make_c_char_p(base64_serial)).decode()
        else:
            return ''

    def load(self, code: str):
        """将给定的授权码存储到默认位置。

        Args:
            code (str): 授权码。
        """
        if self.core.has_dll():
            self.core.lic_load(make_c_char_p(code))

    @property
    def usb_serial(self) -> str:
        """获取当前计算机的 USB 序列号（其中之一），用于注册。

        Returns:
            str: USB 序列号。
        """
        return self.get_serial()

    def check(self):
        """检查授权状态。

        如果当前计算机已正确授权，则函数正常通过；否则触发异常。
        """
        assert self.valid, 'The license is not valid on this computer.'

    def check_once(self):
        """在迭代过程中检查授权状态。

        如果授权未检查过，则执行检查并输出提示信息。
        """
        if not self.license_info_has_checked:
            self.license_info_has_checked = True
            if app_data.has_tag_today('lic_checked'):
                return
            else:
                app_data.add_tag_today('lic_checked')
            if not self.valid:
                text = f"""
The software is not licensed on this computer. Please send the following 
code to author (zhangzhaobin@mail.iggcas.ac.cn):
     <{self.usb_serial}>
Thanks for using.
    """
                print(text)


lic = License(core_obj=core)
