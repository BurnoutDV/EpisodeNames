#!/usr/bin/env python3
# coding: utf-8

# Copyright 2024 by BurnoutDV, <development@burnoutdv.com>
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

from datetime import datetime, date
import time
from typing import Iterable

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, ListView, RichLog, Select, TextArea, ListItem
from textual.screen import ModalScreen, Screen

from episode_names.Utility.i18n import i18n
from episode_names.Utility.db import Project, Playlist, Episode, Folge, TextTemplate, PatternTemplate

class TemplateScreen(Screen):
    BINDINGS = [
        Binding(key="ctrl+n", action="new", description=i18n['Create New']),
        Binding(key="ctrl+d", action="duplicate", description=i18n['Duplicate Current']),
        Binding(key="ctrl+s", action="save", description=i18n['Save Current']),
        Binding(key="ctrl+del", action="delete", description=i18n['Delete Current']),
        Binding(key="ctrl+backspace", action="discard", description=i18n['Discard Current'])
    ]

    def __init__(self):
        self.filter_bar = Input(id="filter", placeholder=i18n['Enter Filter here'], classes="small_input")
        self.templates = Tree("Label", id="template_list")
        self.pattern_name = Input(id="pattern_name", placeholder="Name of the Pattern", disabled=True)
        self.pattern = TextArea(id="pattern", disabled=True, soft_wrap=True, show_line_numbers=True)
        self.current_pattern = None
        self.unsaved_patterns: dict[int, PatternTemplate] = {}
        # TODO: logic for not saved patterns
        # TODO: save cursor positions?
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(i18n["Template Edit"])
            with Horizontal():
                with Vertical(classes="sidebar"):
                    yield self.filter_bar
                    yield self.templates
                with Vertical():
                    yield self.pattern_name
                    yield self.pattern
            yield Footer()

    def on_mount(self):
        self.templates.show_root = False
        self.templates.show_guides = False
        self._update_pattern_list()
        self.templates.focus()
        self.app.write_raw_log(self.pattern.available_themes, "TextEditor Themes:")

    @on(Tree.NodeSelected, "#template_list")
    def _select_project(self, message: Tree.NodeSelected):
        if not message.node.data:
            return False
        if not message.node.data['db_uid']:
            return False
        uid = message.node.data['db_uid']
        data = TextTemplate.as_PTemplate_by_uid(uid)
        if not data:
            self.app.write_log(f"DB does not know template with ID {uid}")
            return False
        self.current_pattern = data
        self._set_editor(data)

    def _set_editor(self, this: PatternTemplate):
        self.pattern_name.disabled = False
        self.pattern_name.value = this.title
        self.pattern.disabled = False
        self.pattern.load_text(this.pattern)
        self.pattern.move_cursor((0,0))
        self.pattern.focus()

    def _update_pattern_list(self, title_filter=""):
        patterns = TextTemplate.dump()
        self.templates.clear()
        self.templates.root.expand()
        if not patterns: # empty list
            self.templates.root.add_leaf(i18n['No Elements present'])
            return
        self.app.write_raw_log(patterns)
        for each in patterns:
            line = f"{each.title} [#{each.db_uid}-{len(each.pattern)}]"
            self.templates.root.add_leaf(line, data={'db_uid': each.db_uid})
