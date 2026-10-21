"""``WebLicense`` 反馈读取接口的自测（v3.12 的两个动作 + base64 解码）。

直接运行::

    python zmlx/exts/_test_feedback_api.py

[!] 本文件**不联网** —— 它只喂**假的答复文本**给 ``WebLicense.decode_feedback``
那条解码链（那正是「解码关在 WebLicense 里」这条约定的落点），所以可以在任何
机器上跑。

[!] 与项目里其它 ``*_test.py`` 一样：**只增不删**（见 projects/zml/AGENTS.md）。

[!] **提示文本一律 ASCII**（本节与下面那些 ``print('--- ... ---')`` 的段落标题
都用 ``[!]``，不用 U+26A0 那个警告符号）：本文件是**直接运行**的脚本，输出落在
调用者的控制台上，而 Windows 中文控制台是 **GBK** —— 一个 U+26A0（GBK 里没有
这个码位，实测连字形都编不出来）就会让 ``print`` 抛 ``UnicodeEncodeError``，
脚本**在跑到一半时崩掉**（2026-10-11 实测：27 项只跑到第 6 项）。中文说明文字
不受影响（GBK 编得出来），需要强调时用 ``[!]``。
"""
import base64
import json
import sys

from zmlx.exts import web_license as w

OK = 0
BAD = 0


def check(label, got, want):
    global OK, BAD
    if got == want:
        OK += 1
        print(f'  OK   {label}')
    else:
        BAD += 1
        print(f'  FAIL {label}\n         got  {got!r}\n         want {want!r}')


def main():
    record = {'ts': '2026-09-28T22:30:07+08:00', 'text': '中文反馈', 'n': 42}
    raw = json.dumps(record, ensure_ascii=False).encode('utf-8')
    b64 = base64.b64encode(raw).decode('ascii')
    good = f'Feedback: 20260928223007.json | Email: a@b.com | FileBase64: {b64}'

    print('--- decode_feedback: 正常往返 ---')
    check('bytes round-trip', w.decode_feedback(good), raw)
    check('json round-trip',
          json.loads(w.decode_feedback(good).decode('utf-8')), record)

    print()
    print('--- 0 字节文件是【成功】(b"" 而不是 None) ---')
    check('0-byte -> b""', w.decode_feedback(
        'Feedback: x.json | Email: a@b.com | FileBase64: '), b'')
    check('0-byte + spaces -> b""', w.decode_feedback(
        'Feedback: x.json | FileBase64:    '), b'')

    print()
    print('--- 段值里是垃圾 -> None（[!] 绝不能也回 b""）---')
    # [!] 这一组是最容易漏的：``b64decode`` 默认会把字母表外的字符**丢掉**，
    #    于是 "!!!" 会被静默解成 b"" —— 那就把「内容坏了」说成了「空文件」。
    #    实现里靠「先判空串」+ ``validate=True`` 两条一起挡住，缺一不可。
    for label, payload in (('garbage', '!!!'),
                           ('non-ascii', '中文'),
                           ('bad padding', 'e30')):
        check(f'{label} -> None', w.decode_feedback(
            f'Feedback: x.json | FileBase64: {payload}'), None)

    print()
    print('--- 记号判定（复数=列表、单数=单条，只差一个 s）---')
    # [!] 拿列举的记号来解单条 = 永远失败（反之亦然）
    check('plural mark -> None', w.decode_feedback(
        'Feedbacks: 1 | Email: a@b.com | Files: a.json'), None)
    # [!] 提交反馈的 Succeed 同名不同义
    check('Succeed -> None', w.decode_feedback('Succeed'), None)
    check('whitespace tolerated', w.decode_feedback('  ' + good + '  '), raw)

    print()
    print('--- 业务拒绝 / 连不上 -> None（永不抛异常）---')
    for bad in ('Not permitted.',
                'The feedback file is not available.',
                'Please register with your email first.',
                'The file u_abc has no license.',
                'Service temporarily unavailable',
                'WinHttpSendRequest 失败 —— Win32 error 12007',
                'Feedback: x.json | Email: a@b.com',   # 没有 FileBase64 段
                '', None, 123, [], {}):
        check(f'reject {str(bad)[:34]!r:40s}', w.decode_feedback(bad), None)

    print()
    print('--- 截断段不影响解码（段数不固定，按段名找）---')
    truncated = ('Feedback: x.json | Email: a@b.com | Truncated: true'
                 f' | FileBase64: {b64}')
    check('truncated still decodes', w.decode_feedback(truncated), raw)

    print()
    print('--- 二进制内容照样能取出（解码只管 base64，不管内容）---')
    weird = b'\xff\xfe\x00binary'
    wr = 'Feedback: x.json | FileBase64: ' + base64.b64encode(weird).decode()
    check('raw bytes kept', w.decode_feedback(wr), weird)

    print()
    print('--- 接口存在且不抛异常（get_feedback_bytes 会联网，这里只验契约）---')
    check('get_feedback_bytes callable',
          callable(getattr(w, 'get_feedback_bytes', None)), True)
    check('get_feedback callable', callable(getattr(w, 'get_feedback', None)), True)
    check('list_feedbacks callable',
          callable(getattr(w, 'list_feedbacks', None)), True)

    print()
    print(f'== {OK} passed, {BAD} failed ==')
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
