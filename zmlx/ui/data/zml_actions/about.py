# ** icon = 'info.png'

from zml import *
from zmlx import get_latest_version

latest_version = get_latest_version()

while core.has_log():
    core.pop_log()

summary = lic.summary

text = about()

text = text + f"""

latest version: {latest_version}
website: https://gitee.com/geomech/hydrate
    
license: {summary}
"""

if latest_version is not None and latest_version > version:
    text = text + "\nYou are not using the latest version, please update. "
else:
    text = text + "\nThanks for using! "

if summary is None:
    while core.has_log():
        print(core.pop_log())
    print('\n\n')

print(text)
gui.about('About', text)
