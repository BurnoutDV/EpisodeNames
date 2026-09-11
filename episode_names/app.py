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

import time
import sys
from typing import Iterable

from rich.console import RenderableType
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, RichLog
from textual.screen import ModalScreen, Screen

from episode_names.Modals.DialogueModals import YesNoBox, ConfirmMessageBox
from episode_names.Screens import (
    EpisodeScreen,
    TemplateScreen,
    StatisticScreen,
    SettingsScreen,
    ModularInterface,
    LinkingScreen,
)
from episode_names.Utility import MenuProvider, i18n, user_setup
from episode_names.Utility.db import Settings, EditDelta
from episode_names.Utility.db_aux_utility import previous_versions
from episode_names.__init__ import (
    __version__,
    __author__,
    __license__,
    __appname__,
    __appauthor__,
    __folder_version__,
)


def mirror_s_srk(this_key: str) -> str | None:
    """
    Mirror of Settings.save_retrieve_key because for some reasons somethings
    does not work they way I would it expect to work
    :param this_key:
    :return:
    """
    try:
        res = Settings.select().where(Settings.key == this_key).limit(1).get()
        return res.value
    except Settings.DoesNotExist:
        return None


def mirror_s_uosk(this_key: str, this_value: str) -> bool:
    """
    # ! Same as mirror_s_srk

    :param this_key:
    :param this_value:
    :return:
    """
    return (
        Settings.insert(key=this_key, value=this_value)
        .on_conflict(conflict_target=Settings.key, update={Settings.value: this_value})
        .execute()
    )


class DebugLog(ModalScreen[bool]):
    """
    Sad Excuse for a quick debug log functionality, I am totally aware that there is a way with Textual
    to achieve the same thing without this.
    """

    BINDINGS = [
        ("escape", "back", i18n["Cancel"]),
        ("ctrl+c", "quit", i18n["Quit"]),
    ]

    def __init__(self, log: RichLog):
        self.debug = log
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="log_overlay"):
            yield self.debug
            yield Footer()

    def _action_back(self):
        self.dismiss(True)


class EpisodeNames(App):
    CSS_PATH = "CSS/general.tcss"
    COMMANDS = {MenuProvider}
    COMMAND_PALETTE_BINDING = "circumflex_accent"

    # TODO: idea: activity graph by amount of written words in description
    # TODO: new version confirmation dialogue needs styling

    BINDINGS = [
        Binding(key="escape", action="quit_dial", description=i18n["Quit"], show=False),
        Binding(
            key="f1",
            action="switch_mode('episodes')",
            description=i18n["Episode"],
            show=False,
        ),
        Binding(
            key="f2",
            action="switch_mode('templates')",
            description=i18n["Templates"],
            show=False,
        ),
        Binding(
            key="f3",
            action="switch_mode('linking')",
            description=i18n["Linking"],
            show=False,
        ),
        Binding(
            key="f4",
            action="switch_mode('statistic')",
            description=i18n["Statistic"],
            show=False,
        ),
        #Binding(key="f6",action="switch_mode('modular')",description=i18n["Modular"],show=False,),
        Binding(
            key="f7",
            action="switch_mode('settings')",
            description=i18n["Settings"],
            show=False,
        ),
        Binding(key="f8", action="open_debug", description="Debug", show=False),
    ]

    MODES = {
        "episodes": EpisodeScreen,
        "templates": TemplateScreen,
        "settings": SettingsScreen,
        "linking": LinkingScreen,
        "statistic": StatisticScreen,
        "modular": ModularInterface,
        # "help": HelpScreen,
    }

    def __init__(self):
        user_setup(__appname__, __appauthor__, __folder_version__)
        self.hour_zero = time.time_ns() / 1000000
        self.dummy_log = RichLog(id="dummy_log")
        self.debug_open = False
        self.console_title = (
            f"Episode Names - v{__version__}, DB Version: {__folder_version__}"
        )
        # ? at least for Konsole the set_window_title does not work
        sys.stderr.write(f"\x1b]2;{self.console_title}\x07")
        sys.stderr.flush()
        self.redraw_after_import = False, False
        super().__init__()

    def on_mount(self) -> None:
        # ! Why do i dont have settings here
        if saved_theme := mirror_s_srk("textual_theme"):
            self.theme = saved_theme
        self.console.set_window_title(self.console_title)
        self.app.switch_mode("episodes")
        # check if update has occured
        old_versions = previous_versions()

        unconfirmed = []
        if old_versions:
            for each in old_versions:
                # TODO: make this as unified string somewhere
                if not mirror_s_srk(f"aknowledge_old_version_{each}"):
                    unconfirmed.append(each)
        if unconfirmed:
            self.show_old_db_modal(unconfirmed)

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        yield from super().get_system_commands(screen)
        # hide default commands
        pass

    def write_raw_log(self, this: RenderableType, additional_text=""):
        self.write_log(f"Raw Object: {additional_text}")
        self.dummy_log.write(this)

    def write_log(self, text):
        delta_time = round(time.time_ns() / 1000000 - self.hour_zero, 2)
        self.dummy_log.write(f"{delta_time} - {text}")

    def show_old_db_modal(self, versions: list) -> None:
        if len(versions) <= 0:
            return None

        def dialogue_callback(status: bool):
            if status:  # * aka, checkbox checked for aknowledgement
                for each in versions:
                    mirror_s_uosk(f"aknowledge_old_version_{each}", "checked")

        self.app.push_screen(
            ConfirmMessageBox(
                i18n.t("Old_Version_blues", {"%%versions%%": ", ".join(versions)}),
                aknowledge=True,
                confirm_text=i18n["Confirm that you understand and have read"],
            ),
            dialogue_callback,
        )

    def _action_show_templates(self):
        self.app.switch_mode("templates")

    def action_debug(self):
        """
        A malable command for the command palette that does whatever I need
        just right now combined in a convenient reachable place
        :return:
        """
        # ? currently: Theme Variables:
        # self.write_raw_log(self.app.theme_variables)
        # ? test settings
        # self.write_raw_log(Settings.get_keys(["db_version", "textual_theme", "bdsgsfg"]))
        # self.write_raw_log(Settings.get_keys(["db_version", "textual_theme", "bdsgsfg"], False))
        # ? i18n tests
        #self.write_raw_log(i18n.color_map)
        self.write_raw_log(EditDelta.get_all_episode_edits(392))

    def _action_open_debug(self):
        if self.debug_open:
            return

        def handle_debug(diss: bool):
            self.debug_open = False

        self.debug_open = True
        self.app.push_screen(DebugLog(self.dummy_log), handle_debug)

    def action_quit(self) -> None:
        # TODO: save other interface choices here
        mirror_s_uosk("textual_theme", self.app.theme)
        self.exit(message=i18n["Thanks for choosing EpisodeNames"])

    def action_quit_dial(self):
        def handle_quit_message(dec: bool):
            if dec:
                self.action_quit()

        self.app.push_screen(
            YesNoBox(i18n["Do you want to quit?"]), handle_quit_message
        )


def run_main():
    print("Running App")
    app = EpisodeNames()
    app.run()


if __name__ == "__main__":
    run_main()
