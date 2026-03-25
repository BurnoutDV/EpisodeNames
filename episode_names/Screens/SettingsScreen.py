#!/usr/bin/env python3
# coding: utf-8
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
import datetime
import os.path

from textual import on, work
from textual.app import ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import DataTable, Footer, Tree, Select, Input, MarkdownViewer, TextArea, Button, Label, \
    Checkbox
from textual.screen import Screen
from textual_fspicker import FileSave, FileOpen, Filters

from episode_names.Modals import YesNoBox, SelectExport
from episode_names.Utility import i18n
from episode_names.Utility.db import Settings
from episode_names.Utility.custom_widgets import EnPageMarker
from episode_names.Utility.db_aux_utility import export_to_json, import_from_json, purge_all_user_data
from episode_names.__init__ import __version__

class SettingsScreen(Screen):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
    ]

    CSS_PATH = "../CSS/SettingsScreen.tcss"

    def __init__(self):
        self.home = os.path.expanduser("~")
        super().__init__()

    def compose(self) -> ComposeResult:
        yield EnPageMarker("f7")
        with Vertical(id='top_dog'):
            with Horizontal():
                yield Label(i18n['The Settings Screen'])
                yield Button(label=i18n['Save'], id="btn_save")
                yield Button(label=i18n['Discard'], id="btn_abort")
        with ScrollableContainer(id='main'):

            with Horizontal(classes='settings', id='con_style'):
                yield Select([('Custom', 1)], id='sel_theme')
            with Horizontal(classes='settings', id='con_dateformat'):
                yield Input(classes="compact_input", id='in_dateformat')
                yield Input(classes="compact_input", id='in_datetimeformat', tooltip=i18n['tooltip_datetime'])
            with Horizontal(classes='settings', id='con_linking'):
                yield Input(classes="compact_input", id='in_youtube_api_key')
                yield Input(classes="compact_input", id='in_youtube_channel_id')
            with Vertical(classes='settings', id='con_backup'): # TODO: use grid por favor
                with Horizontal():
                    yield Button(label=i18n['Database2JSON Export'] ,id="export_json", classes="danger")
                    yield Button(label=i18n['Database2JSON Export Partial'] ,id="export_json_partial", classes="danger")
                    # TODO: implement this..maybe option to limit export to records of certain age?
                with Horizontal():
                    yield Checkbox(label=i18n['Delete old data'], id='delete_old')
                    yield Button(label=i18n['Database2JSON Import'] ,id="import_json", classes="danger")

    def on_mount(self) -> None:
        self.query_exactly_one("#con_style").border_title = i18n['Style']
        self.query_exactly_one("#con_dateformat").border_title = i18n['dateformat']
        self.query_exactly_one("#con_linking").border_title = i18n['Youtube Linking']
        self.query_exactly_one("#con_backup").border_title = i18n['Backup']
        some_settings = Settings.get_keys(['youtube_api_key', 'youtube_channel_id', 'dateformat', 'datetimeformat'])
        in_dateformat: Input = self.query_exactly_one("#in_dateformat")
        in_dateformat.border_subtitle = i18n['Dateformat']
        in_dateformat.value = some_settings.get('dateformat', "")
        in_datetimeformat: Input = self.query_exactly_one("#in_datetimeformat")
        in_datetimeformat.border_subtitle = i18n['Datetimeformat']
        in_datetimeformat.value = some_settings.get('datetimeformat', "")
        in_youtube_api_key: Input = self.query_exactly_one("#in_youtube_api_key")
        in_youtube_api_key.border_subtitle = i18n['YT API Key']
        in_youtube_api_key.value = some_settings.get('youtube_api_key', "")
        in_youtube_channel_id = self.query_exactly_one("#in_youtube_channel_id")
        in_youtube_channel_id.border_subtitle = i18n['YT Channel ID']
        in_youtube_channel_id.value = some_settings.get('youtube_channel_id', "")
        theme_selector: Select = self.query_exactly_one('#sel_theme')
        theme_selector.clear()
        all_themes = []
        for each in self.app.available_themes.keys():
            all_themes.append((each, each))
        theme_selector.set_options(all_themes)
        theme_selector.value = self.app.theme

    @on(Button.Pressed, "#export_json")
    @work
    async def select_save_path(self, categories:list|None = None):
        """
        :param categories: ['local', 'remote', 'app']
        :return:
        """
        now_str = datetime.date.today().isoformat()
        if save_to := await self.app.push_screen_wait(FileSave(
                location=self.home,
                title=i18n['Export as'],
                save_button=i18n['Save'],
                cancel_button=i18n['Cancel'],
                default_file=f"episode_export_v{__version__}_{now_str}.json")
        ):
            if export_to_json(str(save_to), categories=categories):
                self.notify(i18n['Export successful'])
            else:
                self.notify(i18n['Export failed'])

    @on(Button.Pressed, "#export_json_partial")
    def partial_export(self):
        def callback_trader(selected: list | None):
            if selected is None:
                return
            if selected is not None and not selected:
                self.app.notify(i18n['Nothing selected'])
            self.select_save_path(selected)
        self.app.push_screen(SelectExport(), callback_trader)

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

    def _action_save(self):
        """Saves preset settings in input fields"""
        date_format : Input = self.query_exactly_one("#in_dateformat")
        datetime_format : Input = self.query_exactly_one("#in_datetimeformat")
        theme : Select = self.query_exactly_one("#sel_theme")
        api_key : Input = self.query_exactly_one("#in_youtube_api_key")
        channel_id : Input = self.query_exactly_one("#in_youtube_channel_id")
        if str(date_format.value).strip():
            Settings.update_or_set_key("dateformat", str(date_format.value).strip())
        if str(datetime_format.value).strip():
            Settings.update_or_set_key("datetimeformat", str(datetime_format.value).strip())
        if str(theme.value).strip() and theme.value != self.app.theme:
            Settings.update_or_set_key("textual_theme", str(theme.value).strip())
            self.app.theme = theme.value
        if str(api_key.value).strip():
            Settings.update_or_set_key("youtube_api_key", str(api_key.value).strip())
        if str(channel_id.value).strip():
            Settings.update_or_set_key("youtube_channel_id", str(channel_id.value).strip())
        self.app.notify(i18n['Settings Saved'], title=i18n['Settings Menu'])
        self.app.write_log("Settings >> Save Button.triggered")

    @on(Button.Pressed, "#btn_save")
    def _btn_save(self):
        self._action_save()



