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
import copy
from select import select
from typing import Iterable, Literal

import pyperclip

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, Select, TextArea, OptionList, Header
from textual_autocomplete import AutoComplete, Dropdown, DropdownItem, InputState
from textual.screen import ModalScreen, Screen

from episode_names.Utility.i18n import i18n
from episode_names.Utility.db import Project, Playlist, Episode, Folge, TextTemplate, PatternTemplate
from episode_names.Screens.dialogue import YesNoBox
from episode_names.Utility.order import new_episode, create_description_text


class CreateEditProject(ModalScreen[Playlist or None]):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="ctrl+c, esc", action="abort", description=i18n['Cancel'])
    ]

    def __init__(self, initial_project: Playlist or None = None):
        self.tx_title = i18n['Editing an existing Project']
        if not initial_project:
            initial_project = Playlist("", "", "", -1)
            self.tx_title = i18n['Create a new Project']
        self.initial_project = initial_project
        self.current = copy.copy(initial_project)
        self.categories = [] # init categories as empty list
        super().__init__()

    def compose(self) -> ComposeResult:
        self.pr_title = Input(placeholder=i18n['Name'])
        self.category = Input(placeholder=i18n['Category'])
        self.description = TextArea(id='description', soft_wrap=True, show_line_numbers=True)

        with Vertical(classes="center_vert"):
            yield Label(self.tx_title, classes="title")
            yield self.pr_title
            yield AutoComplete(
                self.category,
                Dropdown(id="autocomplete_dropdown", items=self._update_autocomplete)
            )
            yield self.description
            with Horizontal(classes="adjust"):
                yield Button(i18n['Save'], id="save")
                yield Button(i18n['Cancel'], id="abort")

    def on_mount(self) -> None:
        self.categories = Project.get_categories()
        self.pr_title.value = self.initial_project.title
        self.category.value = self.initial_project.category
        self.description.load_text(self.initial_project.description)

    def _action_save(self) -> None:
        self._update_internal_playlist()
        self.dismiss(self.current)

    def _action_no_save(self):
        self.dismiss(None)

    def _action_abort(self) -> None:
        self._update_internal_playlist()
        self.dismiss(None)
        return None
        # currently broken
        # TODO: fix save message later
        if self.current == self.initial_project:
            self.dismiss(None)
            return

        def callback_box(status: bool):
            if status:
                self.dismiss(None)

        self.app.push_screen(YesNoBox(i18n['Data has changed, you really want to abort?']), callback_box)

    @on(Button.Pressed, "#save")
    def _btn_save(self) -> None:
        self._action_save()

    @on(Button.Pressed, "#abort")
    def _btn_abort(self) -> None:
        self._action_abort()

    def _update_internal_playlist(self) -> None:
        self.current.title = self.pr_title.value
        self.current.category = self.category.value
        self.current.description = self.description.text

    def _update_autocomplete(self, input_state: InputState) -> list[DropdownItem]:
        items = []
        for each in self.categories:
            items.append(
                DropdownItem(each)
            )
        # stolen from example
        matches = [c for c in items if input_state.value.lower() in c.main.plain.lower()]
        ordered = sorted(matches, key=lambda v: v.main.plain.startswith(input_state.value.lower()))

        return ordered
