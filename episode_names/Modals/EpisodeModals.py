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

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.message import Message
from textual.widgets import DataTable, Footer, Input, Button, Tree, Label, Select, TextArea, OptionList, Header, Collapsible
from textual.widgets.option_list import Option
from textual.screen import ModalScreen

from episode_names.Utility import i18n, wlen
from episode_names.Utility.db import Project, Playlist, Episode, Folge, TextTemplate, PatternTemplate
from episode_names.Utility.custom_widgets import DateInput

class AssignTemplate(ModalScreen[TextTemplate or None]):
    BINDINGS = [
        Binding(key="ctrl+s, enter", action="save", description=i18n['Save']),
        Binding(key="escape", action="abort", description=i18n['Cancel'], priority=True)
    ]

    CSS_PATH = "../CSS/EpisodeModals.tcss"

    # TODO: no option id note??? - 2026-04-28 what?

    def __init__(self, hot_episode: Folge):
        self.current_episode = hot_episode
        self.locked_widgets = True
        self.cache = dict()
        super().__init__()

    class UnLockWidgets(Message):
        pass

    def compose(self) -> ComposeResult:
        self.preview = TextArea("", id="preview_stuff", read_only=True)
        self.templates = OptionList("", id="template_list", classes="sidebar max-height")
        self.locked_widgets = True

        with Vertical(classes="generic_modal_main"):
            # TODO: proper insert i18n here
            yield Label(f"{i18n['Assign Template']} - {self.current_episode.counter1} - {self.current_episode.title}")
            with Horizontal(classes="max-height"):
                yield self.templates
                yield self.preview
            with Horizontal(classes="adjust"):
                yield Button(i18n['Save'], id="save")
                yield Button(i18n['Cancel'], id="abort")
            yield Footer()

    def on_mount(self) -> None:
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
        self.templates.add_option(None)
        for each in list_of_templates:
            self.templates.add_option(Option(each.title, str(each.db_uid)))
            self.cache[str(each.db_uid)] = each  # Option Index are strings
        if self.current_episode.db_template > 0:
            index = self.templates.get_option_index(str(self.current_episode.db_template))
        else:
            index = self.templates.get_option_index("-1")
        self.templates.highlighted = index
        #self.app.write_raw_log(self.cache, "Template Cache")
        self.post_message(self.UnLockWidgets())

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


    def _list_selected(self, selected: OptionList.OptionHighlighted) -> None:
        """
        When Enter Key pressed, uses that template and instantly closes the modal with the
        selected options as new template
        :param selected:
        :return:
        """
        if self.locked_widgets:
            return
        if not selected.option_id:
            self.app.notify(f"AssignTemplate: {i18n['No Option ID']}", severity="warning")
            return
        if selected.option_id in self.cache:  # aka a know database variable
            self.save_and_exit(int(selected.option_id))
        if selected.option_id == "-1":
            self.save_and_exit(-1)

    @on(OptionList.OptionSelected, "#template_list") # for mouse use
    @on(OptionList.OptionHighlighted, "#template_list") # for keyboard use
    def _list_highlighted(self, selected: OptionList.OptionHighlighted) -> None:
        """
        Previews the currently highlighted option by displaying the template text in
        the textarea, information cached. I hope this will never be a problem.
        :param selected:
        :return:
        """
        if self.locked_widgets:
            return
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

    @on(UnLockWidgets)
    def __unlock_widgets(self):
        self.locked_widgets = False

class CreateEditEpisode(ModalScreen[Folge or None]):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="escape", action="abort", description=i18n['Cancel'], priority=True)
    ]

    CSS_PATH = "../CSS/EpisodeModals.tcss"

    def __init__(self, copy_from: None or Folge = None, p_uid: int = 0):
        self.copy_from = copy_from
        if not self.copy_from and p_uid:
            current_play = Project.as_Playlist_by_uid(p_uid)
            if current_play:
                self.copy_from = Folge(
                    title="",
                    description="",
                    desc_addon="",
                    notes="",
                    yt_link=None,
                    db_project=current_play.db_uid
                )
        super().__init__()

    def compose(self) -> ComposeResult:
        self.gui_title = Input(placeholder=i18n['Title'])
        self.gui_session = Input(placeholder=i18n['Session'], classes="compact_input")
        self.gui_date = DateInput(placeholder=i18n['Date'], classes="compact_input") # TOdO: find date widget or constrained
        self.gui_counter1 = Input(placeholder="#", classes="compact_input", type="integer")
        self.gui_counter2 = Input(placeholder="##", classes="compact_input", type="integer")
        self.description = TextArea(id="tx_description", soft_wrap=True, show_line_numbers=True)
        self.desc_addon = TextArea(id="tx_desc_addon", soft_wrap=True, show_line_numbers=True)
        with Vertical(classes="generic_modal_main"):
            with Vertical():
                yield Label(f"Edit or Create Entry", classes="title")
                with Horizontal(classes="main_title"):
                    yield self.gui_title
                with Horizontal(classes="compact_line"):
                    yield self.gui_session
                    yield self.gui_date
                    yield self.gui_counter1
                    yield self.gui_counter2
                with Collapsible(collapsed=True, title=i18n['Description Addon'], id="Desc_Addon"):
                    yield self.desc_addon
                with Collapsible(collapsed=True, title=i18n['Description'], id="Description"):
                    yield self.description
                #yield Checkbox("apply retrograde")
                with Horizontal(classes="adjust"):
                    yield Button(i18n['Save'], id="save")
                    yield Button(i18n['Cancel'], id="abort")
            yield Footer()

    def on_mount(self) -> None:
        if isinstance(self.copy_from, Folge):
            self.gui_title.value = self.copy_from.title
            self.gui_title.border_title = i18n['Title']
            self.gui_session.value = self.copy_from.session
            self.gui_session.border_subtitle = i18n['Session']
            self.gui_date.value = self.copy_from.recording_date.strftime("%d.%m.%Y")
            self.gui_date.border_subtitle = i18n['Date']
            self.gui_counter1.value = str(self.copy_from.counter1)
            self.gui_counter1.border_subtitle = "#"
            self.gui_counter2.value = str(self.copy_from.counter2)
            self.gui_counter2.border_subtitle = "##"
            self.description.text = str(self.copy_from.description)
            self.desc_addon.text = str(self.copy_from.desc_addon)

        else:
            # there has to be some kind of copy from
            self.app.notify(i18n['No suiteable creation method for episode found'], severity="error")
            self.dismiss(None)

    def _action_save(self):
        form = self._get_form_as_folge()
        if form:
            self.dismiss(form)

    def _get_form_as_folge(self):
        try:
            # TODO: use agree upon dateform from settings here
            rec_date = datetime.strptime(self.gui_date.value, "%d.%m.%Y").date()
        except ValueError:
            rec_date = None
        try:
            return Folge(
                title=self.gui_title.value,
                db_uid=self.copy_from.db_uid if self.copy_from else -1,
                db_project=self.copy_from.db_project if self.copy_from else 0,
                db_template=self.copy_from.db_template if self.copy_from else None,
                yt_link=self.copy_from.yt_link if self.copy_from else None,
                yt_human_touch=self.copy_from.yt_human_touch if self.copy_from else None,
                counter1=int(self.gui_counter1.value), # TODO: maybe buffer this with except dude
                counter2=int(self.gui_counter2.value),
                # extra_counter= NO WIDGET YET
                session=self.gui_session.value,
                description=self.description.text.strip(),
                desc_addon=self.desc_addon.text.strip(),
                recording_date=rec_date if rec_date else date.today(),
            )
        except ValueError:
            self.app.notify(i18n['Counter1&2 have to be Numbers'],severity="error")
            return None

    def _action_abort(self):
        from episode_names.Modals import YesNoBox # ? Local Import because reasons
        # TODO make this configurable, maybe on a per-form basis
        form = self._get_form_as_folge()
        if not form: # ! this is a bit stupid, if the counters are wrong no warning
            self.dismiss(None) # ? in theory, they cant be; input cannot accept..but...users..
        if self.copy_from and self.copy_from != form:
            def callback_box(status: bool):
                if status:
                    self.dismiss(None)
                    return
            self.app.push_screen(YesNoBox(i18n['Data has changed, discard changes?']), callback_box)
        else:
            self.dismiss(None)

    @on(Button.Pressed, "#save")
    def _btn_save(self):
        self._action_save()

    @on(Button.Pressed, "#abort")
    def _btn_abort(self):
        self._action_abort()

    @on(TextArea.Changed, "#tx_description")
    def _on_description_length_change(self):
        d_len = wlen(self.description.text)
        if d_len > 0:
            self.query_exactly_one("#Description").title = f"{i18n['Description']} [{i18n.t('combo_words', {'%%number%%': d_len})}]"
        else:
            self.query_exactly_one("#Description").title = i18n['Description']

    @on(TextArea.Changed, "#tx_desc_addon")
    def _on_desc_addon_length_change(self):
        a_d_len = len(self.desc_addon.text)
        if a_d_len > 0:
            self.query_exactly_one("#Desc_Addon").title = f"{i18n['Description Addon']} [{i18n.t('combo_chars', {'%%number%%': a_d_len})}]"
        else:
            self.query_exactly_one("#Desc_Addon").title = i18n['Description Addon']

    @on(Collapsible.Expanded) # assuming there is only two
    def _collapse_bonanza(self, message: Collapsible.Toggled) -> None:
        """
        Closes the other collapsible
        """
        if message.collapsible.id == "Desc_Addon":
            other = "#Description"
        else:
            other = "#Desc_Addon"
        self.query_exactly_one(other).collapsed = True


class WriteNoteModal(ModalScreen[Folge | Playlist | str | None]):
    """
    A multipurpose modal to write 'notes' or any multi lined text that can be done on the fly
    while editing any object. Originally I wanted this to write notes to episodes and playlists
    but then realized that I might as well create it a bit more open-ended so it can be used
    for something else
    """
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="escape", action="abort", description=i18n['Cancel'], priority=True),
        Binding(key="ctrl+r", action="reset", description=i18n['Reset'])
    ]

    CSS_PATH = "../CSS/EpisodeModals.tcss"

    def __init__(self, notes: Folge | Playlist | str | None = None, option: str = "note"):
        self.notes: Folge | Playlist | str | None = None
        if isinstance(notes, Folge):
            self.modus = 0
            self.notes = notes
        elif isinstance(notes, Playlist):
            self.modus = 1
            self.notes = notes
        else:
            self.modus = 2
            self.notes = notes
        if option == "desc_addon":
            self.note_attr = "desc_addon"
            self.modus = 3
        elif option == "description":
            self.modus = 4
            self.note_attr = "description"
        else: # std mode, as before I added descriptions
            self.note_attr = "notes"
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="wrapper", classes="generic_modal_main"):
            with Vertical():
                yield Header(id="headline")
                # TODO: collapse when others are open
                with Horizontal(classes="max-height"):
                    yield TextArea(text="", id="note_area")
                with Horizontal(classes="adjust"):
                    yield Button(i18n['Save'], id="btn_save")
                    yield Button(i18n['Cancel'], id="btn_abort")
            yield Footer()

    def on_mount(self) -> None:
        note_text: TextArea = self.query_exactly_one("#note_area")
        if self.modus <= 4:
            if self.notes.__getattribute__(self.note_attr): # * it might be Null
                note_text.load_text(self.notes.__getattribute__(self.note_attr))
        else:
            if self.notes: # and is not none
                note_text.load_text(self.notes)
        if self.modus == 0: # * Episode / Folge
            self.title = i18n['Edit/Write note for episode']
            self.sub_title = f"#{self.notes.counter1} - {self.notes.title}"
        elif self.modus == 1: # * Playlist / Project
            self.title = i18n['Project notes']
            self.sub_title = self.notes.title
            # * additional changes to the design
            wrapper : Vertical = self.query_exactly_one("#wrapper")
            wrapper.add_class('no_height_limit')
            tx_area : TextArea = self.query_exactly_one("#note_area")
            tx_area.soft_wrap = True
            tx_area.show_line_numbers = True
        elif self.modus == 3: # * Change Additional Description
            self.title = i18n['Edit Description Addon']
            self.sub_title = f"#{self.notes.counter1} - {self.notes.title}"
        elif self.modus == 4: # * Change Solo Description
            self.title = i18n['Edit Episode Description']
            wrapper: Vertical = self.query_exactly_one("#wrapper")
            wrapper.add_class('no_height_limit') # a bit bigger but not as big as project_note
            self.sub_title = f"#{self.notes.counter1} - {self.notes.title}"
        else:
            self.title = i18n['Generic Note Window']

    def action_reset(self):
        """
        Returns text area to init status
        :return:
        """
        note_text: TextArea = self.query_exactly_one("#note_area")
        note_text.load_text("") # reset
        self.on_mount()

    @on(Button.Pressed, "#btn_save")
    def _action_save(self):
        note_text: TextArea = self.query_exactly_one("#note_area")
        if self.modus <= 4: # Episode OR Playlist
            self.notes.__setattr__(self.note_attr, note_text.text.strip())
            self.dismiss(self.notes)
        else:
            self.dismiss(note_text.text)

    @on(Button.Pressed, "#btn_abort")
    def _action_abort(self):
        self.dismiss(None)

class GenericCopyModal(ModalScreen[str | None]):
    BINDINGS = [
        Binding(key="ctrl+s", action="save", description=i18n['Save']),
        Binding(key="escape", action="abort", description=i18n['Cancel'], priority=True)
    ]

    CSS_PATH = "../CSS/EpisodeModals.tcss"

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        pass

    def on_mount(self) -> None:
        pass

    def _action_save(self):
        self.dismiss("some text here alan")

    def _action_abort(self):
        self.dismiss(None)