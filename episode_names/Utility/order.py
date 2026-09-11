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

import copy
import os
import re
import json

from textual.widgets import Tree

from pathlib import Path
from platformdirs import user_data_dir
from datetime import date

from textual.widgets._tree import TreeNode, TreeDataType

from episode_names.Utility.db import init_db, Project, Playlist, Episode, Folge, TextTemplate, PatternTemplate

def new_episode(previous: Folge,
                new_session=None,
                new_description=None,
                reset_counter2=False,
                new_title=""):
    """
    Creates a new episode and increments the internal counter
    :param previous:
    :param str new_session:
    :param str new_description:
        :param str new_title:
    :return:
    """
    current = copy.copy(previous)
    current.db_uid = -1
    if current.counter2 > 0:
        current.counter2 += 1
    if reset_counter2:
        current.counter2 = 1
    current.counter1 += 1
    current.title = new_title
    if new_session:
        current.session = new_session
    if new_description:
        current.description = new_description
    return current

def multisub(subs, subject):
    """
    Simultaneously perform all substitutions on the subject string.
    """
    # https://stackoverflow.com/a/765835
    pattern = '|'.join('(%s)' % re.escape(p) for p, s in subs)
    substs = [s for p, s in subs]
    replace = lambda m: substs[m.lastindex - 1]
    return re.sub(pattern, replace, subject)

def create_description_text(this: Folge,
                            date_format: str = "%d.%m.%Y",
                            override: PatternTemplate | None = None) -> str or None:
    """

    TODO: make this more efficient.

    :param override: You can set your own TextTemplate that is to be used instead
    :param date_format: DATE, not *datetime* Format for release_date field
    :param this: Folge class, not an *Episode* difference, although in doesnt matter here
    :return: str
    """

    def temporary_real_escape(temple: PatternTemplate) -> PatternTemplate:
        """
        I like to have the escape sequences in plain text in the database,
        but for them to actually work we need them in their true form, this
        makes that possible. Boilerplate inc.
        :return: PatternTemplate enriched Template
        """
        attributes = ['description_prefix', 'description_suffix',
                      'description_addon_prefix', 'description_addon_suffix']
        # * yes this is hack, I don't feel any remorse
        for each in attributes:
            temp = multisub([
                (r'\n', '\n'),
                (r'\t', '\t'),
                (r'\r', '\r'),
            ],
            temple.__getattribute__(each))
            temple.__setattr__(each, temp)
        return temple

    if not this.db_template:
        return None

    if override:
        text = override
    else:
        text = TextTemplate.as_PTemplate_by_uid(this.db_template)
        if not text:
            return None # If no template is assigned

    text = temporary_real_escape(text)
    # ? prep step for suffix & prefix of description stuff
    if this.description.strip():
        this.description = (text.description_prefix +
                            this.description +
                            text.description_suffix)
    if this.desc_addon.strip():
        this.desc_addon = (text.description_addon_prefix +
                            this.desc_addon +
                            text.description_addon_suffix)

    return multisub([
        ("$$counter1$$", str(this.counter1)),
        ("$$counter2$$", str(this.counter2)),
        ("$$session$$", this.session),
        ("$$desc_addon$$", this.desc_addon),
        ("$$description$$", this.description),
        ("$$record_date$$", this.recording_date.strftime(date_format)), # TODO: make this setting
        ("$$title$$", this.title)
        ], text.pattern)


def get_tree_node_with_data(tree: Tree, value: str | int, *keys) -> TreeNode[TreeDataType] | None:
    """Returns the first node that got a matching value in the json data field
    under the chain of *keys given.
    usage example: Tree.get_node_with_data(42, 'database', 'id')
    Args:
        tree: the actuall tree widget, this is supposed to be part of the Tree Widget, see PullReq 5362
        value: str|int of the desired data in the data json
        *keys: chain of keys to the nested value
    Returns:
        The first Node with the desired value or None
    """
    for treeline in tree._tree_lines:
        if treeline.node.data:
            data = treeline.node.data
            try:
                for key in keys:
                    data = data[key]
                if data == value:
                    return treeline.node
            except(KeyError, TypeError):
                continue
    return None  # if nothing was found

def user_setup(name, author, version) -> None:
    """
    Handles all the annoying details of config files in the user folder

    :param name: see platformdirs.user_data_dir, this uses that
    :param author: _see platformdirs.user_data_dir, this uses that_
    :param version: _see platformdirs.user_data_dir, this uses that_
    :return: Nothing, but it initiates the database
    """
    user_dir = user_data_dir(name, author, version=version)
    if not Path(user_dir).is_dir():
        Path(user_dir).mkdir(parents=True, exist_ok=True)
    os.chdir(user_dir)
    # originally I wanted to be fancy and use toml or yaml, but json is sufficient
    default_config = Path(user_dir) / "config.json"
    if not default_config.is_file():
        try:
            with open(default_config, "w") as config_file:
                default_conf_dict = {
                    'db_path': 'episode_names.db',
                    'relative_user_folder': True,
                    'absolute_db_path': ""
                }
                json.dump(default_conf_dict, config_file, indent=2)
                config = default_conf_dict
        except (FileNotFoundError, PermissionError, OSError):
            print("Cannot get write in homefolder, this is rather bad. Aborting")
            exit(1)  # General Error
    else:
        try:
            with open(default_config, "r") as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, PermissionError, OSError):
            print("Cannot get read on homefolder, this is pretty bad. Aborting")
            exit(1) # Major Error
    if config['relative_user_folder']: # default loading .local folder
        db_path = Path(user_dir) / config['db_path']
    else:
        db_path = Path(config['absolute_db_path'])
    if db_path.is_file():
        init_db(db_path) # * ~home/.local/share/episode_names/[ver]
    else: # create new db file
        init_db(db_path, creation=True)