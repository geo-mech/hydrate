"""图标源文件：全部在 24x24 的坐标系里描述，由 ``build.py`` 渲染成 PNG。

坐标约定
--------
- 画布 24x24，**不画底衬**：图形以外的部分是透明的，图标跟随所在位置的底色；
- 描边型图标：``stroke-width`` 2、``stroke-linecap/linejoin`` 均为 round；
- 填充型图标：自上而下、由浅到深。

改图标只改这个字典（加一个 key 就是一个新图标），然后运行 ``build.py`` ——
它会写出 ``svg/<name>.svg``（可再编辑的源文件）并渲染
``zmlx/ui/data/zml_icons/<name>.png``。

⚠️ 这里的 key 就是 ``settings.load_icon(name)`` 里的 name，改名等于改 API：
``zmlx/ui/main.py``、各插件的 ``add_action(..., icon=...)`` 都按名字引用。
"""

BLUE = '#2563EB'
GREEN = '#059669'
RED = '#DC2626'
AMBER = '#F59E0B'
SLATE = '#334155'
INK = '#1E293B'
SKY = '#0EA5E9'

S = 'fill="none" stroke-linecap="round" stroke-linejoin="round"'

ICONS = {}

ICONS['open'] = f'''
<path d="M3.4 18.6V6a1.2 1.2 0 0 1 1.2-1.2h4.6l2.1 2.4h6.9a1.2 1.2 0 0 1 1.2 1.2v10.2a1.2 1.2 0 0 1-1.2 1.2H4.6a1.2 1.2 0 0 1-1.2-1.2z"
      fill="{AMBER}"/>
<path d="M3.9 10.4h16.2" stroke="#fff" stroke-width="1.2" opacity=".85"/>
'''

ICONS['new'] = f'''
<path d="M6.4 20.4a1.4 1.4 0 0 1-1.4-1.4V4.6a1.4 1.4 0 0 1 1.4-1.4h7.4L18.2 7.6v2.4"
      fill="{BLUE}"/>
<path d="M13.8 3.2v4.4h4.4z" fill="#93C5FD"/>
<circle cx="16.6" cy="16.8" r="5.2" fill="#fff"/>
<circle cx="16.6" cy="16.8" r="4.2" fill="{BLUE}"/>
<path d="M16.6 14.4v4.8M14.2 16.8h4.8" {S} stroke="#fff" stroke-width="1.9"/>
'''

ICONS['save'] = f'''
<path d="M5 3.4h10.6l4 4v12.2a1.4 1.4 0 0 1-1.4 1.4H5a1.4 1.4 0 0 1-1.4-1.4V4.8A1.4 1.4 0 0 1 5 3.4z"
      fill="{BLUE}"/>
<rect x="7.4" y="3.4" width="8" height="6" rx="1" fill="#fff"/>
<rect x="12.9" y="4.6" width="1.7" height="3.3" rx=".85" fill="{BLUE}"/>
<rect x="6.4" y="13" width="10.2" height="8" rx="1.2" fill="#fff"/>
'''

ICONS['saveas'] = f'''
<path d="M3.2 16.6V6.4a1.2 1.2 0 0 1 1.2-1.2h10.4l3.4 3.4v8" {S} stroke="{SLATE}" stroke-width="1.9"/>
<path d="M5.6 9.6h6.4M5.6 13h4.4" {S} stroke="{SLATE}" stroke-width="1.9"/>
<circle cx="16.8" cy="16.6" r="4.6" fill="{GREEN}"/>
<path d="M16.8 14.2v4.8M14.4 16.6h4.8" {S} stroke="#fff" stroke-width="1.8"/>
'''

ICONS['import'] = f'''
<path d="M10.8 3.2h8.2a1.4 1.4 0 0 1 1.4 1.4v14.8a1.4 1.4 0 0 1-1.4 1.4h-8.2" {S}
      stroke="{SKY}" stroke-width="2"/>
<path d="M3.4 12h10.4M9.6 7.8l4.2 4.2-4.2 4.2" {S} stroke="{SKY}" stroke-width="2.1"/>
'''

ICONS['export'] = f'''
<path d="M14.2 3.2H4.4v17.6h9.8" {S} stroke="{SLATE}" stroke-width="1.9"/>
<path d="M9.4 12h11.2M16.4 7.8l4.2 4.2-4.2 4.2" {S} stroke="{AMBER}" stroke-width="2.1"/>
'''

ICONS['begin'] = f'''
<circle cx="12" cy="12" r="9.1" fill="{GREEN}"/>
<path d="M10 7.6l6.2 4.4-6.2 4.4z" fill="#fff"/>
'''

ICONS['pause'] = f'''
<circle cx="12" cy="12" r="9.1" fill="{AMBER}"/>
<rect x="8.2" y="7.6" width="2.7" height="8.8" rx="1.35" fill="#fff"/>
<rect x="13.1" y="7.6" width="2.7" height="8.8" rx="1.35" fill="#fff"/>
'''

# 「继续」与「运行」是同一个动作（都是把内核从暂停处放开），共用一张图；
# 单独留一个 key 是为了让 ``icon='resume'`` 在名字上也说得通。
ICONS['resume'] = ICONS['begin']

ICONS['stop'] = f'''
<circle cx="12" cy="12" r="9.1" fill="{RED}"/>
<rect x="8.1" y="8.1" width="7.8" height="7.8" rx="1.5" fill="#fff"/>
'''

ICONS['kill'] = f'''
<circle cx="12" cy="12" r="9.1" fill="{RED}"/>
<path d="M8.8 8.8l6.4 6.4M15.2 8.8l-6.4 6.4" {S} stroke="#fff" stroke-width="2.3"/>
'''

ICONS['console'] = f'''
<rect x="2.6" y="3.6" width="18.8" height="16.8" rx="3" fill="{INK}"/>
<rect x="2.6" y="3.6" width="18.8" height="16.8" rx="3" fill="none" stroke="#CBD5E1" stroke-width="1"/>
<path d="M6.8 9.2l3 2.8-3 2.8" {S} stroke="#4ADE80" stroke-width="1.9"/>
<path d="M12.4 14.8h4.6" {S} stroke="{SKY}" stroke-width="1.9"/>
'''

ICONS['clean'] = f'''<rect x="6.2" y="13.6" width="10.6" height="5.2" rx="1.5" transform="rotate(-45 11.5 16.2)" fill="#F59E0B"/>
<path d="M12.4 3.6l8.2 8.2" fill="none" stroke-linecap="round" stroke="#F59E0B" stroke-width="3.6"/>
<path d="M3.4 20.4h17.2" fill="none" stroke-linecap="round" stroke="#0EA5E9" stroke-width="2"/>
'''

ICONS['close_all'] = f'''
<rect x="3" y="3" width="12.6" height="12.6" rx="2.4" {S} stroke="{SLATE}" stroke-width="1.8"/>
<path d="M8.2 8.6h11.2a1.6 1.6 0 0 1 1.6 1.6v9.2a1.6 1.6 0 0 1-1.6 1.6H10" {S}
      stroke="{SLATE}" stroke-width="1.8"/>
<path d="M10.4 9.8l4.4 4.4M14.8 9.8l-4.4 4.4" {S} stroke="{RED}" stroke-width="2.2"/>
'''

ICONS['set'] = f'''
<path d="M12 2.8l7.4 4.2v9.8L12 21.1 4.6 16.8V7z" fill="{SLATE}"/>
<circle cx="12" cy="12" r="3" fill="none" stroke="#fff" stroke-width="1.9"/>
<circle cx="12" cy="12" r=".9" fill="#fff"/>
'''

ICONS['variables'] = f'''
<rect x="2.6" y="4.6" width="18.8" height="14.8" rx="2.6" fill="{INK}"/>
<rect x="2.6" y="4.6" width="18.8" height="14.8" rx="2.6" fill="none" stroke="#CBD5E1" stroke-width="1"/>
<path d="M9.2 9.2L6.8 12l2.4 2.8M14.8 9.2L17.2 12l-2.4 2.8" {S} stroke="#4ADE80" stroke-width="1.9"/>
'''

ICONS['plugin'] = f'''
<path d="M4.2 4.8a1 1 0 0 1 1-1h3.9v2a2 2 0 1 0 4 0v-2h5.7a1 1 0 0 1 1 1v4.6h-2a2 2 0 1 0 0 4h2v6a1 1 0 0 1-1 1h-6v-2a2 2 0 1 0-4 0v2H5.2a1 1 0 0 1-1-1v-6h2a2 2 0 1 0 0-4h-2z"
      fill="{BLUE}"/>
'''

ICONS['reg'] = f'''
<rect x="3.2" y="3" width="12.2" height="18" rx="2" {S} stroke="{SLATE}" stroke-width="1.8"/>
<path d="M6.2 8h6.2M6.2 12h6.2M6.2 16h3.6" {S} stroke="{SLATE}" stroke-width="1.8"/>
<circle cx="16.8" cy="8.4" r="2.9" fill="{SKY}"/>
<path d="M11.2 20.2c0-3.2 2.5-5.4 5.6-5.4s5.6 2.2 5.6 5.4z" fill="{SKY}"/>
'''

ICONS['refresh'] = f'''
<path d="M19.4 12a7.4 7.4 0 1 1-2.2-5.3" {S} stroke="{SKY}" stroke-width="2.2"/>
<path d="M19.8 3.6v4.7h-4.7" {S} stroke="{SKY}" stroke-width="2.2"/>
'''

ICONS['info'] = f'''
<circle cx="12" cy="12" r="9.1" fill="{BLUE}"/>
<circle cx="12" cy="7.7" r="1.35" fill="#fff"/>
<path d="M12 10.9v6.3" {S} stroke="#fff" stroke-width="2.2"/>
'''

ICONS['demo'] = f'''<rect x="2.5" y="3.6" width="19" height="16.8" rx="2.8" fill="#0EA5E9"/>
<rect x="5.1" y="6.6" width="5.8" height="4.8" rx="1" fill="#fff" opacity=".92"/>
<path d="M5.1 14.2h6.6M5.1 16.9h4.4" fill="none" stroke-linecap="round" stroke="#fff" stroke-width="1.7" opacity=".92"/>
<circle cx="16.2" cy="12.6" r="4.7" fill="#fff"/>
<path d="M14.7 10.3l3.8 2.3-3.8 2.3z" fill="#0EA5E9"/>
'''

ICONS['cwd'] = f'''
<path d="M2.6 6.6a1.4 1.4 0 0 1 1.4-1.4h4.9l2.1 2.4h9a1.4 1.4 0 0 1 1.4 1.4v9.6a1.4 1.4 0 0 1-1.4 1.4H4a1.4 1.4 0 0 1-1.4-1.4z"
      fill="{AMBER}"/>
'''

ICONS['clock'] = f'''
<circle cx="12" cy="12.4" r="8" {S} stroke="{INK}" stroke-width="2"/>
<path d="M12 8v4.8l3.1 1.8" {S} stroke="{RED}" stroke-width="2"/>
<path d="M9.9 3.2h4.2" {S} stroke="{INK}" stroke-width="2"/>
'''

ICONS['matplotlib'] = f'''
<rect x="3.2" y="3.2" width="17.6" height="17.6" rx="3" {S} stroke="{INK}" stroke-width="1.8"/>
<path d="M5.6 17V7.4M5.6 17h13.2" {S} stroke="{INK}" stroke-width="1.8"/>
<rect x="7.8" y="12.2" width="2.5" height="4.8" rx=".7" fill="{SKY}"/>
<rect x="11.4" y="8.8" width="2.5" height="8.2" rx=".7" fill="{AMBER}"/>
<rect x="15" y="10.6" width="2.5" height="6.4" rx=".7" fill="{GREEN}"/>
'''

# ---- 外部链接 / 文档类：首页、期刊、反馈、联系方式、更新、退出 ----
ICONS['home'] = f'''
<path d="M12 2.7L2.8 10.6a1 1 0 0 0 .65 1.76H5.3V20a1.3 1.3 0 0 0 1.3 1.3h10.8A1.3 1.3 0 0 0 18.7 20v-7.64h1.85a1 1 0 0 0 .65-1.76z"
      fill="{BLUE}"/>
<rect x="9.4" y="14.2" width="5.2" height="7.1" rx="1.2" fill="#fff"/>
'''

ICONS['web'] = f'''<rect x="2.5" y="3.4" width="19" height="17.2" rx="2.8" fill="#0EA5E9"/>
<path d="M9.7 6.9h7.6" fill="none" stroke-linecap="round" stroke="#fff" stroke-width="1.8" opacity=".9"/>
<circle cx="5.6" cy="6.9" r=".85" fill="#fff" opacity=".9"/>
<circle cx="12" cy="14.3" r="5" fill="#fff"/>
<circle cx="12" cy="14.3" r="2.2" fill="none" stroke="#0EA5E9" stroke-width="1.2"/>
<path d="M7 14.3h10" fill="none" stroke="#0EA5E9" stroke-width="1.2"/>
<path d="M12 9.3a5 5 0 0 1 0 10M12 9.3a5 5 0 0 0 0 10" fill="none" stroke="#0EA5E9" stroke-width="1.2"/>
'''

ICONS['issues'] = f'''
<path d="M3.4 10.2a5 5 0 0 1 5-5h7.2a5 5 0 0 1 5 5v3.6a5 5 0 0 1-5 5H9.9l-4.7 2.3a.8.8 0 0 1-1.2-.72v-1.6a5 5 0 0 1-.6-2.4z"
      fill="{SKY}"/>
<circle cx="8.6" cy="12" r="1.35" fill="#fff"/>
<circle cx="12" cy="12" r="1.35" fill="#fff"/>
<circle cx="15.4" cy="12" r="1.35" fill="#fff"/>
'''

ICONS['contact'] = f'''
<rect x="2.6" y="5.2" width="18.8" height="13.6" rx="2.6" fill="{BLUE}"/>
<path d="M4.6 7.6l6.5 4.8a1.6 1.6 0 0 0 1.8 0l6.5-4.8" {S} stroke="#fff" stroke-width="1.8"/>
'''

ICONS['update'] = f'''
<circle cx="12" cy="12" r="9.1" fill="{GREEN}"/>
<path d="M12 6.4v8.2M8.9 11.7L12 14.8l3.1-3.1" {S} stroke="#fff" stroke-width="2"/>
<path d="M7.9 17.2h8.2" {S} stroke="#fff" stroke-width="2"/>
'''

ICONS['quit'] = f'''
<circle cx="12" cy="12" r="9.1" fill="{RED}"/>
<path d="M12 6.6v6.2" {S} stroke="#fff" stroke-width="2.2"/>
<path d="M8.2 8.7a5.4 5.4 0 1 0 7.6 0" {S} stroke="#fff" stroke-width="2.1"/>
'''

# ---- 文件类型 / 解释器 ----
ICONS['python'] = f'''<path d="M14.25 .18l .9 .2 .73 .26 .59 .3 .45 .32 .34 .34 .25 .34 .16 .33 .1 .3 .04 .26 .02 .2 -.01 .13V8.5l -.05 .63 -.13 .55 -.21 .46 -.26 .38 -.3 .31 -.33 .25 -.35 .19 -.35 .14 -.33 .1 -.3 .07 -.26 .04 -.21 .02H8.77 l -.69 .05 -.59 .14 -.5 .22 -.41 .27 -.33 .32 -.27 .35 -.2 .36 -.15 .37 -.1 .35 -.07 .32 -.04 .27 -.02 .21v3.06H3.17l -.21 -.03 -.28 -.07 -.32 -.12 -.35 -.18 -.36 -.26 -.36 -.36 -.35 -.46 -.32 -.59 -.28 -.73 -.21 -.88 -.14 -1.05 -.05 -1.23 .06 -1.22 .16 -1.04 .24 -.87 .32 -.71 .36 -.57 .4 -.44 .42 -.33 .42 -.24 .4 -.16 .36 -.1 .32 -.05 .24 -.01h .16l .06 .01h8.16v -.83H6.18l -.01 -2.75 -.02 -.37 .05 -.34 .11 -.31 .17 -.28 .25 -.26 .31 -.23 .38 -.2 .44 -.18 .51 -.15 .58 -.12 .64 -.1 .71 -.06 .77 -.04 .84 -.02 1.27 .05z" fill="#3776AB"/>
<path d="M20.96 10.29l .28 .06 .32 .12 .35 .18 .36 .27 .36 .35 .35 .47 .32 .59 .28 .73 .21 .88 .14 1.04 .05 1.23 -.06 1.23 -.16 1.04 -.24 .86 -.32 .71 -.36 .57 -.4 .45 -.42 .33 -.42 .24 -.4 .16 -.36 .09 -.32 .05 -.24 .02 -.16 -.01h-8.22v .82h5.84l .01 2.76 .02 .36 -.05 .34 -.11 .31 -.17 .29 -.25 .25 -.31 .24 -.38 .2 -.44 .17 -.51 .15 -.58 .13 -.64 .09 -.71 .07 -.77 .04 -.84 .01 -1.27 -.04 -1.07 -.14 -.9 -.2 -.73 -.25 -.59 -.3 -.45 -.33 -.34 -.34 -.25 -.34 -.16 -.33 -.1 -.3 -.04 -.25 -.02 -.2 .01 -.13v -5.34l .05 -.64 .13 -.54 .21 -.46 .26 -.38 .3 -.32 .33 -.24 .35 -.2 .35 -.14 .33 -.1 .3 -.06 .26 -.04 .21 -.02 .13 -.01h5.84l .69 -.05 .59 -.14 .5 -.21 .41 -.28 .33 -.32 .27 -.35 .2 -.36 .15 -.36 .1 -.35 .07 -.32 .04 -.28 .02 -.21V6.07h2.09l .14 .01z" fill="#FFD43B"/>
<circle cx="9.64" cy="4.11" r=".86" fill="#fff"/>
<circle cx="14.32" cy="19.89" r=".86" fill="#fff"/>
'''

ICONS['pdf'] = f'''
<path d="M6.4 2.9h7.3l4.4 4.4v13.2a1.6 1.6 0 0 1-1.6 1.6H6.4a1.6 1.6 0 0 1-1.6-1.6V4.5a1.6 1.6 0 0 1 1.6-1.6z"
      fill="#E11D48"/>
<path d="M13.7 2.9v3.2a1.2 1.2 0 0 0 1.2 1.2h3.2z" fill="#FDA4AF"/>
<rect x="4.5" y="13.2" width="13.2" height="7" rx="1.9" fill="#fff"/>
<text x="11.1" y="18.6" text-anchor="middle" font-family="Microsoft YaHei, SimHei, Arial, sans-serif"
      font-size="4.6" font-weight="700" letter-spacing=".2" fill="#E11D48">PDF</text>
'''

# ---------------------------------------------------------------- 应用图标
# 与工具栏图标规则不同：它自己就是完整画面（整块渐变圆角方块），不套底衬。
# 语义：蓝色地层里立着几根白色井筒，底部两道浅蓝是水合物层 / 流体界面。
APP_ICON = '''
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#60A5FA"/>
    <stop offset=".55" stop-color="#2563EB"/>
    <stop offset="1" stop-color="#1E3A8A"/>
  </linearGradient>
</defs>
<rect x="0" y="0" width="24" height="24" rx="5.2" ry="5.2" fill="url(#bg)"/>
<circle cx="12" cy="12" r="11.2" fill="none" stroke="#FFFFFF" stroke-width="0.55" opacity=".16"/>
<rect x="2.6" y="13.1" width="18.8" height="3.3" rx="1.4" fill="#BAE6FD" opacity=".62"/>
<rect x="2.6" y="17" width="18.8" height="3.9" rx="1.4" fill="#7DD3FC" opacity=".38"/>
<rect x="5.2" y="4.4" width="3.5" height="15.4" rx="1.75" fill="#FFFFFF"/>
<rect x="10.2" y="6.1" width="3.5" height="13.7" rx="1.75" fill="#FFFFFF" opacity=".94"/>
<rect x="15.2" y="7.8" width="3.5" height="12" rx="1.75" fill="#FFFFFF" opacity=".86"/>
<rect x="10.2" y="9.4" width="3.5" height="1.7" rx="0.7" fill="#2563EB" opacity=".9"/>
'''


def svg(body, size=24):
    """组装一个 SVG。size=24 时坐标即原值；其它尺寸整体缩放。

    ``body`` 是 24x24 坐标系里的图形；整张图**没有底衬**，图形以外保持透明，
    这样图标会跟随所在位置的底色（浅色 / 深色主题、工具栏、菜单）。

    ⚠️ 缩放必须套住**所有**图形元素：早先底衬 rect 是在缩放组**外面**拼进去的，
    于是它只盖住左上角 24px 的一小块、其余透明 —— 渲染出来就是图标左上角那一小块
    白斑。底衬已经去掉，但这条教训对将来要加的整块背景同样成立。
    """
    k = size / 24.0
    scale = '' if size == 24 else f'<g transform="scale({k:g})">'
    close = '' if size == 24 else '</g>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" '
            f'height="{size}" viewBox="0 0 {size} {size}">'
            f'{scale}{body}{close}</svg>')
