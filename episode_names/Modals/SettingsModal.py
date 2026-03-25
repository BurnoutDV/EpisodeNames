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

from textual import on, events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, Select, TextArea, OptionList, Header, \
    Collapsible, TabbedContent, TabPane, Placeholder, SelectionList
from textual.widgets.option_list import Option
from textual.screen import ModalScreen

from episode_names.Utility import i18n
from episode_names.Utility.db import Episode, Project, YtVideo, YtPlaylist, Folge, TextTemplate, PatternTemplate

class SelectExport(ModalScreen[list | None]):
    BINDINGS = [
        Binding(key="escape", action="abort", description=i18n['Cancel'], priority=True),
        Binding(key="enter", action="save", description=i18n['Confirm'], priority=True)
    ]

    CSS_PATH = "../CSS/SettingsModals.tcss"

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        selections = [
            ("Local Data", "local"),
            ("Youtube Data", "remote"),
            ("Application", "app")
        ]
        with Vertical(classes="generic_modal_main"):
            Label(i18n['Select data export categories'])
            yield SelectionList(*selections, id="export_options")
            with Horizontal(classes="adjust"):
                yield Button(i18n['confirm'], id="save")
                yield Button(i18n['abort'], id="abort")

    def on_mount(self) -> None:
        pass

    @on(Button.Pressed, "#save")
    def _action_save(self):
        selected: SelectionList = self.query_exactly_one("#export_options")
        self.dismiss(selected.selected)

    @on(Button.Pressed, "#abort")
    def _action_abort(self):
        self.dismiss(None)