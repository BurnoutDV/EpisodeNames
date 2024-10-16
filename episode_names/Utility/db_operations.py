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

from dataclasses import dataclass
from datetime import datetime, date

from episode_names.Utility.db import Episode, TextTemplate, Project

@dataclass
class Folge:
    title: str
    db_uid: int = -1 # objects can exists without db connection
    db_project: int = -1
    db_template: int = -1
    counter1: int = 1
    counter2: int = 0
    session: str = ""
    description: str = ""
    recording_date: date = date.today()

    def __str__(self):
        if self.counter2 > 0:
            return f"{self.title} #{self.counter1}##{self.counter2} - {self.session} [desc:{len(self.description)}]"
        return f"{self.title} #{self.counter1} - {self.session} [desc:{len(self.description)}]"

    @staticmethod
    def from_episode(this: Episode):
        return Folge(
            title=this.title,
            db_uid=this.id,
            db_project=this.project_id,
            db_template=this.template_id,
            counter1=this.counter1,
            counter2=this.counter2,
            session=this.session,
            description=this.description,
            recording_date=this.record_date,
        )

@dataclass
class Playlist:
    title: str
    category: str = ""
    description: str = ""
    db_uid: int = -1

    @staticmethod
    def from_project(this: Project):
        return Playlist(
            title=this.name,
            category=this.category,
            description=this.description,
            db_uid=this.id
        )

@dataclass
class PatternTemplate:
    title: str
    insert_here: str = ""
    db_uid: int = -1

def update_or_create_template(object: PatternTemplate) -> int:
    if object.db_uid <= 0:
        return create_template(object)
    res = (TextTemplate
           .update(
            title = object.title,
            insert_here = object.insert_here
            )
            .execute())
    return res

def create_template(object: PatternTemplate) -> int:
    res = (TextTemplate
           .insert(
            title = object.title,
            insert_here = object.insert_here
            )
           .execute())
    return res

def update_or_create_project(object: Playlist) -> int:
    if object.db_uid <= 0:
        return create_project(object)
    res = (Project.update(
        name = object.title,
        category = object.category,
        description = object.description
    )
   .where(Project.id == object.db_uid)
   .execute())
    return res

def create_project(object: Playlist) -> int:
    res = (Project
        .insert(
        name=object.title,
        category=object.category,
        description=object.description
    )
        .execute())
    return res

def get_all_projects() -> list[Playlist]:
    res = Project.select()
    flood = []
    for each in res:
        flood.append(Playlist.from_project(each))
    return flood

def get_project(p_uid) -> Playlist:
    res = Project.select().where(Project.uid == p_uid)
    return Playlist.from_project(res)

def get_episode(uid) -> Folge:
    res = (Episode.get(Episode.id == uid))
    return Folge.from_episode(res)

def get_project_episodes(project_id) -> list[Folge]:
    res = Episode.select().where(Episode.project_id == project_id)
    qua_water = []
    for each in res:
        qua_water.append(Folge.from_episode(each))
    return qua_water

def update_or_create_episode(this: Folge) -> int:
    """

    :param this:
    :return: uid of the new database entry
    """
    if this.db_uid <= 0:
        return create_episode(this)
    res = (Episode
    .update(
        title=this.title,
        counter1=this.counter1,
        counter2=this.counter2,
        record_date=this.recording_date,
        session=this.session,
        description=this.description,
        template_id=this.db_template,
        project_id=this.db_project,
        edit_date=datetime.now()
    )
    .where(Episode.id == this.db_uid)
    .execute())
    return res

def create_episode(this: Folge):
    res = (Episode.insert(
        title=this.title,
        counter1=this.counter1,
        counter2=this.counter2,
        record_date=this.recording_date,
        session=this.session,
        description=this.description,
        template_id=this.db_template,
        project_id=this.db_project
    ).execute())
    return res
