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

from textual import on, events, work
from textual.app import ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, ListView, DataTable, Footer, Tree, TabbedContent, TabPane, MarkdownViewer, TextArea
from textual.screen import Screen

import json

from episode_names.Modals.DialogueModals import YesNoBox
from episode_names.Modals.LinkingModals import LinkPlaylistModal
from episode_names.Utility import i18n
from episode_names.Utility.custom_widgets import EnPageMarker
from episode_names.Utility.db import Settings, YtPlaylist, YtDbPlay, YtDbVid, YtVideo
from episode_names.Utility.youtube_api_calls import get_channel_playlists, get_all_playlists_videos
from episode_names.Utility.recommend import find_related_project, wlen
from episode_names.Modals import LinkVideoModal

class LinkingScreen(Screen):
    BINDINGS = [
        Binding(key="ctrl+g", action="fetch_playlists", description=i18n['DL Playlist']),
        Binding(key="ctrl+p", action="show_modal", description="debug: modal"),
        Binding(key="o", action="debug_pl_data", description="debug: playlist data"),
    ]
    CSS_PATH = "../CSS/LinkingScreen.tcss"

    YT_TITLE_REGEX_DEFAULT = " - Lets Play"

    def __init__(self):
        self.title_regex: str | None = LinkingScreen.YT_TITLE_REGEX_DEFAULT
        self.api_key: str | None = None
        self.channel_id: str | None = None
        self.datetimeformat = Settings.save_retrieve_key("datetimeformat", "%d.%m.%Y %H:%M:%S.%f")

        super().__init__()

    def compose(self) -> ComposeResult:
        self.playlists = Tree(label="Label", id='playlists')
        self.videos = DataTable()
        yield EnPageMarker("f3")
        with Vertical(id="no_go_blocker"):
            yield MarkdownViewer("Walls of text", show_table_of_contents=False, id="md_no_go")
        with Vertical(id="main_vert"):
            yield Label("Channel: bla false", id="top_label")
            with Horizontal(id="main_divider"):
                yield self.playlists
                yield self.videos
        yield Footer()

    def _on_mount(self) -> None:
        # retrieve playlist regex rules (more than one)?
        settings = Settings.get_keys(['youtube_api_key', 'youtube_channel_id', 'yt_title_regex'])
        if 'youtube_api_key' in settings and 'youtube_channel_id' in settings:
            self.query_exactly_one("#no_go_blocker").remove()
        else:
            text = i18n['missing_settings_general']
            if not 'youtube_api_key' in settings:
                text += i18n['missing_yt_api']
            if not 'youtube_channel_id' in settings:
                text += i18n['missing_channel_id']
            text += i18n['missing_settings_tail']
            self.query_exactly_one("#md_no_go").document.update(text)
        self.api_key = settings['youtube_api_key']
        self.channel_id = settings['youtube_channel_id']
        if not 'yt_title_regex' in settings:
            Settings.update_or_set_key('yt_title_regex', LinkingScreen.YT_TITLE_REGEX_DEFAULT)
        # mock up
        playlists_data: list[YtPlaylist] = YtDbPlay.get_all_from_db()
        self.playlists.focus()
        self.playlists.show_root = False
        self.playlists.show_guides = False
        #self.videos.disabled = True

        self.playlists.root.expand()
        if playlists_data:
            for each in playlists_data:
                title = f"{each.title} [{each.entries}]"
                self.playlists.root.add_leaf(title, data={'yt_id': each.yt_id})

    @on(Tree.NodeSelected, "#playlists")
    def _select_playlist(self, message: Tree.NodeSelected):
        if not message.node.data:
            return False
        if not message.node.data['yt_id']:
            return False
        projects = find_related_project(message.node.data['yt_id'], additional_bad_words=["Let's", "Play"])
        temp: YtDbPlay = YtDbPlay.get_by_id(message.node.data['yt_id'])
        self.app.push_screen(LinkPlaylistModal(temp))
        self.app.write_raw_log(projects)
        if projects:
            projects = ", ".join([i['name'] for i in projects.values()])
            self.query_exactly_one("#top_label").content = projects
        self.populate_video_view(message.node.data['yt_id'])

    """
    Notes on loading video view from remote:
        1. if video data is there, good. -> END
        2. if not, ask user if they want to download
        3. setup worker in the background to load the data
        4. if the selected Playlist hasnt changed update the view
            when the data becomes available, otherwise dont
            
    What when multiple downloads are at the same time? Do i need a queue?
    """

    def populate_video_view(self, playlist):
        # fetch from db if available
        videos = YtDbPlay.get_playlist_videos(playlist)
        if not videos:
            # fetch data instead
            # TODO: make this async
            async def handle_callback(decision: bool):
                if decision:
                    vids = get_all_playlists_videos(playlist, self.api_key, complex_response=True)
                    if not isinstance(vids, list):
                        if isinstance(vids, int):
                            self.app.notify(i18n.t('req_error_code', [str(vids)]))
                        self.app.write_raw_log(vids)
                        return
                    YtDbPlay.assign_videos(playlist, vids)
            self.app.push_screen(YesNoBox(i18n['Yt_Fetch_YesNo']), handle_callback)
            return

        # TODO: display all header data here but give options to reorder
        self.videos.clear(columns=True)
        self.videos.show_header = True
        self.videos.add_column("#", key="position")
        self.videos.add_column("title", key="title")
        self.videos.add_column("len(Desc)", key="description_len")
        self.videos.add_column("views", key="views")
        self.videos.add_column("upload_date", key="upload_date")
        self.videos.add_column("publish_date", key="publish_date")
        #fill in all
        for item in videos:
            self.videos.add_row(
                *[
                    str(item.pl_pos),
                    item.title,
                    f'{i18n.t('combo_words', {'%%number%%': wlen(item.description)})}',
                    item.views if item.views else 0,
                    item.upload_date.strftime(self.datetimeformat),
                    item.publish_date.strftime(self.datetimeformat)
                ]
            )

    def action_show_modal(self):
        one_vid = YtVideo.from_yt_db_vid(YtDbVid.get_by_id("NvaA8IafS9s"))
        self.app.push_screen(LinkVideoModal(one_vid))

    def action_debug_pl_data(self):
        thetree : Tree = self.query_exactly_one("#playlists")
        current = thetree.cursor_node
        if not current.data:
            self.app.write_log("F4: ALT+Q: No current data")
            return None
        if not current.data['yt_id']:
            self.app.write_raw_log(current.data, "F4: ALT+Q")
            return None
        self.app.write_raw_log(YtPlaylist.from_yt_db_play(YtDbPlay.get_by_id(current.data['yt_id'])))

    def action_fetch_playlists(self):
        API_KEY = "AIzaSyBCQUtyg54u5uzjqxt33bpPr4wbCK1ImAA"
        CHANNEL = "UCU3N3MrZThrI9OMBarMPu3A"
        playlists = get_channel_playlists(CHANNEL, API_KEY, complex_response=True)
        if isinstance(playlists, list):
            for each in playlists:
                YtDbPlay.update_or_create(each)
        else:
            self.app.write_raw_log(playlists)

