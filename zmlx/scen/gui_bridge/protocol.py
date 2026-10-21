"""界面桥 — **协议层**（方法名、错误码、请求校验、命令白名单）.

⚠️ 本模块**不 import Qt、不开 socket**，只做纯数据与校验 —— 于是它能在无界面环境里
离线单测。这一层是刻意隔离出来的：它的 bug 会以「界面偶发不刷新」的形式出现在很远
的地方，最难查（见 ``ReadMe.md`` §13 的 P0）。

协议是 JSON-RPC 2.0 的**子集**：只用 ``id`` / ``method`` / ``params`` / ``result`` / ``error``。
选它而不是自造格式，是因为错误语义有标准，且将来要包成 MCP server 时字段能直接复用。

Created by DeepSeek, 2026-10-30: 第一版（MVP，只含 ping / info / commands / tabs /
    show / screenshot）
"""

import json


#: 解析错误
PARSE_ERROR = -32700
#: 不是合法请求
INVALID_REQUEST = -32600
#: 方法不存在或未开放
METHOD_NOT_FOUND = -32601
#: 参数不合法
INVALID_PARAMS = -32602
#: 服务端内部错误
INTERNAL_ERROR = -32603
#: 业务失败（``ok: false``）
FAILED = -32000
#: 鉴权失败
UNAUTHORIZED = -32001
#: 忙（串行锁等不到 / 命令通道用满）
BUSY = -32002


class ProtocolError(Exception):
    """一次可预期的失败（会被翻译成 JSON-RPC 的 ``error`` 对象）."""

    def __init__(self, code, message, hint=None):
        super(ProtocolError, self).__init__(message)
        self.code = int(code)
        self.message = str(message)
        self.hint = hint

    def to_error(self):
        """转成 JSON-RPC 的 ``error`` 字段."""
        error = {'code': self.code, 'message': self.message}
        if self.hint:
            error['data'] = {'hint': self.hint}
        return error


#: 本版本**真正实现**的方法。不在表里的一律 ``METHOD_NOT_FOUND``。
METHODS = (
    'ping',         # 连通性
    'info',         # 窗口状态快照
    'commands',     # 可调用的 gui 命令名（过滤后）
    'tabs',         # 标签页列表
    'show',         # 打开 / 切到某个页面（核心能力）
    'screenshot',   # 截图（PNG base64）
)

#: 参数上限（防止一次塞爆界面 / JSON）
MAX_TEXT = 200_000
MAX_ROWS = 2000
MAX_COLUMNS = 30
MAX_SCREENSHOT_WIDTH = 4000


def normalize_request(payload):
    """校验一份 JSON-RPC 请求，返回 ``(id, method, params)``.

    Args:
        payload: 已经 ``json.loads`` 过的对象。

    Returns:
        tuple: ``(id, method, params)``；``params`` 一定是 dict（缺省为空 dict）。

    Raises:
        ProtocolError: ``INVALID_REQUEST`` / ``INVALID_PARAMS``。
            消息写得**可操作**，它会原样回给调用方（可能是 agent）。
    """
    if not isinstance(payload, dict):
        raise ProtocolError(
            INVALID_REQUEST,
            '请求必须是 JSON 对象，当前是 {0}'.format(type(payload).__name__),
            hint='示例：{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}')

    request_id = payload.get('id')
    method = payload.get('method')
    if not isinstance(method, str) or not method.strip():
        raise ProtocolError(INVALID_REQUEST, '缺少 method（字符串）',
                            hint='可用方法：' + ', '.join(METHODS))

    method = method.strip().lower()
    params = payload.get('params')
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ProtocolError(INVALID_PARAMS,
                            'params 必须是 JSON 对象（不是数组）',
                            hint='示例：{"name": "show_env_edit"}')
    return request_id, method, params


def loads(text):
    """把请求体解析成对象；失败抛 ``PARSE_ERROR``."""
    try:
        return json.loads(text)
    except (ValueError, TypeError) as err:
        raise ProtocolError(PARSE_ERROR, '请求体不是合法 JSON：{0}'.format(err))


def dumps(obj):
    """统一的响应序列化（``ensure_ascii=False`` 便于人读日志）."""
    return json.dumps(obj, ensure_ascii=False)


def success(request_id, result):
    """构造成功响应."""
    return {'jsonrpc': '2.0', 'id': request_id, 'result': result}


def failure(request_id, error):
    """构造失败响应（``error`` 是 :class:`ProtocolError` 或它的 ``to_error()`` 结果）."""
    if isinstance(error, ProtocolError):
        error = error.to_error()
    return {'jsonrpc': '2.0', 'id': request_id, 'error': error}


# ---------------------------------------------------------------------------
# 命令白名单
# ---------------------------------------------------------------------------

#: 允许 ``show`` 调用的 gui 命令**前缀**。只放"打开一个页面看一眼"这类只读入口。
ALLOW_PREFIXES = ('show_', 'view_', 'get_tab_', 'count_tab', 'is_')

#: 即使前缀匹配也**明确拒绝**的名字。两类：
#: ① 有副作用（发邮件 / 打开任意文件 / 往标签页灌内容）；
#: ② 自己（``show_gui_bridge`` 会打开本插件自己的面板，对外部调用方没有意义，
#:    且会让"允许调用的命令"里出现一个自我引用）。
DENY_NAMES = frozenset({
    'show_feedback',      # 会往开发者邮箱发东西（ai_assistant 同样排除它）
    'show_gui_bridge',    # 自己
    'open_file',          # 能打开任意文件
    'open_code',          # 能打开任意文件
    'edit_in_tab',        # 能把任意内容灌进标签页
})


def is_command_allowed(name):
    """这个 gui 命令名是否允许被外部进程调用.

    Args:
        name: ``GuiApi`` 命令表里的名字。

    Returns:
        bool: 允许为 ``True``。
    """
    if not isinstance(name, str) or not name:
        return False
    if name in DENY_NAMES:
        return False
    return name.startswith(ALLOW_PREFIXES)


def check_command_name(name):
    """校验 ``show`` 的 ``name`` 参数，不合法抛 ``ProtocolError``."""
    if not isinstance(name, str) or not name.strip():
        raise ProtocolError(INVALID_PARAMS, 'show 需要 name（gui 命令名，字符串）',
                            hint='先用 method=commands 取可用名字')
    name = name.strip()
    if not is_command_allowed(name):
        raise ProtocolError(
            METHOD_NOT_FOUND,
            '命令 {0!r} 未对界面桥开放'.format(name),
            hint='只允许以 {0} 开头的只读入口；用 method=commands 取完整清单'.format(
                ' / '.join(ALLOW_PREFIXES)))
    return name


def check_int(value, name, low, high, default=None):
    """取一个带边界的整数参数（越界抛 ``INVALID_PARAMS``）."""
    if value is None:
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ProtocolError(INVALID_PARAMS,
                            '{0} 必须是整数，当前是 {1!r}'.format(name, value))
    if number < low or number > high:
        raise ProtocolError(INVALID_PARAMS,
                            '{0} 必须在 [{1}, {2}] 之间，当前 {3}'.format(
                                name, low, high, number))
    return number
