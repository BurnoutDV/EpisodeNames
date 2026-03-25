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

"""
A word about database relations:
I am absolutly aware that one video on youtube can be in many playlists at the same time,
but for the scope of this tool we are only handling videos that are in one playlist and only
those videos, otherwise I had to handle a many to many relationship and deduplicate data. If,
for some reason there are multiple playlists that contain the same videos that are linked in
episode_names, each instance of the linked video will be its own database entry as the yt_id
is not the primary key
"""

import requests
from datetime import datetime

from episode_names.Utility.db import YtVideo, YtPlaylist, normalize_datetime

def get_all_playlists_videos(playlist_id: str,
                            api_key: str,
                            paging: str | None = None,
                            complex_response=False) -> YtVideo | None | bool | int:
    """
    Requests

    :param channel_id:
    :param api_key:
    :param complex_response:
    :return: None if something goes wrong, else object
    **IF complex_response is True**:
    *True* if request through but not malformed json, *False* if keys missing,
    *[int]* if non-200 Code

    """
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    payload = {
        'part': 'snippet,contentDetails',
        'playlistId': playlist_id,
        'maxResults': 50,
        'key': api_key
    }
    if paging:
        payload['pageToken'] = paging
    playlist_page = requests.get(base_url, params=payload)
    if playlist_page.status_code == requests.codes.ok:
        try:
            data = playlist_page.json()
        except requests.exceptions.JSONDecodeError:
            return True if complex_response else None
    else:
        return playlist_page.status_code if complex_response else None
    check_keys = ['kind', 'items']
    # ? all those json integrity checks are breaking me
    # * yes I know that json schema is a thing
    if data['kind'] != "youtube#playlistItemListResponse":
        return False if complex_response else None # ? dont think that can happen
    if set(check_keys) - data.keys():
        return False if complex_response else None
    next_page = data.get('nextPageToken', False)
    # Playlist items::::
    item_check_key = ['kind', 'snippet', 'contentDetails']
    snipped_check = ['publishedAt', 'title', 'description', 'position']
    video_lst = []
    for item in data['items']:
        if set(item_check_key) - item.keys():
            continue # TODO: some logging here Alan
        if set(snipped_check) - item['snippet'].keys():
            continue
        if item['kind'] != "youtube#playlistItem":
            continue
        one_video = YtVideo(
            yt_id=item['contentDetails'].get('videoId', None),
            title=item['snippet'].get('title', ""),
            description=item['snippet'].get('description', ""),
            upload_date=normalize_datetime(item['snippet'].get('publishedAt', None)),
            publish_date=normalize_datetime(item['contentDetails'].get('videoPublishedAt', None)),
            last_update=datetime.now(),
            playlist=item['snippet'].get('playlistId', ""),
            pl_pos=item['snippet'].get('position', ""),
            views=None # ? we actually dont get this here
        )
        if one_video.yt_id: # * I am quite sure this cannot not happen either
            video_lst.append(one_video)
    if next_page: # more than one page in result set
        more_videos = get_all_playlists_videos(playlist_id, api_key, paging=next_page)
        if more_videos:
            video_lst = video_lst + more_videos
    return video_lst

def get_channel_playlists(channel_id: str, api_key: str, next_page=False, complex_response=False):
    base_url = "https://www.googleapis.com/youtube/v3/playlists"
    payload = {
        'part': 'snippet,contentDetails',
        'channelId': channel_id,
        'maxResults': 50,
        'key': api_key
    }
    if next_page:
        payload['pageToken'] = next_page
    playlist_list = requests.get(base_url, params=payload)
    if playlist_list.status_code == requests.codes.ok:
        try:
            data = playlist_list.json()
        except requests.exceptions.JSONDecodeError:
            return True if complex_response else None
    else:
        print(playlist_list.content)
        return playlist_list.status_code if complex_response else None
    check_keys = ['kind', 'items']
    # ? all those json integrity checks are breaking me
    # * yes I know that json schema is a thing
    if data['kind'] != "youtube#playlistListResponse":
        return False if complex_response else None # ? dont think that can happen
    if set(check_keys) - data.keys():
        return False if complex_response else None
    next_page = data.get('nextPageToken', False)
    item_check_key = ['kind', 'snippet', 'contentDetails', 'id']
    snipped_check = ['publishedAt', 'title', 'description']
    playlist_lst = []
    for item in data['items']:
        if set(item_check_key) - item.keys():
            continue  # TODO: some more logging here Alan
        if set(snipped_check) - item['snippet'].keys():
            continue
        if item['kind'] != "youtube#playlist":
            continue
        one_playlist = YtPlaylist(
            yt_id=item['id'],
            title=item['snippet'].get('title', ""),
            description=item['snippet'].get('description', ""),
            publish_date=normalize_datetime(item['snippet'].get('publishedAt', None)),
            last_update=datetime.now(),
            entries=item['contentDetails'].get('itemCount', None)
        )
        if one_playlist.yt_id:  # * I am quite sure this cannot not happen either
            playlist_lst.append(one_playlist)
    if next_page:  # more than one page in result set
        more_playlists = get_channel_playlists(channel_id, api_key, next_page=next_page)
        if more_playlists:
            playlist_lst = playlist_lst + more_playlists
    return playlist_lst

def get_one_video_detail():
    pass

if __name__ == "__main__":
    print("This is part of episode_names and not supposed to be run on its own")
    print("Although..you might be able..add some simple cli interface here alan")
    exit(0)
    many_videos = get_all_playlists_pages("", "", complex_response=True)
    many_playlists = get_channel_playlists("", "", complex_response=True)
    if not many_playlists:
        print(many_playlists)
    for each in many_playlists:
        print(each)

