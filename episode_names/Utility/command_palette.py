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

"""
Class that provides the command palette for the main app

Code "inspired"* by https://github.com/darrenburns/posting

* outright stolen because that's the one example I could find
"""
from functools import partial
from typing import TYPE_CHECKING, cast
from textual.command import Hit, Hits, Provider, DiscoveryHit
from textual.types import IgnoreReturnCallbackType


from episode_names.Utility.db_operations import create_project
from episode_names.Utility.i18n import i18n

if TYPE_CHECKING:
    from episode_names.app import EpisodeNames

class MenuProvider(Provider):

    @property
    def commands(self,) -> tuple[tuple[str, IgnoreReturnCallbackType, str, bool], ...]:
        app = self.episode_names
        screen = self.screen

        commands_to_show: list[tuple[str, IgnoreReturnCallbackType, str, bool]] = []

        from episode_names.Screens.EpisodesScreen import EpisodeScreen
        from episode_names.Utility.db import Project, Playlist, Episode, Folge

        if isinstance(screen, EpisodeScreen):
            ## create project - always there
            create_project = (
                i18n["project: Create a new Project"],
                screen._action_create_project_menu,
                i18n['Opens a menu to create an entire new project from scratch'],
                True,
            )
            commands_to_show.append(create_project)
            if screen.current_project: # levels down
                current_project = Project.as_Playlist_by_uid(screen.current_project)
            if current_project: # security check for some weirdness that will never happen
                ### edit project
                edit_project = (
                    i18n.t('Edit Project', {'%%P%%': current_project.title}),
                    partial(screen._open_edit_project_menu, current_project.db_uid),
                    i18n.t('Edit Project Helper', {'%%P%%': current_project.title, '%%DB%%': current_project.db_uid}),
                    True,
                )
                commands_to_show.append(edit_project)
                ### create episode
                last_episode = Episode.get_latest(current_project.db_uid)
                i18n_decider = 'Create Episode helper' if last_episode else 'Create Episode helper blank'
                create_episode = (
                    i18n['episode: Create Episode'],
                    screen._action_new_entry,
                    i18n.t(i18n_decider, {'%%P%%': current_project.title}),
                    True,
                )
                commands_to_show.append(create_episode)
                ### edit episode
                row_key, column_key = self.screen.entryview.coordinate_to_cell_key(
                    self.screen.entryview.cursor_coordinate)
                if row_key:
                    this = Episode.as_Folge_by_uid(row_key.value)
                    if this:
                        edit_episode = (
                            i18n.t('Edit Episode', {'%%E%%': this.title}),
                            screen._action_edit_entry,
                            i18n.t('Edit Episode Helper', {'%%E%%': this.title, '%%P%%': current_project.title}),
                            True,
                        )
                        commands_to_show.append(edit_episode)

        # default stuff reimagined
        if not app.ansi_color:
            commands_to_show.append(
                (
                    i18n["theme: Change theme"],
                    app.action_change_theme,
                    i18n["Change the current theme"],
                    True,
                ),
            )

        if screen.query("HelpPanel"):
            commands_to_show.append(
                (
                    i18n["help: Hide keybindings sidebar"],
                    app.action_hide_help_panel,
                    i18n["Hide the keybindings sidebar"],
                    True,
                ),
            )
        else:
            commands_to_show.append(
                (
                    i18n["help: Show keybindings sidebar"],
                    app.action_show_help_panel,
                    i18n["Display keybindings for the focused widget in a sidebar"],
                    True,
                ),
            )

        commands_to_show.append(
            (
                i18n["app: Quit episode_names"],
                app.action_quit,
                i18n["Quit episode_names and return to the command line"],
                True,
            ),
        )
        return tuple(commands_to_show)

    async def discover(self) -> Hits:
        """Handle a request for the discovery commands for this provider.
        Yields:
            Commands that can be discovered.
        """
        for name, runnable, help_text, show_discovery in self.commands:
            if show_discovery:
                yield DiscoveryHit(
                    name,
                    runnable,
                    help=help_text,
                )

    async def search(self, query: str) -> Hits:
        """Handle a request to search for commands that match the query.
        Args:
            query: The user input to be matched.
        Yields:
            Command hits for use in the command palette.
        """
        matcher = self.matcher(query)
        for name, runnable, help_text, _ in self.commands:
            if (match := matcher.match(name)) > 0:
                yield Hit(
                    match,
                    matcher.highlight(name),
                    runnable,
                    help=help_text,
                )

    @property
    def episode_names(self) -> 'episode_names':
        """
        I don't understand what this function does, I cargo culted it
        Or rather, I do understand _what_ it does, but not why.
        Apparently just a typechecking thing?
        """
        return cast('episode_names', self.screen.app)