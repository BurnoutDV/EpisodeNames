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
from select import select
from typing import Iterable, Literal

import pyperclip

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.demo import Title
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, Select, TextArea, OptionList, Header
from textual.widgets.option_list import Option, Separator
from textual.screen import ModalScreen, Screen

from episode_names.Utility.i18n import i18n
from episode_names.Utility.db import Project, Playlist, Episode, Folge, TextTemplate, PatternTemplate
from episode_names.Utility.order import new_episode, create_description_text


class CreateEditProject(ModalScreen[Playlist or None]):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="ctrl+c, esc", action="abort", description=i18n['Cancel'])
    ]

    def __init__(self, initial_project: Playlist or None = None):
        self.initial_project = initial_project
        self.current = Playlist("")
        super().__init__()

    def compose(self) -> ComposeResult:
        LINES = """Current
Legacy
Disgrace""".splitlines()
        self.pr_title = Input(placeholder=i18n['Name'])
        self.category = Select((line, line) for line in LINES)
        self.description = TextArea(id='description')
        self.tags = TextArea(id='tags')

        with Vertical(classes="center_vert"):
            yield Label("Creating or Editing Project", classes="title")
            yield self.pr_title
            yield self.category
            yield self.description
            with Horizontal():
                yield Button(i18n['Save'], id="save")
                yield Button(i18n['Cancel'], id="abort")

    def _action_save(self):
        self.current.title = self.pr_title.value
        self.current.category = self.category.value
        self.current.tags = self.tags.text
        self.dismiss(self.current)

    def _action_abort(self):
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def _btn_save(self) -> None:
        self._action_save()

    @on(Button.Pressed, "#abort")
    def _btn_abort(self) -> None:
        self._action_abort()