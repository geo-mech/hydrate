# 界面桥（`zmlx/scen/gui_bridge/`）

> **状态：MVP 已实现并实测通过（2026-10-30）。** 6 个方法在两个真实窗口之间跨进程可用，
> 实测记录与踩坑见 §15。仍待拍板的是 D7 / Q1 / Q4（§12、§14）。
> 本文件是**唯一真相**：架构、协议、方法表、线程模型、安全模型、测试方案、决策记录都在这。

一句话：**把已经跑起来的 IGG-Hydrate 界面，暴露成一条本机可用的 RPC 通道，让外部进程
（脚本、另一个 AI agent、另一个 IGG-Hydrate 实例）能"打开某个页面 / 看界面状态 / 截图 /
读当前页数据"。**

---

## 1. 为什么需要它（与现状的关系）

`zmlx/scen/ai_assistant/`（2026-10-29）已经有一套「AI 控制界面」的通道，但它是**进程内**的：

- 模型输出 ```action 代码块 → `ActionSpec.normalize` 校验（`action.py:92-196`）
  → `ActionRunner.execute` 在 GUI 线程执行（`:212-293`）；
- 动作只有 8 种：`show` / `link` / `text` / `table` / `plot_display` / `console` /
  `write_script` / `run_script`（`action.py:77-78`）。

**它缺的不是能力，是边界**：外部进程（比如 WorkBuddy 这边的 agent、或一段 bash 脚本）
够不着那个进程里的 `gui.command`。本包补的正是这一步 —— 把「同一个进程里的函数调用」
变成「跨进程的一次请求」，其余尽量不动。

⚠️ **不 import `ai_assistant`**，理由见 §5.3：那会让两个可独立关闭的插件互相依赖。

---

## 2. 边界

### 2.1 做什么

| 能力 | 例子 | 谁用 |
|---|---|---|
| 连通性与自检 | `ping` / `info` | 外部 agent 的第一步 |
| 能力发现 | `commands`（返回真实命令名，来自 `list_all()`） | agent 自己找能做哪些事 |
| 只读导航 | `show`（打开某个页面） | agent 回答「在哪设置 X」 |
| 展示内容 | `text` / `table` / `link` | agent 把结果贴到界面上 |
| 看界面 | `screenshot`（返回 PNG） | **agent 判断"操作有没有生效"** |
| 读状态 | `tabs` / `state`（当前页的 `get_data()`）/ `console` | agent 读回结果 |
| 等异步 | `wait_idle`（轮询式） | 扫描 / 计算 / 加载完成 |

### 2.2 不做什么（红线，不是"暂缓"）

| 不做 | 原因 |
|---|---|
| 不开放 `run_script` / `write_script` / 任何 exec | 一旦开放就等于**本机任意代码执行** |
| 不开放 `open_file` / `edit_in_tab` | 能读任意文件、能把任意内容灌进标签页 |
| 不开放 `close` / `start` / `set_style_sheet` | 会打断用户正在做的事、或让界面错乱 |
| 不开放 `window`（返回 `MainWindow` 实例） | 不可序列化（见 §8.2） |
| 不做通用控件寻址（"点第 3 个按钮"） | 全仓 `setObjectName` 仅 **28 处**，没有稳定标识，见 §7.1 |
| 不做远程（非本机）访问 | 不是本次目标；放开就是另一个量级的安全问题 |
| 不做沙箱承诺 | 见 §11 最后一段 |

---

## 3. 文件职责（落地时按此建）

| 文件 | 行数量级 | 依赖 | 职责 |
|---|---|---|---|
| `zml_plugin.py` | ~120 | Qt + `gui` | 插件入口：`# ** enabled = False`；菜单项；注册唯一命令 `bridge_call`；挂测试控件 |
| `protocol.py` | ~150 | **纯 stdlib** | 方法名常量、错误码、参数规整与边界检查（可离线单测，不 import Qt） |
| `methods.py` | ~350 | Qt + `gui` | 方法实现。**所有函数都在 GUI 线程里跑**，可以直接碰 `QMainWindow` |
| `server.py` | ~220 | **纯 stdlib** | `ThreadingHTTPServer` 封装：路由、鉴权、JSON 编解码、串行锁、日志 |
| `discovery.py` | ~120 | **纯 stdlib** | 句柄文件写/读/扫、pid 存活判断、退出清理 |
| `client.py` | ~150 | **纯 stdlib** | `urllib` 客户端：`ping/info/show/...`，供测试控件与外部脚本 |
| `test_panel.py` | ~400 | Qt | `BridgeTestPanel`：本机服务状态 + 目标选择 + 发请求 + 双向日志 |
| `ReadMe.md` | — | — | 本文件 |

**零新增第三方依赖**（不引入 Flask / FastAPI / requests）。理由：`zmlx` 是随包分发的库，
新增依赖会影响所有用户；而这条通道的需求用 `http.server` + `urllib` 足够。

---

## 4. 架构：一次调用的完整路径

```
外部进程（agent / 脚本 / 另一个 IGG-Hydrate）
   │  POST http://127.0.0.1:<port>/rpc
   │  Header: X-ZML-Bridge-Token: <token>
   │  Body:   {"jsonrpc":"2.0","id":7,"method":"show","params":{"name":"show_env_edit"}}
   ▼
[server.py]  HTTP 服务线程（stdlib，非 Qt 线程）
   │  ① 校验 token  ② 解析 JSON  ③ 取**串行锁**（同一时刻只放一个请求进去）
   ▼
[protocol.py]  校验 method 是否在 allowlist、params 是否合法
   ▼
gui.command('bridge_call', method, params)     ← 唯一的跨线程投递点（已有能力）
   │  信号 → GUI 线程（`GuiApi.command` 自带，见 utils/gui_api.py:97-145）
   ▼
[methods.py]  GUI 线程内执行
   │  · show/text/table/link → 调 gui 命令或 MainWindow 方法
   │  · tabs/state          → 直接用 `gui.get()` 拿到的 MainWindow 对象
   │  · screenshot          → QWidget.grab() → PNG
   ▼
   返回 dict → 沿原路回传（异常也回传）→ 释放串行锁 → HTTP 响应
```

### 4.1 为什么只注册一个命令

判据是**面越小越好**：外部能触达的每一个 gui 命令名都是一处攻击面、一处要审计的入口。
只开 `bridge_call(method, params)` 一个 —— 于是**方法白名单**（`protocol.METHODS`）与
**参数校验**（`protocol.check_*`）都只有一处，加方法时漏写校验一眼就能看出来。

⚠️ **旧版这里写的理由是「通道池上限 20、用满不排队就返回 `None`」—— 该理由已作废**：
20 通道池于 **v1.9.9** 删除，`utils/gui_api.py` 现在是**每次调用新建一个通道、用完
即弃、无并发上限、不再丢弃**。所以铺开 20 个命令并不会撞上限；**不要再用「省通道」
当依据**，也不要在别处照抄这条理由。

⇒ 服务端仍然用**一把串行锁**保证同一时刻只有一个请求在飞。吞吐不是这个功能的指标，
**可预测**才是（队列里只有一个人；等锁超过 `LOCK_TIMEOUT` 就回 `BUSY`，让调用方能
区分「对方忙」和「对方死了」）。

⚠️ **非 200 一律 `Connection: close`**（2026-10-30 修）：`401` / `413` / `400` / `404`
这些早退分支**没有消费请求体**（token 校验、长度校验、JSON 解析都在读 body 之前就回包
了），而 HTTP/1.1 默认 keep-alive —— 残留 body 会被当成**下一个请求**的请求行，同一
连接上后续请求全部得到基类的 `400 Bad Request` 页面（实测：先发错 token 再发正确请求，
第二次拿到 HTML 错误页）。**内置 `BridgeClient` 不受影响**（`urllib` 每次新建连接），
但 `requests.Session`、手写 `http.client`、浏览器 fetch 会复用连接，所以必须修。
出错后重连，比让客户端拿到错乱响应清楚得多；正常的 `200` 仍然复用连接。

### 4.2 时序（正常一次 `show`）

```
t0  外部: 建连接、发请求
t1  服务线程: token OK → 拿锁 → 校验 method/params → emit
t2  GUI 线程: bridge_call 被执行 → 找到 show_env_edit → 开/切标签页
t3  GUI 线程: 返回 {'ok': True, 'menu': '设置 → 系统'}
t4  服务线程: 释放锁 → 200 + JSON
t5  外部: 收到回包（同时刻界面已经变了 —— 这是"同步"的，不是"发出去就不管"）
```

⚠️ **同步语义**是本设计的关键选择：`gui.command` 天然阻塞等待 GUI 线程执行完，
所以外部拿到的回包**代表界面确实动了**，而不是排队通知。这比"发消息 + 事后查状态"
对 agent 友好得多（少一轮状态轮询）。

---

## 5. 协议

### 5.1 形式

JSON-RPC 2.0 的**子集**（只用到 `method` / `params` / `id` / `result` / `error`）。
选它而不是自造格式的理由：① 错误语义有标准（`code` + `message`）；
② 将来若要把本服务包成 MCP server（MCP 也是 JSON-RPC 2.0），字段能直接复用。

```
POST /rpc          Content-Type: application/json
GET  /health       → {"ok":true,"app":"IGG-Hydrate","version":"1.9.x"}（不需要 token）
```

请求：

```json
{"jsonrpc": "2.0", "id": 7, "method": "show", "params": {"name": "show_env_edit"}}
```

成功：

```json
{"jsonrpc": "2.0", "id": 7, "result": {"ok": true, "menu": "设置 → 系统"}}
```

失败：

```json
{"jsonrpc": "2.0", "id": 7,
 "error": {"code": -32602, "message": "params.name 必须是字符串",
           "data": {"hint": "可用命令见 method=commands"}}}
```

### 5.2 错误码

| code | 含义 | 典型触发 |
|---|---|---|
| `-32700` | 不是合法 JSON | 手抖 |
| `-32600` | 不是合法请求（缺 method / id） | 客户端 bug |
| `-32601` | 方法不存在或**未开放** | `run_script`（明确拒绝，消息里说明原因） |
| `-32602` | 参数不合法（含越界） | `show` 给了不存在的命令名 |
| `-32603` | 服务端内部错误 | 实现 bug |
| `-32000` | 业务失败（`ok:false` 的内容） | 目标插件没加载、页面不可用 |
| `-32001` | 鉴权失败 | token 不对 |
| `-32002` | **忙**（串行锁等超时） | 前一个请求卡住超过 N 秒 |

⚠️ `-32002` 是**必须实现的**：`gui.command` 在 GUI 线程里如果被长任务占住
（比如正在跑一个 `Console` 长任务），服务线程会一直等锁。要让外部能区分
"对方忙"和"对方挂了"，否则 agent 会以为是网络问题反复重试。

### 5.3 方法清单（白名单的唯一来源）

**能力清单不写死，取自运行时的 `GuiApi.list_all()`**（`utils/gui_api.py:78`）。
`commands` 方法返回它，并按下面的规则过滤：

```
允许的前缀：show_ / view_ / get_tab_ / count_tab / is_ / device_pixel_ratio
显式黑名单（即使前缀匹配也拒绝）：show_feedback, show_license*, open_file, open_code
```

`show` 的 `name` **直接就是 gui 命令名**，不做"给模型看的别名"这一层 ——
这样零维护、自动跟随新插件；中文说明由 agent 自己从 `tabs`/`info` 的返回里读。

| method | params | result | 风险 | 备注 |
|---|---|---|---|---|
| `ping` | — | `{ok, app, version, pid, uptime}` | 无 | 连通性 |
| `info` | — | `{ok, window:{title,size,maximized,dark}, running, tab_count, cwd}` | 无 | 状态快照 |
| `commands` | — | `{ok, names:[...], count}` | 无 | 来自 `list_all()` |
| `tabs` | — | `{ok, current, items:[{index, caption}]}` | 无 | 用 `count_tabs` + `get_tab_caption`（`main.py:1863,1881`） |
| `show` | `{name}` | `{ok, menu?}` | 无 | 必须是 allowlist 里的命令名 |
| `text` | `{title, text}` | `{ok}` | 无 | 长度上限 200k（同 `action.py:84`） |
| `table` | `{title, columns, rows}` | `{ok}` | 无 | 上限 2000×30 |
| `link` | `{url, caption?}` | `{ok}` | 低 | 只允许 `http(s)://` |
| `console` | `{mode:'text'\|'html', tail?}` | `{ok, text}` | 无 | 只读 |
| `screenshot` | `{target?:'window'\|'tab', max_width?, path?}` | `{ok, png_b64?, path?, width, height}` | 无 | 见 §7.3 |
| `state` | — | `{ok, type, data}` 或 `{ok:false, reason}` | 无 | 当前页有 `get_data()` 才有 |
| `wait_idle` | `{timeout?}` | `{ok, idle, waited}` | 无 | **轮询式**，见 §6.3 |
| `log` | `{tail?}` | `{ok, items:[...]}` | 无 | 本服务访问日志，调试用 |

**明确不开放**（`-32601` 并说明原因）：`run_script`、`write_script`、`open_file`、
`edit_in_tab`、`close`、`start`、`set_style_sheet`、`window`、任何 `mark_direct` 命令。

### 5.4 为什么不复用 `ai_assistant` 的 `SHOW_TARGETS`

`SHOW_TARGETS`（`action.py:43-66`，18 项）的价值是**给模型看的中文说明 + 菜单路径**，
面向"聊天窗里的用户问『怎么设置环境变量』"。而跨进程调用的对象是**另一个 agent**，
它可以先 `commands` 拿到真实命令名、再 `info` 看窗口状态 —— 不需要我们预先翻译。

⇒ 本包不复制这份表（复制必然漂移）；两个包各自演进，互不 import。

---

## 6. 线程模型（本设计最容易写错的地方）

### 6.1 三类线程，各自能碰什么

| 线程 | 谁 | 能碰 Qt 控件吗 | 说明 |
|---|---|---|---|
| GUI 线程 | `QApplication` 主线程 | ✅ 只有它能 | `bridge_call` 在这里执行 |
| HTTP 服务线程 | `ThreadingHTTPServer` 每个请求一个 | ❌ **绝对不能** | 只做 JSON / token / 锁 |
| 客户端线程 | 外部进程，或本进程测试控件 | ❌ | 只能发 HTTP |

### 6.2 三条硬约束

1. **服务线程绝不能直接 `widget.xxx()`** —— 必须经 `gui.command('bridge_call', ...)`。
   直接调用的后果是"偶发不刷新 / 偶发崩"，且不可复现（`gui_buffer.py:343` 那段
   `mark_direct` 的教训，2026-10-23 因此当日撤销过 14 条命令的标记）。
2. **`bridge_call` 注册时不要 `mark_direct`** —— 它要建控件、要切标签页，
   属于"必须派发到 GUI 线程"的那一类。
3. **返回值必须可 JSON 序列化**。`window` 命令返回 `MainWindow` 实例（`main.py:423`），
   直接 `json.dumps` 会炸 —— 这也是它被列入 §2.2 黑名单的原因。

### 6.3 `wait_idle` 为什么是轮询

朴素做法是服务端循环 `while not idle: sleep` —— 但它持有串行锁，会把所有其它请求
（包括 `ping`）一起堵死，外部无法区分"忙"和"死"。

⇒ 服务端**立刻返回** `{idle: false, waited: 0}`，由客户端循环调用。
`client.py` 提供一个 `wait_idle(timeout=60)` 的语法糖（内部每 0.3s 调一次），
外部 agent 不需要自己写循环。

### 6.4 超时

| 层 | 超时 | 行为 |
|---|---|---|
| HTTP 连接读 | 10s | 客户端断开 |
| 等串行锁 | 5s | 返回 `-32002 忙` |
| `gui.command` 内部 | **无超时** | ⚠️ 若 GUI 线程被长任务占住，会一直等 —— 这是已知限制，记入 §14 Q4 |

---

## 7. 传输细节

### 7.1 为什么不做"通用控件寻址"

`setObjectName` 全仓只有 **28 处**。多数按钮、输入框、表格都没有名字，只能靠
控件树位置或可见文字定位 —— 一旦 UI 调整，脚本就会静默点到别的地方。
所以本包的能力**只到"页面级"和"数据级"**，不到"控件级"。

将来若真要控件级，正确的路是**语义寻址**而不是坐标寻址：`editors/` 下 20 个类
已经实现了 `set_data` / `get_data` 鸭子类型，给标签页加一个「本页有哪些字段」的自述
接口，比遍历 `QObject` 树稳定得多。→ 记为 §12 D7。

### 7.2 端口与绑定

- 绑定 `127.0.0.1`，端口用 `0`（由系统分配），**不用固定端口**：避免与其它软件冲突、
  避免被同机扫描猜到。
- ⚠️ Windows 上 `127.0.0.1` 监听**不会**触发防火墙弹窗（只绑回环），但仍需实测确认。
- 只监听 IPv4 回环即可（`::1` 不监听，减少面）。

### 7.3 截图

- `QWidget.grab()` 返回 `QPixmap`，转 `QImage` → `QBuffer` → PNG bytes → base64。
- ⚠️ **高 DPI**：本机实测 `devicePixelRatio = 1.75`，`grab()` 返回**物理像素**
  （1440 逻辑宽 → 2520 物理宽）。默认按 `max_width=1440` 缩放，否则 base64 体积翻倍。
- `target='window'` 取主窗口；`target='tab'` 取当前标签页控件。
- 两种返回：默认 `png_b64`（自包含，适合 agent 直接看图）；给了 `path` 就**存盘**
  并只返回路径（适合人来检查，也避免 JSON 里塞几百 KB）。

---

## 8. 发现与鉴权

### 8.1 句柄文件

服务启动后写一份：

```
<临时目录>/zml_gui_bridge/<pid>.json
{ "pid": 12345, "port": 51234, "token": "9f3a…（32 hex）",
  "app": "IGG-Hydrate", "version": "1.9.42", "started": 1793412345 }
```

- `<临时目录>` = `tempfile.gettempdir()`（Windows 上是 `%LOCALAPPDATA%\Temp`）。
- **外部 agent 的发现方式**：扫这个目录，把所有 `pid.json` 读出来，对每个 `port` 发
  `GET /health`（不需要 token）确认活着。
- **测试控件**用同一份逻辑列出"本机其它实例"，一键填入目标。

### 8.2 生命周期与残留

| 时机 | 动作 |
|---|---|
| 服务启动 | 写 `<pid>.json` |
| 正常停止（菜单关闭 / 窗口关闭 / `atexit`） | 删自己的 json |
| **进程被强杀** | json 残留 → 下次启动时**扫描并清理**：`pid` 不存在的删掉 |

⚠️ Windows 上判 pid 存活不要用 `os.kill(pid, 0)`（在 Windows 上它可能真发信号）。
用 `ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)`，非 0 即存活；
另外再加一层"`GET /health` 连不上也算死"。

### 8.3 鉴权

- token = `secrets.token_hex(16)`，每次启动重新生成（**不持久化**）。
- 请求头 `X-ZML-Bridge-Token`；`/health` 例外（否则无法探活）。
- 威胁模型：**同用户的其它进程**能读 temp 目录里的 json ⇒ 能拿到 token。
  所以 token 防的是"同机不同用户的进程"和"网页里 JS 的 DNS-rebinding 类尝试"，
  **不防**"你自己用户下的脚本"。这一点必须写在界面上（测试控件里显示一行说明）。

---

## 9. 安全模型（先说清楚它挡不住什么）

| 威胁 | 挡得住吗 | 靠什么 |
|---|---|---|
| 别的用户的进程调用 | ✅ | temp 目录按用户隔离 + token |
| 本机别的软件意外连上 | ✅ | 随机端口 + token |
| 恶意网页通过浏览器打本机端口 | ✅（大部分） | token + 只接受 `POST /rpc` + 校验 `Content-Type` |
| **同用户下的脚本 / 你自己跑的 agent** | ❌ **挡不住** | 它读得到 temp 里的 token |
| 能力越界（想执行代码） | ✅ | 白名单里**没有** `run_script` / `exec` |
| 塞爆内存 | ✅（基本） | `text` 200k 字符 / `table` 2000 行上限 |

**一句话**：这条通道的信任假设是「**本机、同一用户 = 可信**」。它比 `ai_assistant`
的聊天通道**宽**（那个只面对模型输出），所以：

1. **默认 `enabled = False`**，不随包启用；
2. 服务**不是启动即起**，要从菜单显式点「启动服务」；
3. 界面上常驻一个可见状态（标题栏或状态栏标注「界面桥：运行中 · 端口 51234」），
   **用户永远能看见它开着**；
4. 每次请求都记一行日志（`log` 方法可读），包括来源端口。

⚠️ 与 `ai_assistant/guard.py` 的关系：那个守卫只注入**绘图子进程**（`sketch.RUNNER`），
拦的是模型写的绘图代码去联网/读写文件。它**不影响**本包在主进程里开监听端口 ——
两者不冲突，但也**不互相保护**。

---

## 10. 测试控件（`BridgeTestPanel`）

> 用户的核心诉求：**打开两个界面，就能自己验证这两个进程能不能通讯。**

### 10.1 界面草图

```
┌ 本机服务 ───────────────────────────────────────────────────────────┐
│ 状态  ● 运行中    端口 51234    PID 18452        [启动] [停止] [复制 token] │
│ 句柄  %TEMP%\zml_gui_bridge\18452.json                              │
│ 请求  12 次   最近 show(show_env_edit) 200 · 3.2ms                  │
└─────────────────────────────────────────────────────────────────────┘
┌ 目标（另一个进程） ────────────────────────────────────────────────┐
│ [✓] 自动发现：找到 1 个其它实例                                     │
│   ▸ PID 22103 · 端口 49877 · IGG-Hydrate 1.9.42 · 本机   [选中]     │
│ 或手动 [127.0.0.1:______] [连接]                                    │
│ 状态  ● 已连接   RTT 3ms                                            │
└─────────────────────────────────────────────────────────────────────┘
┌ 发请求 ────────────────────────────────────────────────────────────┐
│ [ping] [info] [tabs] [screenshot] [show ▾] [自定义 JSON…]           │
└─────────────────────────────────────────────────────────────────────┘
┌ 日志（双向） ──────────────────────────────────────────────────────┐
│ 11:07:03  → ping                                               3ms │
│ 11:07:03  ← {"ok":true,"app":"IGG-Hydrate","pid":22103}            │
│ 11:07:09  → screenshot {"max_width":900}                      41ms │
│ 11:07:09  ← PNG 900×563                                          │
│ 11:07:12  → show {"name":"show_env_edit"}                          │
│ 11:07:12  ← {"ok":true}            ← 此时**对方**界面已切到设置→系统 │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 为什么这个控件本身就是验收工具

它同时扮演两个角色：**本机服务的状态面板** 和 **客户端**。于是不需要任何外部工具，
两个进程就能把整条链路验完。四个判据，从弱到强：

| 步骤 | 操作 | 应当看到 | 证明了什么 |
|---|---|---|---|
| 1 | A 点「ping」 | 收到 B 的 `pid`、`version` | HTTP + token 通 |
| 2 | A 点「tabs」 | 返回的是 **B 的** 标签页列表 | 请求确实进到了 B 的 GUI 线程 |
| 3 | A 点「screenshot」 | A 里显示一张缩略图，**图里是 B 的界面、没有 A 自己的窗口** | 截图来自 B，不是本地伪造 |
| 4 | A 点「show → 环境变量」 | **B 的界面切到「设置 → 系统」**，A 的日志显示 `ok` | 写操作跨进程生效 |

第 3、4 步是硬判据：**A 里能看见 B 的样子、能让 B 动**。这两条过了，通道就是通的。

### 10.3 两个界面怎么来

程序**没有单实例限制**（2026-10-30 实测：全仓无 `CreateMutex` / `QLockFile` / 单实例判断），
所以直接启动两次即可。测试控件里再给一个便利按钮：

- 「再起一个实例」→ `subprocess.Popen([sys.executable, <仓库根>/projects/zml/zml_ui.pyw])`
- ⚠️ 子进程的工作目录要显式给，否则两个实例的「工作路径」相同，`state` 读到的会是同一份数据，
  **看不出差别**。设计上让子进程 `cwd` 指向临时目录下的独立子目录。

### 10.4 落位

作为**本包的标签页**（`gui.get_widget(the_type=BridgeTestPanel, caption='界面桥')`），
与 `ai_assistant` 的 `ChatView` 同一套路：控件只属于这个可关掉的功能，
不进 `ui/tabs/`。

---

## 11. 与既有代码的关系

| 现有件 | 关系 |
|---|---|
| `utils/gui_api.py` `command()` | **唯一**跨线程投递手段，直接用；不改造 |
| `utils/gui_api.py` 每调用一个通道 | **与通道无关**：v1.9.9 删池后无并发上限、不丢弃；"只注册一个命令"的理由是收敛攻击面/审计面（§4.1），串行锁的理由是可预测 |
| `main.py` `get_tab_widget` / `count_tabs` / `get_tab_caption` | `tabs` 方法直接复用，**不改 `main.py`** |
| `ai_assistant/action.py` | **不 import**（§5.4）。设计上各管一段：它管"聊天窗里模型给的 action"，本包管"外部进程的 RPC" |
| `plugins/builtin/` | 不放这里。原因：预计 7 个文件、1500+ 行，且带一个测试控件，单文件塞不下（用户判断一致） |
| `PLAN.md` | 开工前登记一条 `T-YYYYMMDD-NN`，commit 写 `refs:` |

---

## 12. 待定决策（定稿前逐条拍板）

| # | 决策 | 选项 | 推荐 | 理由 |
|---|---|---|---|---|
| **D1** | 包名 | `gui_bridge` / `agent_bridge` / `gui_remote` | `gui_bridge` | 它做的是"进程边界上的桥"，与"给 agent 用"解耦；`scen` 下已有 `ai_assistant`，不重复"AI"字样 |
| **D2** | 传输 | stdlib HTTP / `QLocalServer` 管道 / 文件队列 | **HTTP** | 任何语言可调、`curl` 可验证、将来能包成 MCP；管道要写 Qt 客户端，文件队列没有返回值 |
| **D3** | 协议 | JSON-RPC 2.0 子集 / 自造 `{method,params}` | **JSON-RPC 2.0** | 错误码有标准，且与 MCP 同源 |
| **D4** | 能力清单 | 运行时 `list_all()` + 规则过滤 / 复制 `SHOW_TARGETS` | **运行时过滤** | 零维护、自动跟随插件；复制必然漂移 |
| **D5** | `wait_idle` | 客户端轮询 / 服务端长等待 | **客户端轮询** | 不占串行锁，外部能区分"忙"与"死" |
| **D6** | `screenshot` 返回 | base64 / 落盘路径 / 两者 | **两者**（默认 base64 + `max_width`） | agent 要能直接看图；人检查时要文件 |
| **D7** | 是否做控件级操作 | 不做 / 语义寻址（`get_data` 自述） / 遍历控件树 | **Phase 1 不做** | 无稳定标识（`setObjectName` 仅 28 处）；语义寻址留作 §14 Q1 |
| **D8** | 默认状态与启用方式 | 默认禁用 + 菜单手动启动 / 启用即自动起服务 | **默认禁用 + 手动启动** | 见 §9；用户必须看得见它开着 |
| **D9** | 菜单挂在哪 | `设置 → 界面桥` / `帮助 → AI 控制台` / 独立一级 | `设置 → 界面桥` | 属"高级/实验性设置"，不是帮助文档；与 `ai_assistant` 的「帮助 → AI辅助」分开 |

---

## 13. 实施阶段（每阶段都能单独验收，不一次性铺开）

| 阶段 | 内容 | 验收 |
|---|---|---|
| **P0** | 只做 `discovery.py` + `protocol.py` + 单测（纯 stdlib，不碰 Qt） | 句柄文件读写、残留清理、参数校验的错误码，全部离线可测 |
| **P1** | `server.py` + `methods.py` 的只读子集（`ping`/`info`/`commands`/`tabs`/`screenshot`）+ `zml_plugin.py` | `curl` 能 ping 通、能截到图 |
| **P2** | 写方法（`show`/`text`/`table`/`link`）+ `state` + `wait_idle` | 外部进程能把界面切到指定页 |
| **P3** | `test_panel.py` | §10.2 的四条判据全过（**这是主验收**） |
| **P4** | `client.py` + 文档 + CHANGELOG | 一段 10 行的外部脚本能完成"截图→判断→切页" |

⚠️ P0 的意义：**先把不依赖 Qt 的部分做完并测透**。这一层的 bug 会以"界面偶发不刷新"
的形式出现在很远的地方，最难查。

---

## 14. 未决问题（讨论时请一并定）

- **Q1** `state` 只对实现 `get_data()` 的编辑器有效。**要不要给标签页定一个自述协议**
  （例如 `gui_state()` 返回本页可读字段）？这决定 agent 能"读"到多深。
- **Q2** 现在 `screenshot` 抓的是窗口位图。如果窗口被最小化 / 被遮挡，`grab()` 是否仍给出
  正确内容？（`WA_DontShowOnScreen` 的离屏渲染经验在 `plugins/builtin/architecture.py` 用过，
  但那是"自己画的图"，不是整窗。）→ 实现时需要实测，可能要改用 `render()`。
- **Q3** 是否需要**事件流**（订阅式）：外部注册一个回调地址，界面发生变化时主动 POST 过去？
  代价是要管理回调生命周期、处理回调方不在线。**倾向不做**，用轮询代替。
- **Q4** `gui.command` 没有超时（§6.4）。若 GUI 线程被长任务占住，外部会一直等。
  要不要在服务端加"看门狗"（>30s 未返回就先回 `-32002` 并记日志）？
  ⚠️ 但那只解决"告诉调用方忙"，解决不了"GUI 线程真的被占住" —— 那是另一个问题。
- **Q5** 两个实例的 `cwd` 相同时，`state` 会读到同一份数据，测试时看不出差别。
  是否要在测试控件里强制子进程用独立 `cwd`？（§10.3 已按"是"设计，需确认。）
- **Q6** 这条通道将来要不要直接做成 **MCP server**？如果是，`server.py` 之外再加一个
  `mcp.py`（把同一批 method 描述成 tools），本设计的协议层正好对得上。

---

## 15. 实施记录（MVP，2026-10-30）

这一节记的是**跑出来的事实**，不是设计意图。设计稿在上面，两者不一致时以本节为准。

### 15.1 已落地

| 文件 | 行数 | 状态 |
|---|---|---|
| `protocol.py` | 194 | ✅ 错误码 / 请求校验 / 命令白名单 |
| `discovery.py` | 162 | ✅ 句柄写入、扫描、死 pid 清理 |
| `client.py` | 165 | ✅ `urllib` 客户端 + `discover()` |
| `methods.py` | 246 | ✅ `ping` / `info` / `commands` / `tabs` / `show` / `screenshot` |
| `server.py` | 315 | ✅ HTTP + token + 串行锁 + 访问日志（非 200 一律 `Connection: close`） |
| `test_panel.py` | 348 | ✅ 本机服务状态 + 目标发现 + 发请求 + 双向日志 |
| `zml_plugin.py` | 90 | ✅ `# ** enabled = False`；菜单「设置 → 界面桥（实验）」 |

**未实现**（按设计的 P2 之后）：`state`、`wait_idle`、`log` 三个方法。

### 15.2 实测环境与结果

- 环境：WinPython 3.13 + PyQt6、Windows、`zmlx` 版本 **1.9.7**；
- 方式：进程 A = 手工建 `MainWindow` + `gui.set(...)` + `__console_kernel(None)` + 起服务；
  进程 B = **纯脚本进程**（只 import `client.py`，不碰 Qt），靠临时目录的句柄文件发现 A。

| 判据（§10.2） | 结果 | 实测值 |
|---|---|---|
| 1 `ping` 拿到对方 pid | ✅ | `{'pid': 35104, 'version': '1.9.7', 'uptime': 3.6}` |
| 2 `tabs` 返回对方的标签页 | ✅ | 初始 `count=0`；`show_changelog` 后 `count=1, caption='修改记录'` |
| 3 `screenshot` 图里是对方的界面 | ✅ | 1100×705 PNG（288 KB），图内是 A 的窗口 + 「修改记录」页 |
| 4 `show` 之后对方界面真的切了 | ✅ | 第二次 `tabs` 的 `current` 指向「修改记录」 |
| 白名单拒绝 | ✅ | `show('run_script')` → `code=-32601`「命令未对界面桥开放」 |

- `commands` 返回 **45** 个允许的只读入口（运行时取自 `list_all()`，未维护静态副本）；
- 单次调用耗时：`ping` **34 ms**、`tabs` **17 ms**（含投递到 GUI 线程的往返）；
- 死进程残留清理：强杀宿主后句柄文件留下，下一次 `discover()` 自动删净（实测 `[]`）。

### 15.3 踩到的坑（第一条最重要）

1. **`gui.get()` 返回的是 `GuiApi`，不是主窗口。** 第一版 `_window()` 直接
   `gui.get().windowTitle()`，报 `'GuiApi' object has no attribute 'windowTitle'`。

   正确做法就是**一行** `gui.window()` —— 不需要绕到 `get_func`::

       window = gui.window()

   两条机制让这一行成立：

   - `GuiBuffer.__getattr__` 对**任何**名字都返回一个 `Agent`（`gui_buffer.py:317`），
     所以 `gui.<任意名>` 永远拿得到代理，调用时才会去命令表里查；
   - `MainWindow.__init_gui_api` 末尾对 `window` 调过 `mark_direct`
     （`main.py:445-446`），于是 `command('window')` **跳过投递**、直接执行注册的
     `lambda: self`。

   headless 时 `GuiBuffer.command` 直接返回 `None`（`gui_buffer.py:81-84`），不抛异常，
   所以上面那行在无界面进程里也安全。

   ⚠️ **2026-10-30 更正**：第一版曾写成 `api.get_func('window')()`，虽然结果等价，
   但绕过了 `mark_direct` 的设计意图，还依赖 `GuiApi.get_func` 这个内部细节。
   已改回 `gui.window()`（用户指出）。
2. **`QPlainTextEdit` 里长 JSON 折行后第二行顶格**，视觉上不够整齐（测试面板日志区）。
   不影响功能，暂不处理。
3. `test_panel` 的模块级单例 `_SERVER` 放在 UI 文件里，语义上更像 `server.py` 的东西。
   MVP 阶段接受，后续若加第二个入口再搬。

### 15.4 与设计稿的偏差

| 项 | 设计 | 实现 | 原因 |
|---|---|---|---|
| `info.window.dark` | — | 增加了 `gui.in_dark_mode()` | agent 判断截图配色时需要 |
| `screenshot` 返回 | base64 | base64 + `bytes` 长度 | 便于日志判断体积 |
| 测试面板截图 | 面板内显示缩略图 | **存临时文件 + `gui.open_image` 开标签页** | 复用现成的大图查看器，且"开一个标签显示对方的界面"这个动作本身就是最好的证据 |
| 测试面板「再起一个实例」 | 设计里有 | **未实现** | 手动双击两个实例更简单；且 `cwd` 问题（Q5）还没定 |

### 15.5 下一步（按优先级）

1. **两个真实界面互测**（不改代码即可做）：开两份程序 → 各自「启动服务」→ 刷新发现 → 截图；
2. `state` / `wait_idle`（P2 的剩余部分），`state` 先只支持 `get_data()` 的页面；
3. 把 `ReadMe.md` 的 Q2（窗口最小化时 `grab()` 是否可靠）实测掉；
4. 定稿 D7 / Q1 / Q4，再谈是否进 `CHANGELOG` 与版本号（当前是**新包、默认禁用**，
   对外不可见，所以暂不写 CHANGELOG）。
