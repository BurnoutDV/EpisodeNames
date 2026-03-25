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
    Collapsible, TabbedContent, TabPane, Placeholder
from textual.widgets.option_list import Option
from textual.screen import ModalScreen

from episode_names.Utility import i18n
from episode_names.Utility.db import Episode, Project, YtVideo, YtPlaylist, Folge, TextTemplate, PatternTemplate
from episode_names.Utility.recommend import find_related_project


class LinkVideoModal(ModalScreen[Folge]):
    CSS_PATH = "../CSS/LinkingModals.tcss"
    def __init__(self, video: YtVideo):
        self.video = video
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id="main"):
            with Vertical(id="left"):
                Input(placeholder="yt title")
                TextArea(placeholder="yt desc")
            with TabbedContent(id="middle"):
                with TabPane("Recommend"):
                    yield Tree(label="Recommended videos")
                with TabPane("Database"):
                    yield Input(placeholder="project filter")
                    yield Tree("Projects")
                    yield Input(placeholder="episode filter")
                    yield Tree("Episodes")
            with Vertical(id="right"):
                with Horizontal():
                    yield Input(placeholder=i18n['Title'])
                with Horizontal():
                    yield Input(placeholder=i18n['Session'], classes="compact_input")
                    yield Input(placeholder=i18n['Date'], classes="compact_input")
                    yield Input(placeholder="#", classes="compact_input", type="integer")
                    yield Input(placeholder="##", classes="compact_input", type="integer")
                with Collapsible(collapsed=True, title=i18n['Description Addon'], id="Desc_Addon"):
                    yield TextArea(id="tx_desc_addon", soft_wrap=True, show_line_numbers=True)
                with Collapsible(collapsed=True, title=i18n['Description'], id="Description"):
                    yield TextArea(id="tx_description", soft_wrap=True, show_line_numbers=True)
        with Horizontal(classes="adjust"):
            yield Button(i18n['Save'], id="save")
            yield Button(i18n['Cancel'], id="abort")

    @on(Button.Pressed, "#abort")
    def _btn_abort(self):
        self.dismiss(None)

class LinkPlaylistModal(ModalScreen[Project]):
    CSS_PATH = "../CSS/LinkingModals.tcss"
    def __init__(self, playlist: YtPlaylist):
        self.playlist = playlist
        super().__init__()

    """
    So you might ask, Burnout, why are using fucking Tree Widgets everywhere
    dont you know that ListViews exists? I do, but Trees can be made to look
    like lists while having a lot of additional compute in them, for instance
    I can enrich the entries with arbitrary meta data which is super convenient
    to be used in later calls, as long as you can trust the interface to carry
    correct informations I find this method so much better than handling some
    kind of lookup table for each element
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="wrapper", classes="generic_modal_main"): # for the modal effects
            with Horizontal(id="main"):
                yield Tree("Recommends", id="recommends")
                yield Placeholder(id="preview")
            with Horizontal(classes="adjust"):
                yield Button(i18n['Save'], id="save")
                yield Button(i18n['Cancel'], id="abort")

    def _on_mount(self, event: events.Mount) -> None:
        recommends: Tree = self.query_exactly_one("#recommends")
        recommends.show_root = False
        recommends.show_guides = False
        recommends.clear()
        recommends.root.expand()
        recs = find_related_project(self.playlist.yt_id)
        if not recs:
            recommends.root.add_leaf(i18n['No recommendations'])
            return
        for key, entry in recs.items():
            recommends.root.add_leaf(entry['name'], data={'db_uid': key})

    @on(Button.Pressed, "#abort")
    def _btn_abort(self):
        self.dismiss(None)