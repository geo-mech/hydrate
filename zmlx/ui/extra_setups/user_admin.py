"""「管理」菜单动作（菜单「帮助 → 用户 → 管理」）.

把 :class:`zmlx.ui.tabs.user_admin_view.UserAdminView` 挂到界面：Tab 控件本体与
``show_user_admin()`` 在 ``zmlx/ui/tabs/user_admin_view.py``，本文件只负责
「注册命令 + 挂菜单」。

⚠️ 菜单文字是「**管理**」而不是「用户管理」：它已经在「用户」子菜单里，
再叫「用户管理」就成了「用户 → 用户管理」这种重复。2026-10-19 那个顶层「用户」
菜单并回了「帮助」，于是这里是「帮助 → 用户 → 管理」。

为什么放在 ``extra_setups/`` 而不是 ``plugins/``
------------------------------------------------

``plugins/`` 下的是**用户可禁用的扩展**（禁用后那段代码根本不执行）；而本页是
**产品功能** —— 授权查询与修改归软件本身，不该让用户在「设置 → 插件」里把它
关掉。``extra_setups/`` 的定位是「装配层：把已有控件挂到菜单」，正是这里。

⚠️ 本模块由 ``extra_setups/__init__.py`` 的 ``setup_ui()`` 调用（那里是**唯一**的
登记点）。``setup_ui`` 本身带 ``@execute_once``，重复调用不会重复注册。

⚠️ **普通用户也会看到这个菜单项**：``UserAdminView`` 开页后先验证管理员身份，
非管理员只看到「没有管理员权限」+ 自己的授权信息与一条出路。菜单项不分级 ——
判定发生在打开页面之后，这样用户至少知道「这里有这个入口，但我不够格」，
而不是菜单项凭空消失。

Created by DeepSeek, 2026-10-18
Modified by DeepSeek, 2026-10-18: 由 ``plugins/user_admin.py`` 移回 ``extra_setups/``
    （用户管理是产品功能，不该做成可禁用的插件）
Modified by DeepSeek, 2026-10-18: 菜单由「帮助 → 查询 → 用户管理」改为「用户 → 管理」
Modified by DeepSeek, 2026-10-19: 「用户」整体并回「帮助」，菜单为「帮助 → 用户 → 管理」
"""

from zmlx.system import execute_once
from zmlx.ui import gui


@execute_once(file=__file__)
def setup_ui():
    """注册「帮助 → 用户 → 管理」与 ``gui.show_user_admin()``."""
    from zmlx.ui.tabs.user_admin_view import setup_ui as register

    register()


if __name__ == '__main__':
    # 直接运行本文件：把界面开起来，验证菜单项能被注册
    if gui.exists():
        setup_ui()
    else:
        gui.execute(setup_ui, close_after_done=False)
