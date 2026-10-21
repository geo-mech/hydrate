"""离线自测：反馈查看控件的解析链与界面行为（**不需要 DLL、不联网**）。

直接运行::

    $env:QT_QPA_PLATFORM='offscreen'; python zmlx/ui/tabs/_test_feedbacks_view.py

⚠️ 与 ``widget/AGENTS.md`` §4 一致：断言**数据结构与显示文本**，不看像素。
"""
import base64
import json
import sys

from zmlx.ui.pyqt import QtWidgets
from zmlx.ui.tabs.feedbacks_view import _Parsers, FeedbacksView

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


def contains(label, haystack, needle):
    global OK, BAD
    if needle in haystack:
        OK += 1
        print(f'  OK   {label}')
    else:
        BAD += 1
        print(f'  FAIL {label}\n         {needle!r} not in {haystack[:200]!r}')


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    print('--- 记号判定（复数是列表、单数是单条，只差一个 s）---')
    listing = ('Feedbacks: 2 | Email: a@b.com | Date: 2026-09-28'
               ' | Files: 20260928223007.json; 20260928224500.json')
    one = 'Feedback: x.json | Email: a@b.com | FileBase64: e30='
    check('list_ok(listing)', _Parsers.list_ok(listing), True)
    check('read_ok(one)', _Parsers.read_ok(one), True)
    # 两个必须互斥 —— 拿混 = 成功读成失败
    check('list_ok(one)', _Parsers.list_ok(one), False)
    check('read_ok(listing)', _Parsers.read_ok(listing), False)
    # 提交反馈的记号同名不同义
    check('list_ok(Succeed)', _Parsers.list_ok('Succeed'), False)
    check('read_ok(Succeed)', _Parsers.read_ok('Succeed'), False)
    check('list_ok(Not permitted.)', _Parsers.list_ok('Not permitted.'), False)

    print()
    print('--- parse_files（0 条时没有 Files 段 -> 空列表，不是错误）---')
    check('2 files', _Parsers.parse_files(listing),
          ['20260928223007.json', '20260928224500.json'])
    check('0 files', _Parsers.parse_files(
        'Feedbacks: 0 | Email: a@b.com | Date: 2026-09-28'), [])
    check('with Dropped',
          _Parsers.parse_files('Feedbacks: 3 | Email: a@b.com'
                               ' | Date: 2026-09-28 | Dropped: 1'
                               ' | Files: a.json; b.json'),
          ['a.json', 'b.json'])
    check('with Truncated',
          _Parsers.parse_files('Feedbacks: 1000 | Email: a@b.com'
                               ' | Date: 2026-09-28 | Truncated: true'
                               ' | Files: a.json'), ['a.json'])
    check('rejected', _Parsers.parse_files('Not permitted.'), [])

    print()
    print('--- find_display_name ---')
    check('from reply', _Parsers.find_display_name(one), 'x.json')
    check('on rejection', _Parsers.find_display_name('Not permitted.'), '')

    print()
    print('--- format_stamp（纯显示，不改发给服务端的名字）---')
    check('normal', _Parsers.format_stamp('20260928223007.json'),
          '2026-09-28 22:30:07')
    check('bad name', _Parsers.format_stamp('bad.json'), '')
    check('13 digits', _Parsers.format_stamp('2026092822300.json'), '')
    check('non-digit', _Parsers.format_stamp('2026092822300a.json'), '')

    print()
    print('--- format_content: 五种数据形态（返回四个键的 dict）---')
    # ① 合法 JSON 且带 text -> **拆开**（元数据 + text 两块）
    rec = {'ts': '2026-09-28T22:30:07+08:00', 'text': '中文', 'n': 1}
    raw = json.dumps(rec, ensure_ascii=False).encode('utf-8')
    parts = _Parsers.format_content(raw)
    check('split flag', parts['split'], True)
    check('text pulled out', parts['text'], '中文')
    check('meta keeps other fields', json.loads(parts['meta']), {'ts': rec['ts'], 'n': 1})
    check('meta drops text key', 'text' not in json.loads(parts['meta']), True)
    check('meta is indented', '\n  ' in parts['meta'], True)
    check('json note empty', parts['note'], '')

    # ①b 没有 text 字段 -> **不拆**，退回整份缩进 JSON
    rec2 = {'ts': '2026-09-28T22:30:07+08:00', 'n': 1}
    parts = _Parsers.format_content(
        json.dumps(rec2, ensure_ascii=False).encode('utf-8'))
    check('no text -> not split', parts['split'], False)
    check('no text -> full json shown', json.loads(parts['meta']), rec2)
    check('no text -> body empty', parts['text'], '')

    # ①c text 不是字符串 -> **不拆**（那份记录的 text 是数据不是正文）
    for label, value in (('number', 42), ('object', {'a': 1}), ('null', None),
                         ('list', [1, 2])):
        parts = _Parsers.format_content(
            json.dumps({'text': value}).encode('utf-8'))
        check(f'text={label} -> not split', parts['split'], False)

    # ①d 顶层不是对象 -> 不拆
    for label, doc in (('list', [1, 2]), ('number', 5), ('string', 'hi')):
        parts = _Parsers.format_content(json.dumps(doc).encode('utf-8'))
        check(f'top-level {label} -> not split', parts['split'], False)

    # ①e text 为空串 -> **仍然算拆开**（元数据非空、正文区空着）
    parts = _Parsers.format_content(
        json.dumps({'ts': 'x', 'text': ''}, ensure_ascii=False).encode('utf-8'))
    check('empty text still splits', parts['split'], True)
    check('empty text body', parts['text'], '')

    # ①f split_json 绝不改动传进来的对象
    original = {'ts': 'x', 'text': 'body'}
    _Parsers.split_json(original)
    check('split_json does not mutate input', original,
          {'ts': 'x', 'text': 'body'})

    # ② 能解码但不是 JSON -> 原文 + 说明（**不拆**）
    parts = _Parsers.format_content(b'hello world')
    check('plain text kept', parts['meta'], 'hello world')
    check('plain text not split', parts['split'], False)
    contains('plain text explained', parts['note'], '不是合法 JSON')

    # ③ 二进制 -> hex 摘要
    # ⚠️ 必须用**真的解不成 UTF-8** 的字节：``bytes(range(16))`` 全是控制字符，
    #    但它们是合法的 UTF-8，于是走「原文」那条分支（这一点值得记住）。
    binary = bytes([0xff, 0xfe, 0x00, 0x01, 0x80, 0x81])
    parts = _Parsers.format_content(binary)
    check('hex shown', parts['meta'], ' '.join(f'{b:02x}' for b in binary))
    check('binary not split', parts['split'], False)
    contains('binary explained', parts['note'], '不是文本')

    # ③b 控制字符（合法 UTF-8）走的是**原文**分支，不是 hex
    parts = _Parsers.format_content(bytes(range(16)))
    check('control chars are text', parts['meta'],
          bytes(range(16)).decode('utf-8'))

    # ④ 0 字节 -> 成功，但显示为空文件
    parts = _Parsers.format_content(b'')
    check('0-byte meta empty', parts['meta'], '')
    check('0-byte note', parts['note'], '（这个文件是空的）')
    check('0-byte not split', parts['split'], False)

    # ⑤ None（业务拒绝）-> 与 0 字节**不同**
    parts = _Parsers.format_content(None)
    check('None meta empty', parts['meta'], '')
    contains('None note differs', parts['note'], '没拿到内容')
    check('None note != 0-byte note',
          parts['note'] != '（这个文件是空的）', True)

    # ⑥ 非法 UTF-8
    parts = _Parsers.format_content(b'\xff\xfe\x00abc')
    contains('bad utf-8 explained', parts['note'], '不是文本')

    print()
    print('--- full_json（「完整原文」区的内容）---')
    check('full json parses back', json.loads(_Parsers.full_json(raw)), rec)
    check('full json keeps text', 'text' in json.loads(_Parsers.full_json(raw)),
          True)
    check('full json on non-json', _Parsers.full_json(b'hello'), '')
    check('full json on empty', _Parsers.full_json(b''), '')
    check('full json on binary', _Parsers.full_json(b'\xff\xfe'), '')

    print()
    print('--- is_truncated ---')
    check('truncated', _Parsers.is_truncated(
        'Feedback: x.json | Email: a@b.com | Truncated: true'
        ' | FileBase64: e30='), True)
    check('not truncated', _Parsers.is_truncated(one), False)

    print()
    print('--- 控件：列举成功后填充文件列表 ---')
    w = FeedbacksView(email='a@b.com', date='2026-09-28')
    w._on_list_reply(listing, '往返耗时：0.42 s')
    check('files filled', w.get_files(),
          ['20260928223007.json', '20260928224500.json'])
    check('banner mentions count', '2' in w.status_label.text(), True)

    print()
    print('--- 控件：0 条 / 越权 / 超一页 三种横幅 ---')
    w._on_list_reply('Feedbacks: 0 | Email: a@b.com | Date: 2026-09-28', '')
    check('0 files', w.get_files(), [])
    contains('0-file banner', w.status_label.text(), '没有反馈')

    w._on_list_reply('Not permitted.', '')
    contains('denied shows raw server text', w.status_label.text(),
             'Not permitted.')
    # ⚠️ 绝不替服务端编「邮箱不存在」
    check('does not invent text', '邮箱不存在' in w.status_label.text(), False)

    w._on_list_reply('Feedbacks: 1000 | Email: a@b.com | Date: 2026-09-28'
                     ' | Truncated: true | Files: a.json', '')
    contains('page-truncated banner', w.status_label.text(), '截断')

    w._on_list_reply('', '')
    contains('empty reply handled', w.status_label.text(), '网络')

    print()
    print('--- 控件：读取一条内容（合法 JSON 带 text -> 拆成两块）---')
    w2 = FeedbacksView(email='a@b.com', date='2026-09-28')
    b64 = base64.b64encode(raw).decode('ascii')
    w2._on_read_reply(
        f'Feedback: 20260928223007.json | Email: a@b.com | FileBase64: {b64}',
        '往返耗时：0.5 s')
    check('text box visible (split)', w2._text_box.isVisibleTo(w2), True)
    check('meta shows other fields', json.loads(w2.meta_view.toPlainText()),
          {'ts': rec['ts'], 'n': rec['n']})
    check('text box shows body', w2.text_view.toPlainText(), '中文')
    check('meta has no text key',
          'text' not in json.loads(w2.meta_view.toPlainText()), True)
    check('full source visible', w2._full_box.isVisibleTo(w2), True)
    check('full source is whole json',
          json.loads(w2.full_view.toPlainText()), rec)
    contains('file name in label', w2.file_label.text(), '20260928223007.json')
    contains('read ok banner', w2.status_label.text(), '读取成功')
    contains('split mentioned in banner', w2.status_label.text(), 'text')

    print()
    print('--- 控件：没有 text 字段 -> 退回单区（下框与完整原文都藏起来）---')
    w2b = FeedbacksView(email='a@b.com')
    rec_notext = {'ts': '2026-09-28', 'n': 7}
    raw_notext = json.dumps(rec_notext, ensure_ascii=False).encode('utf-8')
    w2b._on_read_reply(
        'Feedback: x.json | FileBase64: '
        + base64.b64encode(raw_notext).decode('ascii'), '')
    check('text box hidden', w2b._text_box.isVisibleTo(w2b), False)
    check('full source hidden', w2b._full_box.isVisibleTo(w2b), False)
    check('meta shows whole json', json.loads(w2b.meta_view.toPlainText()),
          rec_notext)

    print()
    print('--- 控件：0 字节文件是成功（与「文件不存在」分开）---')
    w3 = FeedbacksView(email='a@b.com')
    w3._on_read_reply('Feedback: x.json | Email: a@b.com | FileBase64: ', '')
    contains('0-byte banner', w3.status_label.text(), '空文件')
    check('0-byte does not split', w3._text_box.isVisibleTo(w3), False)

    w4 = FeedbacksView(email='a@b.com')
    w4._on_read_reply('The feedback file is not available.', '')
    contains('missing file shows raw text', w4.status_label.text(),
             'The feedback file is not available.')
    check('missing file banner differs from 0-byte',
          '空文件' in w4.status_label.text(), False)

    print()
    print('--- 控件：截断的内容不抛异常，且横幅说明 ---')
    w5 = FeedbacksView(email='a@b.com')
    partial = '{"ts": "2026-09-28", "text": "被截断的'.encode('utf-8')
    b64p = base64.b64encode(partial).decode('ascii')
    w5._on_read_reply(
        f'Feedback: x.json | Email: a@b.com | Truncated: true'
        f' | FileBase64: {b64p}', '')
    contains('truncated banner', w5.status_label.text(), '截断')
    check('content still shown',
          len(w5.meta_view.toPlainText() + w5.text_view.toPlainText()) > 0, True)

    print()
    print('--- 控件：二进制内容不崩 ---')
    w6 = FeedbacksView(email='a@b.com')
    w6._on_read_reply(
        'Feedback: x.json | Email: a@b.com | FileBase64: '
        + base64.b64encode(b'\xff\xfe\x00\x01').decode('ascii'), '')
    contains('binary banner', w6.status_label.text(), '十六进制')
    check('binary content non-empty',
          len(w6.meta_view.toPlainText()) > 0, True)
    check('binary does not split', w6._text_box.isVisibleTo(w6), False)

    print()
    print('--- 控件：切换文件时上一条的残留被清掉 ---')
    w6._on_read_reply(
        f'Feedback: y.json | FileBase64: {b64}', '')
    check('now split again', w6._text_box.isVisibleTo(w6), True)
    w6._clear_content()
    check('meta cleared', w6.meta_view.toPlainText(), '')
    check('text cleared', w6.text_view.toPlainText(), '')
    check('full source cleared', w6.full_view.toPlainText(), '')
    check('text box hidden after clear', w6._text_box.isVisibleTo(w6), False)
    check('full box hidden after clear', w6._full_box.isVisibleTo(w6), False)

    print()
    print('--- 控件：日期快捷按钮（本地计算，不联网）---')
    w7 = FeedbacksView(email='a@b.com')
    w7.set_date_days(0)
    import datetime
    check('today', w7.date_view.text(),
          datetime.date.today().strftime('%Y-%m-%d'))
    w7.set_date_days(1)
    check('yesterday', w7.date_view.text(),
          (datetime.date.today() - datetime.timedelta(days=1)
           ).strftime('%Y-%m-%d'))

    print()
    print('--- 控件：get_query 只去空白，不做校验 ---')
    w7.date_view.setText('  not-a-date  ')
    w7.email_view.setText('  a@b.com  ')
    check('get_query', w7.get_query(), ('a@b.com', 'not-a-date'))

    print()
    print('--- 控件：不实现 save_file（绝不落盘别人的反馈正文）---')
    check('no save_file', hasattr(w7, 'save_file'), False)

    print()
    print('--- 控件：cleanup_before_tab_close 释放全部四个线程引用 ---')
    w7.cleanup_before_tab_close()
    check('all workers released',
          [w7._list_worker, w7._read_worker,
           w7._prefill_worker, w7._user_list_worker],
          [None, None, None, None])

    print()
    print(f'== {OK} passed, {BAD} failed ==')
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
