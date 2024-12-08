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
from textual.widgets import ListView, ListItem, Footer, Input, Tree, Label, TextArea, Collapsible
from textual.screen import Screen

from episode_names.Modals.DialogueModals import YesNoBox
from episode_names.Utility import i18n
from episode_names.Utility.db import TextTemplate, PatternTemplate

class TemplateScreen(Screen):
    BINDINGS = [
        Binding(key="ctrl+n", action="new", description=i18n['Create New']),
        Binding(key="ctrl+d", action="duplicate", description=i18n['Duplicate Current']), #TODO: implement
        Binding(key="ctrl+s", action="save", description=i18n['Save Current']),
        Binding(key="ctrl+del", action="delete", description=i18n['Delete Current']),
        Binding(key="ctrl+l", action="discard", description=i18n['Discard Current']),
        Binding(key="f9", action="toogle_help", description=i18n['Toogle Help'])
    ]

    HELPER_TOKENS = [
        "$$title$$",
        "$$session$$",
        "$$counter1$$",
        "$$counter2$$",
        "$$record_date$$",
    ]

    def __init__(self):
        self.filter_bar = Input(id="filter", placeholder=i18n['Enter Filter here'], classes="small_input")
        self.templates = Tree("Label", id="template_list")
        self.pattern_name = Input(id="pattern_name", placeholder="Name of the Pattern", disabled=True)
        self.pattern = TextArea(id="pattern", disabled=True, soft_wrap=True, show_line_numbers=True)
        self.tags = TextArea(id='tags', disabled=True, soft_wrap=True)
        self.helper = ListView(id='helper')
        # TODO: define own highlighting scheme for textarea
        self.current_pattern = None
        self.unsaved_patterns: dict[int, PatternTemplate] = {}
        # TODO: logic for not saved patterns
        # TODO: save cursor positions?
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(i18n["Template Edit"])
            with Horizontal():
                with Vertical(classes="sidebar"):
                    yield self.filter_bar
                    yield self.templates
                    yield self.helper
                with Vertical():
                    yield self.pattern_name
                    yield self.pattern
                    with Collapsible(collapsed=True, title=i18n['Tags'], id="tag_collapse"):
                        yield self.tags
            yield Footer()

    def on_mount(self):
        self.templates.show_root = False
        self.templates.show_guides = False
        self.update_pattern_list()
        self.templates.focus()
        for each in TemplateScreen.HELPER_TOKENS:
            self.helper.append(ListItem(Label(each)))
        self.helper.styles.height = len(TemplateScreen.HELPER_TOKENS)
        self.helper.display = False

    @on(Tree.NodeSelected, "#template_list")
    def _select_project(self, message: Tree.NodeSelected):
        if not message.node.data:
            return False
        if not message.node.data['db_uid']:
            return False
        uid = message.node.data['db_uid']
        data = TextTemplate.as_PTemplate_by_uid(uid)
        if not data:
            self.app.notify(i18n['Template with this ID is not in Database'])
            self.app.write_log(f"DB does not know template with ID {uid}")
            return False
        if self.current_pattern and data.db_uid == self.current_pattern.db_uid:
            """If we actually load the same template again we dont do anything, some
            awkward tests if the objects actually checking like when self.current_pattern
            really exists"""
            return
        if self.current_pattern and (self.pattern.text != self.current_pattern.pattern or
            self.pattern_name.value != self.current_pattern.title or
            self.current_pattern.db_uid == -1):  # in case of new template
            def callback_box(status: bool):
                """
                Callback function for the following dialogue
                But I am that unsure if I am actually allowed
                to use the variable from the wider scope
                """
                if status:
                    self._action_save() # if we want to save we save
                self.set_editor(data) # in any case set editor text
            self.app.push_screen(YesNoBox(i18n['Do you want to save']), callback_box)
        else:
            self.set_editor(data)

    def _action_save(self):
        if not self.current_pattern:
            return
        self.current_pattern.pattern =  self.pattern.text
        self.current_pattern.title = self.pattern_name.value
        self.current_pattern.tags = self.tags.text
        TextTemplate.update_or_create(self.current_pattern)
        self._action_discard() # clear up view
        self.update_pattern_list()

    def _action_discard(self):
        self.current_pattern = None
        self.pattern_name.disabled = True
        self.pattern_name.value = ""
        self.pattern.disabled = True
        self.pattern.clear()
        self.query_one('#tag_collapse').collapsed = True
        self.tags.disabled = True
        self.tags.clear()
        self.templates.focus()

    def _action_toogle_help(self):
        if self.helper.display:
            self.helper.display = False
        else:
            self.helper.display = True

    def _action_new(self):
        next_id = TextTemplate.get_next_id()
        new_template = PatternTemplate(
            f"template {next_id}",
            "$$counter1$$",
            "",
        )
        self.set_editor(new_template)

    def set_editor(self, this: PatternTemplate):
        self.pattern_name.disabled = False
        self.pattern_name.value = this.title
        self.pattern.disabled = False
        self.pattern.load_text(this.pattern)
        self.pattern.move_cursor((0,0))
        self.pattern.focus()
        self.current_pattern = this
        self.tags.disabled = False
        if this.tags:
            self.tags.load_text(this.tags)
            self.tags.move_cursor((0,0))
        else:
            self.tags.clear()

    # TODO: on change self.tags update title of template thingy to show number of characters

    def update_pattern_list(self, title_filter=""):
        # Todo: you use this to learn about reactive attributes
        patterns = TextTemplate.dump()
        self.templates.clear()
        self.templates.root.expand()
        if not patterns: # empty list
            self.templates.root.add_leaf(i18n['No Elements present'])
            return
        #self.app.write_raw_log(patterns)
        for each in patterns:
            line = f"{each.title} [#{each.db_uid}-{len(each.pattern)}]"
            self.templates.root.add_leaf(line, data={'db_uid': each.db_uid})
