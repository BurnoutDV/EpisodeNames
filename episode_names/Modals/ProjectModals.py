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

import copy

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Input, Button, Label, TextArea, Checkbox
from textual.screen import ModalScreen

#temporary external dependency from textual_autocomplete...
from episode_names.external_internal import AutoComplete, Dropdown, DropdownItem, InputState

from episode_names.Utility import i18n
from episode_names.Utility.db import Project, Playlist
from episode_names.Modals.DialogueModals import YesNoBox


class CreateEditProject(ModalScreen[Playlist | None | bool]):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="escape", action="abort", description=i18n['Cancel'])
    ]

    def __init__(self, initial_project: Playlist or None = None):
        self.tx_title = i18n['Editing an existing Project']
        if not initial_project:
            initial_project = Playlist("")
            self.tx_title = i18n['Create a new Project']
        self.initial_project = initial_project
        self.current = copy.copy(initial_project)
        self.categories = [] # init categories as empty list
        self.can_delete = False
        super().__init__()

    def compose(self) -> ComposeResult:
        self.pr_title = Input(placeholder=i18n['Name'], id="title")
        self.category = Input(placeholder=i18n['Category'], id="category")
        self.description = TextArea(id='description', soft_wrap=True, show_line_numbers=True)
        if self.initial_project.db_uid:
            self.can_delete = Project.is_empty(self.initial_project.db_uid)
            self.app.write_log(f"Can delete yes/no: {str(self.can_delete)}")

        with Vertical(classes="center_vert"):
            with ScrollableContainer(id="min_height_enforcer"):
                yield Label(self.tx_title, classes="title")
                yield self.pr_title
                yield AutoComplete(
                    self.category,
                    Dropdown(id="autocomplete_dropdown", items=self._update_autocomplete)
                )
                yield self.description
                if self.can_delete:
                    with Horizontal(classes="adjust"):
                        yield Checkbox(i18n['Delete Project'], id="delete_project")
                with Horizontal(classes="adjust"):
                    yield Button(i18n['Save'], id="save")
                    yield Button(i18n['Cancel'], id="abort")

    def on_mount(self) -> None:
        self.categories = Project.get_categories()
        self.pr_title.value = self.initial_project.title
        self.category.value = self.initial_project.category
        self.description.load_text(self.initial_project.description)

    @on(Checkbox.Changed, "#delete_project")
    def delete_state_toggle(self, message: Checkbox):
        delete_state = self.query_one("#delete_project")
        elements = ["#title", "#category", "#description"]
        for each in elements:
            widget = self.query_one(each)
            widget.disabled = delete_state.value

    @on(Button.Pressed, "#save")
    def _action_save(self) -> None:
        self._update_internal_playlist()
        # delete option, should only be available for empty ones
        if self.can_delete:
            delete_state = self.query_one("#delete_project")
            if delete_state.value:
                def callback_box(status: bool):
                    if status:
                        self.dismiss(False)
                self.app.push_screen(YesNoBox(i18n['Delete this project?']), callback_box)
                return
        # safe guard against empty projects
        if not self.current.title: # aka empty content
            def callback_box(status: bool):
                if status:
                    self.dismiss(None)
            self.app.push_screen(YesNoBox(i18n['Title cannot be empty, discard entry?']), callback_box)
            return
        if not self.current.category:
            self.current.category = "default"  # make this configurable?
        self.dismiss(self.current)

    @on(Button.Pressed, "#abort")
    def _action_abort(self) -> None:
        self._update_internal_playlist()
        if self.can_delete: # in case delete is activated but canceled, instant dismiss
            delete_state = self.query_one("#delete_project")
            if delete_state.value: # this behaviour might feel a bit odd
                self.dismiss(None)
                return
        if self.current == self.initial_project:
            self.dismiss(None)
            return

        yesnotext = i18n['Data has changed, discard changes?']
        if self.initial_project.db_uid == 0:
            if not self.current: # nothing in it
                self.dismiss(None)
                return
            yesnotext = i18n['New entry is not empty, abort process?']

        def callback_box(status: bool):
            if status:
                self.dismiss(None)
                return

        self.app.push_screen(YesNoBox(yesnotext), callback_box)
        return# standard dismissal

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
