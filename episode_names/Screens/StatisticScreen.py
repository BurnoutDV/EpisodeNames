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
from typing import Iterable, Literal

import pyperclip
from rich.text import Text

from textual import on, events
from textual.app import ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import DataTable, Footer, Tree, TabbedContent, TabPane, MarkdownViewer, TextArea, Label
from textual.screen import Screen
from peewee import JOIN

from episode_names.__init__ import __default_dateformat__, __default_datetimeformat__
from episode_names.Utility import i18n
from episode_names.Utility.custom_widgets import EnPageMarker
from episode_names.Utility.db import Project, Playlist, Episode, Settings, Folge, TextTemplate, PatternTemplate

class StatisticScreen(Screen):
    CSS_PATH = "../CSS/StatisticScreen.tcss"

    # TODO: add additional field for episode edits to save "change delta"
    # TODO: any kind of interface
    # TODO: all the other nice statistics, incorporate yt data as well
    # TODO: presets/saved views
    # TODO: date ranges
    # TODO: adjust amount of outputted lines

    def __init__(self):
        self.dateformat = __default_dateformat__
        self.datetimeformat = __default_datetimeformat__
        self.date_delta = datetime.timedelta(minutes=5) # if edit & create date are in this range, it doesnt appear in some statistics
        super().__init__()

    def compose(self) -> ComposeResult:
        yield EnPageMarker("f4")
        yield DataTable(id="dt_stat_view", zebra_stripes=True, cursor_type="row")
        yield Footer(id="heinz")

    def on_mount(self) -> None:
        self.dateformat = Settings.save_retrieve_key('dateformat', __default_dateformat__)
        self.datetimeformat = Settings.save_retrieve_key('datetimeformat', __default_datetimeformat__)
        self._edit_view()

    def _edit_view(self):
        dt : DataTable = self.query_one("#dt_stat_view", DataTable)
        dt.clear(columns=True)
        dt.show_header = True
        res = (Episode.select().join(Project, JOIN.LEFT_OUTER)
               .order_by(Episode.edit_date.desc())
               .limit(100))
        if len(res) <= 0:
            dt.show_header = False
            dt.add_column("Message")
            dt.add_row("Display of statistics failed.")
            return None
        dt.add_column("#", key="counter1")
        dt.add_column("title", key="title")
        dt.add_column("project", key="project")
        dt.add_column("last_edit", key="last_edit")
        for each in res:
            if each.edit_date < each.create_date + self.date_delta: # checks if create/edit are same, too similar
                continue # edit date is always higher/same as create
            dt.add_row(
                *[
                    each.counter1,
                    each.title,
                    each.project.name,
                    each.edit_date.strftime(self.datetimeformat),
                ],
                key=each.id
            )

    def write_raw_log(self, this, additional_text=""):
        self.app.write_raw_log(this, additional_text)

    def write_log(self, text):
        self.app.write_log(text)