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

import copy
import os
import re
import json

from pathlib import Path
from platformdirs import user_data_dir
from datetime import date
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


def debug_create_template():
    this = """Episode $$counter2$$ des Gold Road DLCs - $$session$$

Let's Play ESO #$$counter1$$ ##$$counter2$$ - $$title$$ [Gold Road]

Mo-Do, So auch Live auf Twitch: https://www.twitch.tv/burnoutdv 17-20 Uhr
Playlist: https://www.youtube.com/playlist?list=PLAFz5ZZJ21wO_nLvLprFRAyxN3YilrARe
Gold Road Playlist: https://www.youtube.com/playlist?list=PLAFz5ZZJ21wN4zSdcr2GqPesmrdQ--7gj
Aufnahme vom $$record_date$$ - #$$counter1$$ - ##$$counter2$$"""
    TextTemplate.insert(pattern=this).execute()

def create_dummy_data():
    p_id = Project.update_or_create(Playlist("Elder Scrolls Online", "default"))
    this = """Episode $$counter2$$ des Gold Road DLCs - $$session$$

Let's Play ESO #$$counter1$$ ##$$counter2$$ - $$title$$ [Gold Road]

Mo-Do, So auch Live auf Twitch: https://www.twitch.tv/burnoutdv 17-20 Uhr
Playlist: https://www.youtube.com/playlist?list=PLAFz5ZZJ21wO_nLvLprFRAyxN3YilrARe
Gold Road Playlist: https://www.youtube.com/playlist?list=PLAFz5ZZJ21wN4zSdcr2GqPesmrdQ--7gj
Aufnahme vom $$record_date$$ - #$$counter1$$ - ##$$counter2$$"""
    TextTemplate.create_new(PatternTemplate("Default", "$$counter1$$ - $$title$$"))
    TextTemplate.update(id = 0).where(TextTemplate.title == "Default").execute()
    # ^this is slightly cursed, but makes sure id=0 is always the default entry
    t_id = TextTemplate.update_or_create(PatternTemplate("ESO-Gold Road", this))
    first = Folge(
        title="Gefangene des Schicksals",
        db_template=t_id,
        db_project=p_id,
        counter1=1924,
        counter2=1,
        session="Sitzung 1",
        description="",
        recording_date=date.fromisoformat("2024-09-09")
    )
    last_id = Episode.create_new(first)
    other_titles = [
        "Mephalas Strang der Geheimnisse",
        "Azuras Laterne",
        "Boethias Klinge",
        "Holomagan-Kloster",
        "Schrein der unweigerlichen Geheimnisse",
        "Ereignisse auf Schienen"
    ]
    for title in other_titles:
        old = Episode.as_Folge_by_uid(last_id)
        new = new_episode(old, new_title=title)
        last_id = Episode.create_new(new)
    # Other Projects, empty
    Project.create_new(Playlist("Elden Ring DLC", "default"))
    Project.create_new(Playlist("Spellforce 3", "default"))
    Project.create_new(Playlist("Viewfinder", "legacy"))
    Project.create_new(Playlist("Outer Wilds", "legacy"))
    Project.create_new(Playlist("Metro Exodus", "legacy"))
    Project.create_new(Playlist("Dragon Age Origins", "disgrace"))
    print("Done with my dastardly task master")

def create_description_text(this: Folge) -> str or None:
    """

    TODO: make this more efficient.

    :param this:
    :return:
    """
    def multisub(subs, subject):
        "Simultaneously perform all substitutions on the subject string."
        # https://stackoverflow.com/a/765835
        pattern = '|'.join('(%s)' % re.escape(p) for p, s in subs)
        substs = [s for p, s in subs]
        replace = lambda m: substs[m.lastindex - 1]
        return re.sub(pattern, replace, subject)

    if not this.db_template:
        return None

    text = TextTemplate.as_PTemplate_by_uid(this.db_template)
    if not text:
        return None # If no template is assigned

    return multisub([
        ("$$counter1$$", str(this.counter1)),
        ("$$counter2$$", str(this.counter2)),
        ("$$session$$", this.session),
        ("$$record_date$$", this.recording_date.strftime("%d.%m.%Y")), # TODO: make this setting
        ("$$title$$", this.title)
        ], text.pattern)

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
        init_db(db_path)
    else: # create new db file and drop dummy data into it
        init_db(db_path)
        create_dummy_data()

if __name__ == "__main__":
    init_db()
    create_dummy_data()
