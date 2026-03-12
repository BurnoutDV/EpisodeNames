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

from episode_names.Utility.db import Episode, TextTemplate, Project, Settings, Playlist, normalize_datetime
from episode_names.__init__ import __folder_version__, __previous_db_versions__,__appname__, __appauthor__

def export_to_json(file_path: Path | str = "export.json") -> bool:
    """
    Because only free data is happy is this the export button. It also makes it kinda easy to change the
    database scheme more without losing all data while doing so

    :param file_path: path to the file to write to
    :return: bool
    """
    the_great_export = {}
    # * select raw db objects, no need for DTOs
    # * Projects
    projects = {}  # ? maybe it would be better to create this as a list without index?
    res = Project.select()
    for each in res:
        projects[each.id] = {
            'uid': each.id,
            'name': each.name,
            'category': each.category,
            'description': each.description,
            'notes': each.notes,
            'yt_link': each.yt_link,
            'yt_title': each.yt_title,
            'yt_desc': each.yt_desc,
            'yt_last_link': each.yt_last_link,
            'edit_date': each.edit_date.isoformat(),
            'create_date': each.create_date.isoformat()
        }
    the_great_export['Projects'] = projects
    # * %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # * Templates
    templates = {}
    res = TextTemplate.select()
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
    episodes = {}
    res = Episode.select()
    for each in res:
        try:
            episodes[each.id] = {
                'uid': each.id,
                'edit_date': each.edit_date.isoformat(),
                'create_date': each.create_date.isoformat(),
                'title': each.title,
                'counter1': each.counter1,
                'counter2': each.counter2,
                'record_date': each.record_date.isoformat(),
                'session': each.session,
                'description': each.description,
                'desc_addon': each.desc_addon,
                'notes': each.notes,
                'yt_link': each.yt_link,
                'yt_title': each.yt_title,
                'yt_desc': each.yt_desc,
                'yt_last_link': each.yt_last_link,
                'template': each.template_id,
                'project': each.project_id
            }
        except e:  # Yeah, yeah I know
            logging.error(f"Exception: {e}")
            return False
    the_great_export['Episodes'] = episodes
    # * %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # * Settings
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
        except e:
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
            yt_title=proj.get('yt_title', None),
            yt_desc=proj.get('yt_desc', None),
            yt_last_link=proj.get('yt_last_link', None),
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
            record_date=epi.get('record_date', date.today()),
            session=epi.get('session', ''),
            description=epi.get('description', ''),
            desc_addon=epi.get('desc_addon', ''),
            notes=epi.get('notes', ''),
            yt_link=proj.get('yt_link', None),
            yt_title=proj.get('yt_title', None),
            yt_desc=proj.get('yt_desc', None),
            yt_last_link=proj.get('yt_last_link', None),
            template_id=new_templates[epi['template']],
            project_id=new_projects[epi['project']],
            edit_date=epi.get('edit_date', None),
            create_date=epi.get('create_date', None)
        )
        count+= 1
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