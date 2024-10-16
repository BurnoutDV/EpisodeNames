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

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, Select, TextArea
from textual.screen import ModalScreen, Screen

from episode_names.Utility.i18n import i18n
from episode_names.Utility.db import Project, Playlist, Episode, Folge, TextTemplate, PatternTemplate
from episode_names.Utility.order import new_episode, create_description_text

class EpisodeScreen(Screen):
    BINDINGS = [
        Binding(key="ctrl+d", action="new_entry", description=i18n['New Entry']),
        Binding(key="ctrl+e", action="edit_entry", description=i18n['Edit Entry']),
        Binding(key="ctrl+t,ctrl+q", action="copy_text", description=i18n['Copy Text'])
    ]

    def __init__(self):
        self.current_project = -1
        super().__init__()

    def compose(self) -> ComposeResult:#
        self.projects = Tree("Project", id="project_tree", classes="sidebar")
        self.entryview = DataTable(id="entryview", zebra_stripes=True, cursor_type="row")
        with Vertical():
            with Horizontal():
                yield self.projects
                yield self.entryview
            yield Footer()

    def on_mount(self) -> None:
        self.write_log("Starting EpisodeNames")
        self.projects.show_root = False
        self.projects.show_guides = False
        self.write_log("Init Data Tables and Views...")
        self._init_data()
        #self._dummy_data()
        self.write_log("Mounting Done")
        self.projects.focus()

    def write_raw_log(self, this, additional_text=""):
        self.app.write_raw_log(this, additional_text)

    def write_log(self, text):
        self.app.write_log(text)

    @on(Tree.NodeSelected, "#project_tree")
    def _select_project(self, message: Tree.NodeSelected):
        self.write_log("Tree Node Selected")
        self.write_log(message.node)
        if not message.node.data:
            self.write_log("No Data on leaf")
            return False
        if not message.node.data['db_uid']:
            self.write_log("db_uid tree data does not exist for this note")
            return False
        p_uid = message.node.data['db_uid']
        data = Project.as_Playlist_by_uid(p_uid)
        if not data:
            self.write_log(f"DB does not know project with ID {p_uid}")
            return False
        self.current_project = p_uid
        self._refill_table_with_project(p_uid)

    def _action_new_entry(self):
        def handle_new_entry_response(this: Folge or None):
            if not this:
                return
            self.write_raw_log(this, "New Entry Folge Object")
            Episode.update_or_create(this)
            self.app.notify(i18n['New Entry created'])
            self._refill_table_with_project(self.current_project)  # repaint table

        if not self.current_project:
            return False  # handle this somehow visually
        try:
            res = (Episode
                   .select()
                   .where(Episode.project == self.current_project)
                   .order_by(Episode.counter1.desc())
                   .get())
            last_episode = Folge.from_episode(res)
            this = new_episode(last_episode)
            self.app.push_screen(EditCreateEpisode(this), handle_new_entry_response)
        except Episode.DoesNotExist:
            self.app.push_screen(EditCreateEpisode(None, self.current_project), handle_new_entry_response)

    def _action_edit_entry(self):
        def handle_edit_entry_response(this: Folge or None):
            if not this:
                return
            Episode.update_or_create(this)
            self._refill_table_with_project(self.current_project)

        row_key, column_key = self.entryview.coordinate_to_cell_key(self.entryview.cursor_coordinate)
        if row_key:
            this = Episode.as_Folge_by_uid(row_key.value)
            if this:
                self.app.push_screen(EditCreateEpisode(this), handle_edit_entry_response)
                return

    def _action_copy_text(self):
        row_key, column_key = self.entryview.coordinate_to_cell_key(self.entryview.cursor_coordinate)
        if not row_key:
            return
        this = Episode.as_Folge_by_uid(row_key.value)
        if not this:
            return
        text = create_description_text(this)
        if not text:
            self.app.notify(f"Cannot create formated text for: \n {str(this)}", title=i18n['No template assigned'])
            return
        self.write_raw_log(pyperclip.copy(text))
        self.app.notify(text, title=i18n['Description copied to clipboard'])
        # todo: make this configurable
        # APP Copy to clipboard doesnt work everywhere OSC 52:
        # https://darren.codes/posts/textual-copy-paste/
        # App.copy_to_clipboard(this)

    def _refill_table_with_project(self, p_uid: int):
        # check if project exists
        # get data
        # display dummy text if none is present
        self.entryview.clear(columns=True)
        self.entryview.show_header = True
        data_ep = Episode.by_project(p_uid)
        if not data_ep:
            self.entryview.show_header = False
            self.entryview.add_column("Message")
            self.entryview.add_row("No entries for this project")
            return False
        self.entryview.add_columns(*["#", "##", i18n['Session'], i18n['Record Date'], i18n['Title'], i18n['Template']])
        # TODO: concat template name into episode
        for each in data_ep:
            self.entryview.add_row(
                *[
                    each.counter1,
                    each.counter2,
                    each.session,
                    each.recording_date.strftime("%d.%m.%Y"),
                    each.title,
                    each.db_template
                ],
                key=each.db_uid
            )

    def _init_data(self):
        """Retrieves data from database in bulk for first build of the view"""
        self.projects.root.expand()
        current = self.projects.root.add("Current", expand=True)

        first_entry = -1
        other_categories = []
        #data_pro = get_all_projects()
        data_pro = Project.dump()
        for each in data_pro:
            if first_entry == -1:
                first_entry = each.db_uid
            if each.category == "default":
                current.add_leaf(each.title, data={'db_uid': each.db_uid})
            else:
                if not each.category in other_categories:
                    other_categories.append(each.category)
        for cat in other_categories:
            current = self.projects.root.add(cat)
            for each in data_pro:
                if each.category != cat:
                    continue
                current.add_leaf(each.title, data={'db_uid': each.db_uid})
        self.current_project = first_entry
        self._refill_table_with_project(first_entry)

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
        self.title = Input(placeholder=i18n['Name'])
        self.category = Select((line, line) for line in LINES)
        self.description = TextArea(id='description')

        with Vertical(classes="center_vert"):
            yield Label("Creating or Editing Project", classes="title")
            yield self.title
            yield self.category
            yield self.description
            with Horizontal():
                yield Button(i18n['Save'], id="save")
                yield Button(i18n['Cancel'], id="abort")

    def _action_save(self):
        self.dismiss(self.current)

    def _action_abort(self):
        self.dismiss(None)


class EditCreateEpisode(ModalScreen[Folge or None]):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="ctrl+c, esc", action="abort", description=i18n['Cancel'], priority=True)
    ]

    def __init__(self, copy_from: None or Folge = None, p_uid: int = -1):
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



