from zmlx.ui.tabs.about import About
from zmlx.ui.tabs.app_path_edit import AppPathEdit
from zmlx.ui.widgets.code_edit import CodeEdit
from zmlx.ui.tabs.code_history_view import CodeHistoryView
from zmlx.ui.tabs.cwd_view import CwdView
from zmlx.ui.tabs.demo_view import DemoView
from zmlx.ui.tabs.env_edit import EnvEdit
from zmlx.ui.tabs.feedback_tool import FeedbackTool
from zmlx.ui.widgets.label import Label
from zmlx.ui.widgets.license_button import LicenseButton
from zmlx.ui.tabs.license_register import LicenseRegister
from zmlx.ui.tabs.output_history_view import OutputHistoryView
from zmlx.ui.widgets.output_widget import OutputWidget
from zmlx.ui.tabs.readme_browser import ReadMeBrowser
from zmlx.ui.tabs.reg_tool import RegTool
from zmlx.ui.tabs.plugin_list_edit import PluginListEdit
from zmlx.ui.tabs.tab_detail_view import TabDetailView
from zmlx.ui.widgets.tab_widget import TabWidget
from zmlx.ui.widgets.text_browser import TextBrowser
from zmlx.ui.tabs.text_file_edit import TextFileEdit
from zmlx.ui.tabs.timer_view import TimerView
from zmlx.ui.widgets.version_button import VersionButton

_keep = [
    CodeEdit, TextFileEdit, PluginListEdit, AppPathEdit, EnvEdit, TextBrowser, ReadMeBrowser, TabDetailView,
    CodeHistoryView, OutputHistoryView, DemoView, CwdView, TimerView, About, FeedbackTool, RegTool, Label,
    VersionButton, LicenseButton, TabWidget, OutputWidget, LicenseRegister
]
