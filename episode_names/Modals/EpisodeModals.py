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
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, Select, TextArea, OptionList, Header
from textual.widgets.option_list import Option, Separator
from textual.screen import ModalScreen

from episode_names.Utility import i18n
from episode_names.Utility.db import Project, Playlist, Episode, Folge, TextTemplate, PatternTemplate

class AssignTemplate(ModalScreen[TextTemplate or None]):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="ctrl+c, esc", action="abort", description=i18n['Cancel'], priority=True)
    ]

    def __init__(self, hot_episode: Folge):
        self.current_episode = hot_episode
        self.cache = dict()
        super().__init__()

    def compose(self) -> ComposeResult:
        self.preview = TextArea("", id="preview_stuff", read_only=True)
        self.templates = OptionList("", id="template_list", classes="sidebar max-height")

        with Vertical():
            yield Header(id="headline", icon=None)
            with Horizontal(classes="max-height"):
                yield self.templates
                yield self.preview
            with Horizontal(classes="adjust"):
                yield Button(i18n['Save'], id="save")
                yield Button(i18n['Cancel'], id="abort")
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = f"{self.current_episode.counter1} - {self.current_episode.title}"
        self.title = i18n['Assign Template']
        self.fill_options()

    def fill_options(self):
        self.templates.clear_options()
        list_of_templates = TextTemplate.dump()
        if not list_of_templates:
            self.app.notify(f"{i18n['There are no templates']}", )
            return
        self.cache = {}
        self.templates.add_option(Option("", id="-1"))
        # todo add current element here
        self.templates.add_option(Separator())
        for each in list_of_templates:
            self.templates.add_option(Option(each.title, str(each.db_uid)))
            self.cache[str(each.db_uid)] = each  # Option Index are strings
        if self.current_episode.db_template > 0:
            index = self.templates.get_option_index(str(self.current_episode.db_template))
        else:
            index = self.templates.get_option_index("-1")
        self.templates.highlighted = index
        #self.app.write_raw_log(self.cache, "Template Cache")

    def save_and_exit(self, template_id: int):
        self.current_episode.db_template = template_id
        self.dismiss(self.current_episode)

    def _action_save(self) -> None:
        """
        Reads the current highlighted Index of the OptionList and uses that
        :return:
        """
        index = self.templates.highlighted
        if not index:
            self.app.notify(f"AssignTemplate: {i18n['No Option highlighted']}", severity="warning")
            return
        try:
            selection = self.templates.get_option_at_index(index)
        except OptionList.OptionDoesNotExist:
            self.app.notify(
                i18n['There seems to be no option selected'],
                title=i18n['OptionList Selection Error'],
                severity="warning"
            )
            return
        self.save_and_exit(selection.id)

    def _action_abort(self) -> None:
        """
        Simply closes the modal.
        :return:
        """
        self.dismiss(None)

    @on(OptionList.OptionSelected, "#template_list")
    def _list_selected(self, selected: OptionList.OptionHighlighted) -> None:
        """
        When Enter Key pressed, uses that template and instantly closes the modal with the
        selected options as new template
        :param selected:
        :return:
        """
        self.app.write_raw_log(selected)
        if not selected.option_id:
            self.app.notify(f"AssignTemplate: {i18n['No Option ID']}", severity="warning")
            return
        if selected.option_id in self.cache:  # aka a know database variable
            self.save_and_exit(int(selected.option_id))
        if selected.option_id == "-1":
            self.save_and_exit(-1)
        # there should be theoretically no other option, but this way it should be written savely?

    @on(OptionList.OptionHighlighted, "#template_list")
    def _list_highlighted(self, selected: OptionList.OptionHighlighted) -> None:
        """
        Previews the currently highlighted option by displaying the template text in
        the textarea, information cached. I hope this will never be a problem.
        :param selected:
        :return:
        """
        if not selected.option_id:
            self.app.notify(f"AssignTemplate: {i18n['No Option ID']}", severity="warning")
            return
        if selected.option_id in self.cache:
            self.preview.load_text(self.cache[selected.option_id].pattern)
            return
        self.preview.clear() # defaults to blank slate

    @on(Button.Pressed, "#save")
    def _btn_save(self) -> None:
        self._action_save()

    @on(Button.Pressed, "#abort")
    def _btn_abort(self) -> None:
        self._action_abort()

class CreateEditEpisode(ModalScreen[Folge or None]):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="ctrl+c, esc", action="abort", description=i18n['Cancel'], priority=True)
    ]

    def __init__(self, copy_from: None or Folge = None, p_uid: int = 0):
        self.copy_from = copy_from
        if not self.copy_from and p_uid:
            current_play = Project.as_Playlist_by_uid(p_uid)
            if current_play:
                self.copy_from = Folge(
                    title="",
                    db_project=current_play.db_uid
                )
        super().__init__()

    def compose(self) -> ComposeResult:
        self.gui_title = Input(placeholder=i18n['Title'])
        self.gui_session = Input(placeholder=i18n['Session'], classes="compact_input")
        self.gui_date = Input(placeholder=i18n['Date'], classes="compact_input") # TOdO: find date widget or constrained
        self.gui_counter1 = Input(placeholder="#", classes="compact_input", type="integer")
        self.gui_counter2 = Input(placeholder="##", classes="compact_input", type="integer")
        with Vertical(classes="center_vert"):
            yield Label(f"Edit or Create Entry", classes="title")
            with Horizontal():
                yield self.gui_title
            with Horizontal():
                yield self.gui_session
                yield self.gui_date
            with Horizontal():
                yield self.gui_counter1
                yield self.gui_counter2
            #yield Checkbox("apply retrograde")
            with Horizontal(classes="adjust"):
                yield Button(i18n['Save'], id="save")
                yield Button(i18n['Cancel'], id="abort")
            yield Footer()

    def on_mount(self) -> None:
        if isinstance(self.copy_from, Folge):
            self.gui_title.value = self.copy_from.title
            self.gui_session.value = self.copy_from.session
            self.gui_date.value = self.copy_from.recording_date.strftime("%d.%m.%Y")
            self.gui_counter1.value = str(self.copy_from.counter1)
            self.gui_counter2.value = str(self.copy_from.counter2)
        else:
            # there has to be some kind of kind of copy from
            self.app.notify(i18n['No suiteable creation method for episode found'], severity="error")
            self.dismiss(None)

    def _action_save(self):
        try:
            rec_date = datetime.strptime(self.gui_date.value, "%d.%m.%Y").date()
        except ValueError:
            rec_date = None
        form = Folge(
            title=self.gui_title.value,
            db_uid=self.copy_from.db_uid if self.copy_from else -1,
            db_project=self.copy_from.db_project if self.copy_from else -1,
            db_template=self.copy_from.db_template if self.copy_from else -1,
            counter1=self.gui_counter1.value,
            counter2=self.gui_counter2.value,
            session=self.gui_session.value,
            description=self.copy_from.description if self.copy_from else "",
            recording_date=rec_date if rec_date else date.today(),
        )
        self.dismiss(form)

    def _action_abort(self):
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def _btn_save(self):
        self._action_save()

    @on(Button.Pressed, "#abort")
    def _btn_abort(self):
        self._action_abort()