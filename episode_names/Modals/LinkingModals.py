#!/usr/bin/env python3
# coding: utf-8
import copy
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
    Collapsible, TabbedContent, TabPane, Placeholder, Checkbox
from textual.widgets.option_list import Option
from textual.screen import ModalScreen

from episode_names.Utility import i18n, get_tree_node_with_data
from episode_names.Utility.db import Episode, Project, YtVideo, YtPlaylist, Folge, TextTemplate, PatternTemplate, \
    Settings
from episode_names.Utility import find_related_project, find_related_folge


class LinkVideoModal(ModalScreen[Folge]):
    CSS_PATH = "../CSS/LinkingModals.tcss"
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="ctrl+p", action="preview", description=i18n['Preview']),
        Binding(key="escape", action="abort", description=i18n['Cancel'], priority=True)
    ]
    CHECK_WIDGET_LINK = { # TODO: condense this further, its the same names with prefix anyway
        'chk_title': 'title',
        'chk_description': 'description',
        'chk_counter1': 'counter1',
        'chk_counter2': 'counter2',
        'chk_session': 'session',
        'chk_date': 'date',
        'chk_desc_addon': 'desc_addon',
    }
    MODE_SELECT_PRESETS = {
        0: [],
        1: ['chk_description'],
        2: ['chk_title', 'chk_description']
    }
    FOLGE_WIDGET_LINK = { # links the Folge attributes to the widgets on the right
        "title": "title",
        "description": "description",
        "counter1": "counter1",
        "counter2": "counter2",
        "session": "session",
        "date": "recording_date",
        "desc_addon": "desc_addon"
    }
    def __init__(self, video: Folge):
        self.video: Folge = video
        self.current_folge: Folge | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        IDEA Time:
        Left side, episode edit view with the data from the current extracted info
        make it able to actually edit text there that can be written later
        middle has search interface, first tab recommendation, second is actual
        search for everything in the database (probably build this last)
        right is enlarged episode menu, make checkboxes at any field if
        you want to overwrite thse (and change border color I guess)
        maybe on top combo box to select a pre-select template for which
        fields to overwrite
        :return:
        """
        with Horizontal(id="main"):
            with Vertical():
                with Horizontal():
                    with ScrollableContainer(id="left"):
                        yield Label(i18n['Transcriped YT Data'])
                        yield Input(placeholder="yt title", id="yt_title")
                        yield TextArea(placeholder="yt desc", id="yt_description")
                        with Horizontal(classes="shrinkwrap"):
                            yield Input(placeholder=i18n['Session'], classes="compact_input", id="yt_session")
                            yield Input(placeholder=i18n['Date'], classes="compact_input", id="yt_date")
                        with Horizontal(classes="shrinkwrap"):
                            yield Input(placeholder="#", classes="compact_input", type="integer", id="yt_counter1")
                            yield Input(placeholder="##", classes="compact_input", type="integer", id="yt_counter2")
                            # TODO: extra counter
                        with Collapsible(collapsed=True, title=i18n['Description Addon'], id="yt_Desc_Addon_collapse"):
                            yield TextArea(id="yt_desc_addon", soft_wrap=True, show_line_numbers=True)
                    with TabbedContent(id="middle"):
                        with TabPane("Recommend"):
                            yield Tree(label="Recommended videos", id="recommends")
                        with TabPane("Database"):
                            yield Input(placeholder="project filter")
                            yield Tree("Projects")
                            yield Input(placeholder="episode filter")
                            yield Tree("Episodes")
                    with Vertical(id="right"):
                        yield Select([('Just Link', 0), ('Link & Description', 1), ('Title, Description', 2)],
                                     compact=True,
                                     allow_blank=True,
                                     id="mode_select")
                        # TODO: remember last selection, also make it configurable?
                        with Horizontal(classes="shrinkwrap"):
                            yield Checkbox(classes="minimal", id="chk_title")
                            yield Input(placeholder=i18n['Title'], id="fl_title")
                        with Horizontal(classes="shrinkwrap"):
                            yield Checkbox(classes="minimal", id="chk_description")
                            yield TextArea(id="fl_description", soft_wrap=True)
                        with Horizontal(classes="shrinkwrap"):
                            yield Checkbox(classes="minimal", id="chk_session")
                            yield Input(placeholder=i18n['Session'], classes="compact_input", id="fl_session")
                            yield Checkbox(classes="minimal", id="chk_date")
                            yield Input(placeholder=i18n['Date'], classes="compact_input", id="fl_date")
                        with Horizontal(classes="shrinkwrap"):
                            yield Checkbox(classes="minimal", id="chk_counter1")
                            yield Input(placeholder="#", classes="compact_input", type="integer", id="fl_counter1")
                            yield Checkbox(classes="minimal", id="chk_counter2")
                            yield Input(placeholder="##", classes="compact_input", type="integer", id="fl_counter2")
                        with Horizontal():
                            yield Checkbox(classes="minimal", id="chk_desc_addon")
                            with Collapsible(collapsed=True, title=i18n['Description Addon'], id="col_desc_addon"):
                                yield TextArea(id="fl_desc_addon", soft_wrap=True, show_line_numbers=True)

                with Horizontal(classes="adjust"):
                    yield Button(i18n['Save'], id="save")
                    yield Button(i18n['Preview'], id="preview")
                    yield Button(i18n['Cancel'], id="abort")

    def _on_mount(self, event: events.Mount) -> None:
        if not self.video: # this makes no sense if somehow nothing is given
            self.dismiss(None)
        # fill right side widgets
        for wdg_id, attr in self.FOLGE_WIDGET_LINK.items():
            temp = self.query_one(f"#yt_{wdg_id}")
            if isinstance(temp, TextArea):  # this kills any lines i wanted to save
                temp.text = self.video.__getattribute__(attr)
            else:
                # counter 1 & 2 are ints, but casting it as str is never wrong
                temp.value = str(self.video.__getattribute__(attr))
        self.query_exactly_one("#mode_select").value = int(Settings.save_retrieve_key("linking_mode_select", 0))
        # ? Populate recommend
        # TODO maybe make this async, it feels like this is a big ressource hog
        recommends: Tree = self.query_exactly_one("#recommends")
        recommends.show_root = False
        recommends.show_guides = False
        recommends.clear()
        recommends.root.expand()
        # TODO: the bad words should probably a config or something
        recs: dict[int, Folge] = find_related_folge(self.video)
        # ? Unlike the related_project function this one gives entire Folge entitites
        # ? back that we then can bind to the tree directly, without requesting them anew
        if not recs:
            recommends.root.add_leaf(i18n['No recommendations'])
            return
        first_hit = None
        for key, entry in recs.items():
            if not first_hit:
                first_hit = key
            # ? the part with the db_uid is a legacy thing, its everywhere else
            format_entry = f"{entry.project_title} - #{entry.counter1} {entry.title} Desc:{len(entry.description)},Add:{bool(entry.desc_addon)},Note:{bool(entry.notes)}"
            recommends.root.add_leaf(format_entry, data={'db_uid': key, 'folge': entry})
        # Select first hit automatically
        if first_hit:
            recommends.select_node(get_tree_node_with_data(recommends, first_hit, 'db_uid'))
        # Right Side
        self.update_folge_side(None, True)

    def update_folge_side(self, a_folge: Folge | None, disable_all = False):
        for each in self.FOLGE_WIDGET_LINK.keys():
            self.query_one(f"#fl_{each}").disabled = disable_all
        col_desc_addon: Collapsible = self.query_one("#col_desc_addon")
        col_desc_addon.collapsed = True
        col_desc_addon.disabled = disable_all
        if disable_all:
            a_folge = Folge("empty") # we need that dummy, otherwise its not possible to not give it
            return
        for key, value in self.FOLGE_WIDGET_LINK.items():
            temp = self.query_one(f"#fl_{key}")
            if isinstance(temp, TextArea): # this kills any lines i wanted to save
                temp.text = a_folge.__getattribute__(value)
            else:
                # counter 1 & 2 are ints, but casting it as str is never wrong
                temp.value = str(a_folge.__getattribute__(value))

    @on(Checkbox.Changed) # in this case the normal on_checkbox_changed function would have worked too
    def checkbox_change(self, event: Checkbox.Changed):
        if event.checkbox.id not in self.CHECK_WIDGET_LINK:
            return  # third party checkbox # ? yes, I know that those should not exists..anyway
        this: Checkbox = self.query_one(f"#{event.checkbox.id}")
        that: Input | TextArea = self.query_one(f"#fl_{self.CHECK_WIDGET_LINK[event.checkbox.id]}")
        if event.checkbox.value: # == True
            that.add_class("chk_selected")
            this.add_class("chk_selected")
        else:
            that.remove_class("chk_selected")
            this.remove_class("chk_selected")
        # ? automagically select the correct preset if the configuration is matching with a preset
        # ALL THIS BECAUSE ASYNC
        # TODO: do this with bubble messages, would be cleaner
        """Story time folks, because big block comments are totally what every coding tutor teaches you, messages in 
        textual 'bubble', I first tried to do a good ol' variable that just locks the changes when the select is used
        but that wont work, because the message that a checkbox has changed will bubble afterwards when everything
        in the Select Widget message handler is done, so setting a temporary variable to false to not reset the 
        Select widget does nothing. This has the one advantage that I actually update the preset selection to everything
        even if not explicitly called out. I am btw quite sure my weird check if the correct combinations of TRUEs in
        the two arrays can be done in a very pythonic and lean way
        """
        chk_values = {}
        # I am "saving" the stati temporarily here instead of quering 3times, not sure if that does anything
        for each in self.CHECK_WIDGET_LINK.keys():
            chk_values[each] = self.query_one(f"#{each}").value
        mode_select = Select.NULL
        for mode, chks in self.MODE_SELECT_PRESETS.items():
            mode_select = mode
            for each, state in chk_values.items():
                if (state and each not in chks) or (not state and each in chks):
                    mode_select = Select.NULL
                    break
            if mode_select == mode:
                self.query_one("#mode_select").value = mode_select
                return
        self.query_one("#mode_select").value = mode_select


    @on(Tree.NodeSelected, "#recommends")
    def _select_folge(self, message: Tree.NodeSelected):
        if not message.node.data or "folge" not in message.node.data:
            return False
        self.current_folge = copy.copy(message.node.data['folge'])
        self.update_folge_side(self.current_folge)

    @on(Select.Changed, "#mode_select")
    def _mode_select(self, message: Select.Changed):
        """
        Handler for the mode select which are basically presets of selected checkboxes
        """
        if message.select.is_blank():
            return
        for wdg_id in self.CHECK_WIDGET_LINK:
            wdg: Checkbox = self.query_one(f"#{wdg_id}")
            if wdg_id in self.MODE_SELECT_PRESETS[message.select.value]:
                wdg.value = True
            else:
                wdg.value = False

    @on(Button.Pressed, "#preview")
    def _action_preview(self):
        """
        Copies the selected changes over to the actual episode to see (and being able to edit)
        the changes
        :return:
        """
        if not self.current_folge:
            return
        # TODO: use the actual widget content and not the generating temp Video-Episode
        for chk_id, wdg_id in self.CHECK_WIDGET_LINK.items():
            if self.query_one(f"#{chk_id}").value is True: # we are verbose today arent we?
                wdg = self.query_one(f"#fl_{wdg_id}")
                if isinstance(wdg, TextArea):
                    wdg.text = self.video.__getattribute__(self.FOLGE_WIDGET_LINK[wdg_id])
                else:
                    wdg.value = str(self.video.__getattribute__(self.FOLGE_WIDGET_LINK[wdg_id]))

    @on(Button.Pressed, "#save")
    def _action_save(self):
        if not self.current_folge:
            self.app.notify(i18n['Cannot save when no episode is selected'], severity="warning")
        # save select status
        sl_mode: Select = self.query_one("#mode_select")
        if sl_mode.value != Select.NULL:
            Settings.update_or_set_key("linking_mode_select", str(sl_mode.value))
        # TODO: as in btn_preview, use actual widget content (or just trigger preview beforehand?)
        for chk_id, wdg_id in self.CHECK_WIDGET_LINK.items():
            if self.query_one(f"#{chk_id}").value is True: # we are verbose today arent we?
                # holy lookup table inception batman!
                attr = self.FOLGE_WIDGET_LINK[wdg_id]
                self.current_folge.__setattr__(attr, self.video.__getattribute__(attr))
        self.current_folge.yt_link = self.video.yt_link
        # the fact that we use the modal means humans are involved
        self.current_folge.yt_human_touch = True
        self.dismiss(self.current_folge)

    @on(Button.Pressed, "#abort")
    def _action_abort(self):
        # TODO: if selected Folge was changed show "are ya shore" dialogue
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
        # TODO: the bad words should probably a config or something
        recs = find_related_project(self.playlist.yt_id, additional_bad_words=["Let's", "Play"])
        if not recs:
            recommends.root.add_leaf(i18n['No recommendations'])
            return
        for key, entry in recs.items():
            recommends.root.add_leaf(entry['name'], data={'db_uid': key})

    @on(Button.Pressed, "#save")
    def _btn_save(self):
        recommends: Tree = self.query_exactly_one("#recommends")
        if recommends.cursor_node.data and 'db_uid' in recommends.cursor_node.data:
            # so we got the ID of the project
            self.dismiss(recommends.cursor_node.data['db_uid']) # maybe brittle?
            return
        self.app.notify(i18n['No valid project selected'], severity="warning")

    @on(Button.Pressed, "#abort")
    def _btn_abort(self):
        self.dismiss(None)