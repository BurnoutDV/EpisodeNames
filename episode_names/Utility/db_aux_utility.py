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
This contains commands that are not exactly database functions but have something to do
with it. For "now"(tm) this is im & export of data
"""
import json
import logging
from datetime import datetime, date
from json import JSONDecodeError
from pathlib import Path
from platformdirs import user_data_dir

from episode_names.Utility.db import Episode, TextTemplate, Project, Settings, Playlist, normalize_datetime, YtDbPlay, \
    YtDbVid, YtDbNumbering
from episode_names.__init__ import __folder_version__, __previous_db_versions__,__appname__, __appauthor__

def export_to_json(file_path: Path | str = "export.json", categories: list | None = None) -> bool:
    """
    Because only free data is happy is this the export button. It also makes it kinda easy to change the
    database scheme more without losing all data while doing so

    :param file_path: path to the file to write to
    :param categories: ['local', 'remote', 'app']
    :return: bool
    """
    if not categories or (isinstance(categories, list) and len(categories) == 0):
        categories = ['local', 'remote', 'app'] # per default everything is in it
    the_great_export = {}
    # * select raw db objects, no need for DTOs
    # * Projects
    if 'local' in categories:
        projects = {}  # ? maybe it would be better to create this as a list without index?
        res : list[Project] = Project.select()
        for each in res:
            projects[each.id] = {
                'uid': each.id,
                'name': each.name,
                'category': each.category,
                'description': each.description,
                'notes': each.notes,
                'yt_link': each.yt_link,
                'yt_human_touch': each.yt_human_touch,
                'edit_date': each.edit_date.isoformat(),
                'create_date': each.create_date.isoformat()
            }
        the_great_export['Projects'] = projects
    # * %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # * Templates
    if 'local' in categories:
        templates = {}
        res : list[TextTemplate] = TextTemplate.select()
        for each in res:
            each.edit_date = normalize_datetime(each.edit_date)
            each.create_date = normalize_datetime(each.create_date)
            templates[each.id] = {
                'uid': each.id,
                'title': each.title,
                'pattern': each.pattern,
                'tags': each.tags,
                'description_prefix': each.description_prefix,
                'description_suffix': each.description_suffix,
                'description_addon_prefix': each.description_addon_prefix,
                'description_addon_suffix': each.description_addon_suffix,
                'edit_date': each.edit_date.isoformat(),
                'create_date': each.create_date.isoformat()
            }
        the_great_export['Templates'] = templates
    # * %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # * Episodes
    if 'local' in categories:
        episodes = {}
        res : list[Episode] = Episode.select()
        for each in res:
            try:
                episodes[each.id] = {
                    'uid': each.id,
                    'edit_date': each.edit_date.isoformat(),
                    'create_date': each.create_date.isoformat(),
                    'title': each.title,
                    'counter1': each.counter1,
                    'counter2': each.counter2,
                    'extra_counter': each.extra_counter,
                    'record_date': each.record_date.isoformat(),
                    'session': each.session,
                    'description': each.description,
                    'desc_addon': each.desc_addon,
                    'notes': each.notes,
                    'yt_link': each.yt_link,
                    'yt_human_touch': each.yt_human_touch,
                    'template': each.template_id,
                    'project': each.project_id
                }
            except e:  # Yeah, yeah I know
                logging.error(f"Exception: {e}")
                return False
        the_great_export['Episodes'] = episodes
    # * %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # * Youtube Playlists
    if 'remote' in categories:
        yt_playlists = {}
        res : list[YtDbPlay] = YtDbPlay.select()
        for each in res:
            try:
                yt_playlists[each.yt_id] = {
                    'yt_id': each.yt_id,
                    'template_id': each.template_id,
                    'title': each.title,
                    'description': each.description,
                    'entries': each.entries,
                    'publish_date': each.publish_date.isoformat() if each.publish_date else None,
                    'edit_date': each.edit_date.isoformat(),
                    'create_date': each.create_date.isoformat()
                }
            except Exception as e:
                logging.error(f"Exception: {e}")
                return False
        the_great_export['YtDbPlay'] = yt_playlists
    # * %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # * Youtube Videos
    if 'remote' in categories:
        yt_videos = {}
        try:
            res: list[YtDbVid] = YtDbVid.select()
            for each in res:
                yt_videos[each.yt_id] = {
                    'yt_id': each.yt_id,
                    'template_id': each.template_id,
                    'title': each.title,
                    'description': each.description,
                    'views': each.views,
                    'upload_date': each.upload_date.isoformat() if each.upload_date else None,
                    'publish_date': each.publish_date.isoformat() if each.publish_date else None,
                    'last_update': each.last_update.isoformat() if each.last_update else None,
                    'last_full_update': each.last_full_update.isoformat() if each.last_full_update else None,
                    'edit_date': each.edit_date.isoformat(),
                    'create_date': each.create_date.isoformat()
                }
        except Exception as e:
            logging.error(f"Exception: {e}")
            return False
        the_great_export['YtDbVid'] = yt_videos
    # * %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # * Playlist Numbering
    # * %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    if 'remote' in categories:
        yt_play_vid_link = [] # ids don't have meaning for this one
        try:
            res: list[YtDbNumbering] = YtDbNumbering.select()
            for each in res:
                yt_play_vid_link.append({
                    'video': each.video_id,
                    'playlist': each.playlist_id,
                    'position': each.position
                })
        except Exception as e:
            logging.error(f"Exception: {e}")
            return False
        the_great_export['YtDbNumbering'] = yt_play_vid_link
    # * Settings
    if 'app' in categories:
        all_settings = {}
        res = Settings.select()
        for each in res:
            if each.key == "db_version":
                continue
            try:
                all_settings[each.id] = {
                    'uid': each.id,
                    'key': each.key,
                    'value': each.value
                }
            except Exception as e:
                logging.error(f"Exception: {e}")
                return False
        the_great_export['Settings'] = all_settings
    the_great_export['__version'] = __folder_version__
    with open(file_path, "w") as json_export_file:
        json.dump(the_great_export, json_export_file, indent=2)
    logging.info(f"Exportet to {file_path}")
    return True

def import_from_json(file_path: Path | str) -> int:
    # TODO: merge with old data by project_name
    # TODO: backup current data temporarily
    with open(file_path, "r") as json_import:
        try:
            raw_data = json.load(json_import)
        except JSONDecodeError as e:
            logging.error(f"JSON import error: {e}")
            return -1
        # * check for proper json format
        # * actually check for the export UIDs being correct to?
        # ? maybe use json scheme for that? maybe overkill to see if 4 keys are present
    count = 0
    new_projects = {} # I could modify the raw_data, this is just a dictionary new & old id
    for proj in raw_data['Projects'].values(): # ? in theory this could be empty ..but whats the point then
        if not 'uid' in proj:
            continue
        new_id = Project.create_raw(
            title=proj['name'],
            category=proj.get('category', 'default'),
            description=proj.get('description', ''),
            notes=proj.get('notes', None),
            yt_link=proj.get('yt_link', None),
            yt_human_touch=proj.get('yt_human_touch', None),
            edit_date=proj.get('edit_date', None),
            create_date=proj.get('create_date', None)
        )
        new_projects[proj['uid']] = new_id
        count+= 1
    new_templates = {}
    for tpl in raw_data['Templates'].values():
        if not 'uid' in tpl:
            continue # this seems like a pointless protection against nothing
        new_id = TextTemplate.create_raw(
            title=tpl['title'],
            pattern=tpl.get('pattern', ''),
            tags=tpl.get('tags', ''),
            description_prefix=tpl.get('description_prefix', '\\n'),
            description_suffix=tpl.get('description_suffix', '\\n'),
            description_addon_prefix=tpl.get('description_addon_prefix', '\\n'),
            description_addon_suffix=tpl.get('description_addon_suffix', '\\n'),
            edit_date=tpl.get('edit_date', None),
            create_date=tpl.get('create_date', None)
        )
        new_templates[tpl['uid']] = new_id
        count+= 1
    for epi in raw_data['Episodes'].values():
        if not 'uid' in epi:
            continue
        res = Episode.create_raw(
            title=epi['title'],
            counter1=epi.get('counter1', 1),
            counter2=epi.get('counter2', 0),
            extra_counter=epi.get('extra_counter', None),
            record_date=epi.get('record_date', date.today()),
            session=epi.get('session', ''),
            description=epi.get('description', ''),
            desc_addon=epi.get('desc_addon', ''),
            notes=epi.get('notes', ''),
            yt_link=proj.get('yt_link', None),
            yt_human_touch=proj.get('yt_human_touch', None),
            template_id=new_templates[epi['template']],
            project_id=new_projects[epi['project']],
            edit_date=epi.get('edit_date', None),
            create_date=epi.get('create_date', None)
        )
        count+= 1
    # * Yt Db Data, those come with an external id so we dont need to remap things
    if 'YtDbPlay' in raw_data and 'YtDbVid' in raw_data:
        for yt_play in raw_data['YtDbPlay'].values():
            YtDbPlay.update_or_create_raw(
                yt_id=yt_play['yt_id'],
                project_id=yt_play.get('project_id', None),
                title=yt_play['title'],
                description=yt_play.get('description', None),
                entries=yt_play.get('entries', 0),
                publish_date=yt_play.get('publish_date', None),
                edit_date=yt_play.get('edit_date', None),
                create_date=yt_play.get('create_date', None),
            )
        for yt_vid in raw_data['YtDbVid'].values():
            YtDbVid.update_or_create_raw(
                yt_id=yt_vid['yt_id'],
                template_id=yt_vid.get('template_id', None),
                title=yt_vid['title'],
                description=yt_vid.get('description', None),
                views=yt_vid.get('views', None),
                publish_date=yt_vid.get('publish_date', None),
                upload_date=yt_vid.get('upload_date', None),
                last_update=yt_vid.get('last_update', None),
                last_full_update=yt_vid.get('last_full_update', None),
                edit_date=yt_vid.get('edit_date', None),
                create_date=yt_vid.get('create_date', None),
            )
    # * Settings exist since v0.2.3
    if 'Settings' in raw_data:
        for setti in raw_data['Settings'].values():
            if not 'uid' in setti:
                continue
            # no date, so no need for create_raw
            res = Settings.update_or_set_key(
                setti.get('key'),
                setti.get('value')
            )
            count+= 1
    return count

    #delete old data
    #create new data
    #generate new ids

def purge_all_user_data(sure=False) -> bool:
    """
    Deletes all content that is not settings

    :param bool sure: if you are not sure, nothing happens
    :return: bool
    """
    if not sure: # this is silly, I know
        return False
    Project.delete().execute()
    Episode.delete().execute()
    TextTemplate.delete().execute()
    return True

def previous_versions() -> list:
    """
    Checks if there are database files present from previos iterations of the database
    scheme.
    :return: list of other databases that once where
    """
    confirmed_old = []
    for old_version in __previous_db_versions__:
        user_dir = user_data_dir(__appname__, __appauthor__, version=old_version)

        if Path(user_dir).is_dir() and Path(user_dir).glob("*.db"):
            confirmed_old.append(old_version)
    # ? I had the thought of giving the filesize of each db file back..but honestly, this seems
    # ? like unecessary work because I then need average init file size for each db revision
    return confirmed_old