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

from textual import on
from textual.widgets import Tabs, Tab, Static

def binding_text(key_bind: str, content: str) -> str:
    return f"[bold][$accent]{key_bind}[/][/bold] {content}"

class EnPageMarker(Widget):
    DEFAULT_CSS = """
    EnPageMarker {
        height: 2;
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