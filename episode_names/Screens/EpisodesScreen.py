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
from textual.app import ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, Select, TextArea, OptionList, Header
from textual.widgets.option_list import Option, Separator
from textual.screen import ModalScreen, Screen

from episode_names.Utility import i18n
from episode_names.Utility.db import Project, Playlist, Episode, Folge, TextTemplate, PatternTemplate
from episode_names.Utility.order import new_episode, create_description_text
from episode_names.Modals import CreateEditProject, AssignTemplate, CreateEditEpisode

class EpisodeScreen(Screen):
    BINDINGS = [
        Binding(key="ctrl+d", action="new_entry", description=i18n['New Entry']),
        Binding(key="ctrl+e", action="edit_entry", description=i18n['Edit Entry']),
        Binding(key="ctrl+a", action="assign_template", description=i18n['Assign Template']),
        Binding(key="ctrl+q", action="copy_text", description=i18n['Copy Text']),
        Binding(key="ctrl+t", action="copy_tags", description=i18n['Copy Tags']),
        Binding(key="ctrl+k", action="create_project_menu", description=i18n['Create Project']),
        Binding(key="ctrl+l", action="edit_project_menu", description=i18n['Edit current Project'])
    ]

    def __init__(self):
        self.current_project = None
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
        self.write_raw_log(Project.get_categories())

    def write_raw_log(self, this, additional_text=""):
        self.app.write_raw_log(this, additional_text)

    def write_log(self, text):
        self.app.write_log(text)

    def _action_create_project_menu(self):
        def handle_callback(new_project: Playlist | None) -> None:
            if new_project:
                Project.create_new(new_project)
                self.redraw_project_tree()
        self.app.push_screen(CreateEditProject(), handle_callback)

    def _action_edit_project_menu(self) -> None:
        current = self.projects.cursor_node
        if not current.data:
            self.app.notify(i18n['No project currently selected.'], severity="information", timeout=2)
            return
        if not current.data['db_uid']:
            self.app.notify(i18n['Selected project has no ID, this should not be happen.'], severity="error")
            return
        p_uid = current.data['db_uid']
        self._open_edit_project_menu(p_uid)

    def _open_edit_project_menu(self, project_db_id: int) -> None:
        """Opens the current project menu, exists so the command palette works"""
        data = Project.as_Playlist_by_uid(project_db_id)
        if not data:
            self.write_log(f"DB does not know project with ID {project_db_id}")
            return False
        def handle_callback(changed: Playlist) -> None:
            if not changed:
                return
            if changed != data:
                Project.update_or_create(changed)
                self.redraw_project_tree()
        self.app.push_screen(CreateEditProject(data), handle_callback) # callback here

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
            self.app.notify(i18n['No currently selected project, cannot create "free" episodes'], severity="warning")
            return False  # handle this somehow visually
        last_episode = Episode.get_latest(self.current_project)
        if last_episode:
            this = new_episode(last_episode)
            self.app.push_screen(CreateEditEpisode(this), handle_new_entry_response)
        else:
            self.app.push_screen(CreateEditEpisode(None, self.current_project), handle_new_entry_response)

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
                self.app.push_screen(CreateEditEpisode(this), handle_edit_entry_response)
                return
    def _action_copy_tags(self):
        """
        Copies tags of the currently selected episode to the clipboard
        :return: Nothing
        """
        row_key, column_key = self.entryview.coordinate_to_cell_key(self.entryview.cursor_coordinate)
        if not row_key:
            return
        this = Episode.as_Folge_by_uid(row_key.value)
        if not this:
            return
        that = TextTemplate.as_PTemplate_by_uid(this.db_template)
        if not that:
            self.app.notify(i18n['Current episode has no template assigned'], severity="warning")
            return
        if not that.tags or len(that.tags) <= 0:
            self.app.notify(i18n['Current episode template has no tags'], severity="warning")
            return
        pyperclip.copy(that.tags)
        self.app.notify(that.tags, title=i18n['Tags copied to clipboard'])

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
        pyperclip.copy(text)
        self.app.notify(text, title=i18n['Description copied to clipboard'])
        # todo: make this configurable
        # APP Copy to clipboard doesnt work everywhere OSC 52:
        # https://darren.codes/posts/textual-copy-paste/
        # App.copy_to_clipboard(this)

    def action_assign_template(self):
        def template_callback(cur_episode: Folge or None):
            if not cur_episode:
                return
            Episode.update_or_create(cur_episode)
            self._refill_table_with_project(self.current_project)

        row_key, column_key = self.entryview.coordinate_to_cell_key(self.entryview.cursor_coordinate)
        if row_key:
            this = Episode.as_Folge_by_uid(row_key.value)
            self.app.push_screen(AssignTemplate(this), template_callback)

    def _refill_table_with_project(self,
           p_uid: int,
           rest_position: None | Literal['above', 'below', 'reset'] = None) -> None:
        """
        Redraws the entire table with the new data from the database, if this project ever scales
        I must probably look into how to update singular cells instead of brute forcing everything
        everytime
        :param p_uid:
        :param rest_position:
        :return:
        """
        #* if Project ID is the same we preserve the cursor position
        was_selected = None
        if p_uid == self.current_project:
            row_key, column_key = self.entryview.coordinate_to_cell_key(self.entryview.cursor_coordinate)
            was_selected = row_key
        # check if project exists
        # get data
        self.entryview.clear(columns=True)
        self.entryview.show_header = True
        self.current_project = p_uid  # even for empty sets the project ID is still set
        data_ep = Episode.by_project(p_uid, order="desc")
        # display dummy text if none is present
        if not data_ep:
            self.entryview.show_header = False
            self.entryview.add_column("Message")
            self.entryview.add_row("No entries for this project")
            return False
        self.entryview.add_column("#")
        self.entryview.add_column("##", key="counter2")
        self.entryview.add_column(i18n['Session'])
        self.entryview.add_column(i18n['Record Date'])
        self.entryview.add_column(i18n['Title'])
        self.entryview.add_column(i18n['Template'])
        # TODO: concat template name into episode
        for each in data_ep:
            template = each.db_template
            if each.joined_template_title:
                template = each.joined_template_title
            self.entryview.add_row(
                *[
                    each.counter1,
                    each.counter2,
                    each.session,
                    each.recording_date.strftime("%d.%m.%Y"),
                    each.title,
                    template
                ],
                key=each.db_uid
            )
        # hide counter2 row when there are now values in there
        if not Project.has_counter2(self.current_project):
            self.entryview.remove_column("counter2")  # the only column with a key as of now
        # highlight the previos cell, I have the sneaking suspicion that this will break somewhen
        if was_selected and was_selected.value:
            new_row = self.entryview.get_row_index(was_selected)
            self.entryview.move_cursor(row=new_row)

    def redraw_project_tree(self) -> int:
        """
        Wastefully loads the entire tree from the database again to make sure its all there again
        if something has changed
        :return: the id of the first entry
        """
        self.projects.reset("") # root empty
        self.projects.root.expand()
        current = self.projects.root.add("Current", expand=True)

        first_entry = -1
        other_categories = []
        # data_pro = get_all_projects()
        data_pro = Project.dump()
        for each in data_pro:
            if first_entry == -1:
                first_entry = each.db_uid
            if each.category == "default":
                temp = current.add_leaf(each.title, data={'db_uid': each.db_uid})
            else:
                if not each.category in other_categories:
                    other_categories.append(each.category)
            if self.current_project and each.db_uid == self.current_project:
                node = temp
        for cat in other_categories:
            current = self.projects.root.add(cat)
            for each in data_pro:
                if each.category != cat:
                    continue
                temp = current.add_leaf(each.title, data={'db_uid': each.db_uid})
                if self.current_project and each.db_uid == self.current_project:
                    node = temp
        # set node to specific entry
        #node = self.projects.get_node_by_id()
        self.projects.select_node(temp)
        return first_entry

    def _init_data(self):
        """Retrieves data from database in bulk for first build of the view"""
        first_entry = self.redraw_project_tree()
        self._refill_table_with_project(first_entry)

