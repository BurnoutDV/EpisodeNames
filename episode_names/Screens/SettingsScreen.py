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
import datetime
import os.path

from textual import on, work
from textual.app import ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import DataTable, Footer, Tree, TabbedContent, TabPane, MarkdownViewer, TextArea, Button, Label, \
    Checkbox
from textual.screen import Screen
from textual_fspicker import FileSave, FileOpen, Filters

from episode_names.Modals.DialogueModals import YesNoBox
from episode_names.Utility import i18n
from episode_names.Utility.db_aux_utility import export_to_json, import_from_json, purge_all_user_data

class SettingsScreen(Screen):
    BINDINGS = [

    ]

    def __init__(self):
        self.home = os.path.expanduser("~")
        super().__init__()

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Label(i18n['The Settings Screen'])
            yield Button(label=i18n['Database2JSON Export'] ,id="export_json", classes="danger")
            yield Checkbox(label=i18n['Delete old data'], id='delete_old')
            yield Button(label=i18n['Database2JSON Import'] ,id="import_json", classes="danger")

    def on_mount(self) -> None:
        pass

    @on(Button.Pressed, "#export_json")
    @work
    async def select_save_path(self):
        now_str = datetime.date.today().isoformat()
        if save_to := await self.app.push_screen_wait(FileSave(
                location=self.home,
                title=i18n['Export as'],
                save_button=i18n['Save'],
                cancel_button=i18n['Cancel'],
                default_file=f"episode_export_{now_str}.json")
        ):
            if export_to_json(str(save_to)):
                self.notify(i18n['Export successful'])
            else:
                self.notify(i18n['Export failed'])

    @on(Button.Pressed, "#import_json")
    @work
    async def select_load_path(self):
        if not await self.app.push_screen_wait(YesNoBox(i18n['warning_delete_current_data'])):
            return
        if open_from := await self.app.push_screen_wait(FileOpen(
                location=self.home,
                title=i18n['Export as'],
                open_button=i18n['Open'],
                cancel_button=i18n['Cancel'],
                filters=Filters(("JSON", lambda p: p.suffix.lower() == ".json"), ("ALL", lambda _: True))
        )):
            self.app.notify(str(open_from))
            delete_checkbox = self.query_one("#delete_old")
            if delete_checkbox.value:
                purge_all_user_data(delete_checkbox.value)
            da_count = import_from_json(open_from)
            self.app.notify(f"We got {da_count} new entries")
            if da_count > 0:
                self.app.redraw_after_import = True, True  # redraw for both screens
                # ? damnit, how to trigger an interface redraw on other screens?
                # ? signals that trigger next time the screen is visible again?



