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
from episode_names.Utility import i18n, find_related_project, wlen, use_template_as_reverse_extractor, \
    get_tree_node_with_data
from episode_names.Utility.custom_widgets import EnPageMarker
from episode_names.Utility.db import Settings, YtPlaylist, YtDbPlay, YtDbVid, YtVideo, TextTemplate, Episode, Folge
from episode_names.Utility.db_operations import PatternTemplate
from episode_names.Utility.youtube_api_calls import get_channel_playlists, get_all_playlists_videos
from episode_names.Modals import LinkVideoModal

class LinkingScreen(Screen):
    BINDINGS = [
        Binding(key="ctrl+g", action="fetch_playlists", description=i18n['DL Playlist']),
        Binding(key="ctrl+u", action="fetch_playlist_videos", description=i18n['DL Videos']),
        Binding(key="ctrl+k", action="assign_project", description=i18n['Assign Project']),
        Binding(key="ctrl+l", action="assign_template", description=i18n['Assign Episode Template']),
        Binding(key="a", action="link_episode", description=i18n['Link Episode']),
        Binding(key="m", action="link_episode_batch", description=i18n['Episode Batch Linking']),
        Binding(key="o", action="debug_pl_data", description="debug: playlist data"),
    ]
    CSS_PATH = "../CSS/LinkingScreen.tcss"

    YT_TITLE_REGEX_DEFAULT = " - Lets Play"

    def __init__(self):
        # TODO: regex helper interface modal bla
        # TODO: bulk mode with automatic follow up
        # TODO: bulk assign in one go modal
        # TODO: proper fetch interface, update fetch
        self.title_regex: str | None = LinkingScreen.YT_TITLE_REGEX_DEFAULT
        self.api_key: str | None = None
        self.channel_id: str | None = None
        self.datetimeformat = Settings.save_retrieve_key("datetimeformat", "%d.%m.%Y %H:%M:%S.%f")
        self.current_playlist: str | None = None # only the ID, not the whole object

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

        playlists_data: list[YtPlaylist] = YtDbPlay.get_all_from_db()
        self.uti_playlist_tree_fill(playlists_data)


    def uti_playlist_tree_fill(self, playlists_data: list[YtPlaylist]):
        self.playlists.focus()
        self.playlists.show_root = False
        self.playlists.show_guides = False
        # self.videos.disabled = True
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

    def _select_video_dataview(self) -> YtVideo | None:
        """
        Boiler Plate Handler to get the currently selected line in the
        datatable
        :return:
        """
        row_key, column_key = self.videos.coordinate_to_cell_key(self.videos.cursor_coordinate)
        if not row_key:
            return None
        this = YtVideo.from_yt_db_vid(YtDbVid.get_by_id(row_key.value))
        if not this:
            return  None
        return this

    def populate_video_view(self, playlist):
        # fetch from db if available
        self.current_playlist = playlist
        videos: list[YtVideo] = YtDbPlay.get_playlist_videos(playlist)
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
                    str(item.pl_pos+1),
                    item.title,
                    f'{i18n.t('combo_words', {'%%number%%': wlen(item.description)})}',
                    item.views if item.views else 0,
                    item.upload_date.strftime(self.datetimeformat),
                    item.publish_date.strftime(self.datetimeformat)
                ],
                key=item.yt_id
            )

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

    def action_fetch_playlist_videos(self):
        if not self.current_playlist:
            return
        vids = get_all_playlists_videos(self.current_playlist, self.api_key, complex_response=True)
        if not isinstance(vids, list):
            if isinstance(vids, int):
                self.app.notify(i18n.t('req_error_code', [str(vids)]))
            self.app.write_raw_log(vids)
            return
        YtDbPlay.assign_videos(self.current_playlist, vids)
        playlists_data: list[YtPlaylist] = YtDbPlay.get_all_from_db()
        self.uti_playlist_tree_fill(playlists_data)
        self.playlists.select_node(get_tree_node_with_data(self.playlists, self.current_playlist, 'yt_id'))

        self.app.notify(i18n[f'Fetched {len(vids)} Videos']) # TODO: makes this dynamic i18n

    def action_fetch_playlists(self):
        playlists = get_channel_playlists(self.channel_id, self.api_key, complex_response=True)
        if isinstance(playlists, list):
            for each in playlists:
                YtDbPlay.update_or_create(each)
        else:
            self.app.write_raw_log(playlists)

    def action_link_episode(self):
        """
        Links a video to an episode so the description and title can be copied into a pure
        data based episode for archiving purpose.
        :return:
        """
        # check if episode itself got a template
        a_video = self._select_video_dataview()
        a_playlist = YtPlaylist.from_yt_db_play(YtDbPlay.get_by_id(self.current_playlist))
        if not a_video:
            return
        if not a_video.template_id: # try to get it from the playlist
            if not a_playlist.project_id:
                self.app.notify(i18n['No assigned project found'], severity="error")
                return
            # ! projects dont have templates, so we now, just like that, select
            # ! a random episode, probably the first, and take the template for that
            # ! one..this might work often, but not always, refactoring needed
            # TODO: make this another modal/or quick action to select first if only one
            random_template_id = (Episode.
                                  select(Episode.template_id).
                                  where(Episode.project_id == a_playlist.project_id)
                                  .get())
            template_id = random_template_id.template_id
        else:
            template_id = a_video.template_id
        ptemplate = TextTemplate.as_PTemplate_by_uid(template_id)
        if not ptemplate:
            self.app.notify(i18n['Assigned template does not exist in Database'], severity="error")
            return
        a_folge: Folge = use_template_as_reverse_extractor(a_video, ptemplate)
        if not a_folge:
            self.app.notify(i18n['Couldnt reverse templating'], severity="warning")
            return
        if a_playlist.project_id: # enrichment
            a_folge.db_project = a_playlist.project_id
        # this temporary a_folge provides a convinient field to carry the yt-id further
        a_folge.yt_link = a_video.yt_id
        # TODO: give option to debug here
        def handle_callback(link_folge: Folge or None):
            if not link_folge:
                return
            if isinstance(link_folge, Folge):
                Episode.update_or_create(link_folge)
                # TODO: [far future] you have to update DataView on F1 View..theoretically...

        self.app.push_screen(LinkVideoModal(a_folge), handle_callback)

    def action_link_episode_batch(self):
        """
        Creation notices, a dialoge modal that has some options in the top and buttons in the bottom,
        middle shows the current video and then goes applies the linking with one key/button
        but offers the possiblity to edit if something is amiss. Then, instead of closing the next,
        non linked video is shown. In an ideal world most of the work is just visually confirming
        that everything is fine and then continuing and only outlayers need a human hand
        :return:
        """
        pass

    def action_assign_project(self):
        temp = YtPlaylist.from_yt_db_play(YtDbPlay.get_by_id(self.current_playlist))
        def select_callback(project: int or None):
            if not project:
                return
            temp.project_id = project
            YtDbPlay.update_or_create(temp)
            self.app.notify(i18n['Playlist Updated']) # TODO: placeholder i18n here
        self.app.push_screen(LinkPlaylistModal(temp), select_callback)
