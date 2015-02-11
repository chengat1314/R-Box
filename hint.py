import sublime
import sublime_plugin
import re
import json
import os


def load_jsonfile():
    jsonFilepath = os.path.join(sublime.packages_path(),
                                'R-Box', 'support', 'hint.json')
    data = None
    with open(jsonFilepath, "r") as f:
        data = json.load(f)
    return data


class RBoxStatusListener(sublime_plugin.EventListener):
    cache = {}
    last_row = 0

    def check(self):
        settings = sublime.load_settings('R-Box.sublime-settings')
        return settings.get("status_bar_hint", True)

    def RStatusUpdater(self, view):
        point = view.sel()[0].end() if len(view.sel()) > 0 else 0
        if not view.score_selector(point, "source.r"):
            view.set_status("r_box", "")
            return
        if not self.check():
            return

        if not self.cache:
            self.cache = dict(load_jsonfile())

        this_row = view.rowcol(point)[0]
        sel = view.sel()
        if len(sel) != 1:
            return
        if sel[0].begin() != sel[0].end():
            return
        contentb = view.substr(sublime.Region(view.line(point).begin(), point))
        m = re.match(r".*?([a-zA-Z0-9.]+)\($", contentb)
        if not m:
            return
        view.set_status("r_box", "")
        func = m.group(1)

        if func in self.cache:
            call = self.cache[func]
            self.last_row = this_row
            view.set_status("r_box", call)
            view.settings().set("r_box_status", True)

    def on_modified(self, view):
        if view.is_scratch() or view.settings().get('is_widget'):
            return
        point = view.sel()[0].end() if len(view.sel()) > 0 else 0
        if not view.score_selector(point, "source.r"):
            return
        if not self.check():
            return
        # run it in another thread
        sublime.set_timeout(lambda: self.RStatusUpdater(view), 1)

    def on_selection_modified(self, view):
        if view.is_scratch() or view.settings().get('is_widget'):
            return
        point = view.sel()[0].end() if len(view.sel()) > 0 else 0
        if not view.score_selector(point, "source.r"):
            return
        if not self.check():
            return
        this_row = view.rowcol(point)[0]
        if this_row != self.last_row:
            view.set_status("r_box", "")
            view.settings().set("r_box_status", False)

    def on_post_save(self, view):
        if view.is_scratch() or view.settings().get('is_widget'):
            return
        point = view.sel()[0].end() if len(view.sel()) > 0 else 0
        if not view.score_selector(point, "source.r"):
            return
        if not self.check():
            return
        sublime.set_timeout(lambda: self.capture_functions(view), 1)

    def on_load(self, view):
        if view.is_scratch() or view.settings().get('is_widget'):
            return
        point = view.sel()[0].end() if len(view.sel()) > 0 else 0
        if not view.score_selector(point, "source.r"):
            return
        if not self.check():
            return
        sublime.set_timeout(lambda: self.capture_functions(view), 1)

    def on_activated(self, view):
        if view.is_scratch() or view.settings().get('is_widget'):
            return
        point = view.sel()[0].end() if len(view.sel()) > 0 else 0
        if not view.score_selector(point, "source.r"):
            return
        if not self.check():
            return
        sublime.set_timeout(lambda: self.capture_functions(view), 1)
        # print(self.cache)

    def capture_functions(self, view):
        if not self.cache:
            self.cache = dict(load_jsonfile())
        funcsel = view.find_all(r"""\b(?:[a-zA-Z0-9._:]*)\s*(?:<-|=)\s*function\s*"""
                                r"""(\((?:(["\'])(?:[^\\]|\\.)*?\2|#.*$|[^()]|(?1))*\))""")
        for s in funcsel:
            m = re.match(r"^([^ ]+)\s*(?:<-|=)\s*(?:function)\s*(.+)$", view.substr(s))
            if m:
                self.cache.update({m.group(1): m.group(1)+m.group(2)})


class RBoxCleanStatus(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        view.set_status("r_box", "")
        view.settings().set("r_box_status", False)
