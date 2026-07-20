#!/usr/bin/env python3
# coding: utf-8
from textual.app import ComposeResult
from textual.widget import Widget
# Copyright 2026 by BurnoutDV, <development@burnoutdv.com>
#
# This file is part of EpisodeNames.
#
# EpisodeNames is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# EpisodeNames is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @license GPL-3.0-only <https://www.gnu.org/licenses/gpl-3.0.en.html>

import re
from typing import ClassVar
from datetime import date, datetime, timedelta

from textual import on
from textual.binding import Binding, BindingType
from textual.widgets import Tabs, Tab, Input, TextArea

from episode_names.Utility import i18n

_RESTRICT_TYPES = {
    # ? ISO DATE + whatever germans use, eg: 2026-05-12 | 12.05.2026
    'date': r"^(([0]?[1-9]|[1-2][0-9]|[3][0-1])\.([1][0-2]|[0]?[1-9])\.(([0-9]{4}|[0-9]{2}))|([0-9]{4})-([0][1-9]|[1][0-2])-([0][1-9]|[1-2][0-9]|[3][0-1]))"
}

def binding_text(key_bind: str, content: str) -> str:
    return f"[bold][$accent]{key_bind}[/][/bold] {content}"

class DateInput(Input):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(key="ctrl+plus", action="increment_date", description="adds a day", show=False),
        Binding(key="up", action="increment_date", description="adds a day", show=False),
        Binding(key="ctrl+minus", action="decrement_date", description="substracts a day", show=False),
        Binding(key="down", action="decrement_date", description="substracts a day", show=False),
    ]
    def __init__(self, *bit, **bops):
        # TODO: add date format restriction
        # for this I need to write an validator and attach it on init/afterwards
        super().__init__(*bit, **bops)

    def action_increment_date(self):
        # TODO: make this more flexible
        a_date = datetime.strptime(self.value, "%d.%m.%Y").date()
        a_date = a_date + timedelta(days=1)
        self.value = a_date.strftime("%d.%m.%Y")

    def action_decrement_date(self):
        a_date = datetime.strptime(self.value, "%d.%m.%Y").date()
        a_date = a_date + timedelta(days=-1)
        self.value = a_date.strftime("%d.%m.%Y")

TEXT_ADD_ONE = "Increments one number by one"
TEXT_SUB_ONE = "Decrements one number by one"

class IncrementalInput(Input):
    """
    A carbon copy of Textual Input with the minimal difference that
    IF there is a single number in the string,not two different number, not three
    but exactly one number, arrow down and up will increment that one number.
    If for some reasons there is more than one number, nothing happens
    """
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding(key="ctrl+plus", action="increment", description=TEXT_ADD_ONE, show=False),
        Binding(key="up", action="increment", description=TEXT_ADD_ONE, show=False),
        Binding(key="ctrl+minus", action="decrement", description=TEXT_SUB_ONE, show=False),
        Binding(key="down", action="decrement", description=TEXT_SUB_ONE, show=False),
    ]
    def _action_increment(self):
        if match := self._see_if_exact_one_number():
            self.value = match.group(1) + str(int(match.group(2))+1) + match.group(3)

    def _action_decrement(self):
        if match := self._see_if_exact_one_number():
            if int(match.group("number")) > 0: # I don't know why gave the thing a name
                self.value = match.group(1) + str(int(match.group(2))-1) + match.group(3)

    def _see_if_exact_one_number(self) -> re.Match | bool:
        pattern = r"^([^0-9]*)(?P<number>\d+)([^0-9]*)$"
        if match := re.search(pattern, self.value):
            try:
                int(match.group('number'))
            except TypeError:
                return False
            return match
        return False

class EnPageMarker(Widget):
    DEFAULT_CSS = """
    EnPageMarker {
        height: 2;
        dock: top;
        Tabs {
            height: 2;
            background: $footer-background;
        }
        Tab {
            height: 1;
            background: $footer-background;
            color: $footer-foreground;
        }
    }
    """
    def __init__(self, active_tab: str) -> None:
        self.active_tab = active_tab
        self.switch_map = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        # custom tabs for dual color?
        so_many_tabs = []
        for each in self.app.BINDINGS:
            self.switch_map[each.key] = each.action
            if each.key == "escape":
                key = "ESC"
            else:
                key = each.key.capitalize()
            so_many_tabs.append(
                Tab(
                    binding_text(key, each.description),
                    id=each.key # ? note, this is the not-capitalized one
                )
            )
        yield Tabs(*so_many_tabs, id="tab_interface", disabled=True)

    def on_mount(self) -> None:
        if obj := self.query_one(f"#{self.active_tab}"): # this is brittle
            self.query_one("#tab_interface").active = obj.id

    # ! this does not actually work
    # TODO: make this work so I can enable the actual widget again
    @on(Tabs.TabActivated)
    def switch_emulation(self, message: Tabs.TabActivated):
        if message.tab.id in self.switch_map:
            self.app.run_action(self.switch_map[message.tab.id])

class TextArea2(TextArea):
    """
    This is a carbon copy of the Textual "TextArea" in all functionality, it
    only does one thing different: select all is not F7 but CTRL+A
    It also exposes the keys for copy, cut, paste and select all.
    """
    text_area_group = Binding.Group(i18n['TextArea Shortcuts'])
    BINDINGS : ClassVar[list[BindingType]]  = [
        Binding("home", "cursor_line_start", "Cursor line start", show=False),
        Binding("ctrl+x", "cut", "Cut", show=True, group=text_area_group),
        Binding("ctrl+c,super+c", "copy", "Copy", show=True, group=text_area_group),
        Binding("ctrl+v", "paste", "Paste", show=True, group=text_area_group),
        Binding("ctrl+a", "select_all", "Select all", show=True, group=text_area_group),
        Binding("ctrl+z", "undo", "Undo", show=True, group=text_area_group),
        Binding("ctrl+y", "redo", "Redo", show=True, group=text_area_group),
    ]

