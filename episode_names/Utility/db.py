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
from typing import Literal

from dataclasses import dataclass
from datetime import datetime, date

from peewee import (
    DatabaseProxy,
    DateTimeField,
    DateField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
    CharField, JOIN,
)

database_proxy = DatabaseProxy()

@dataclass
class Folge:
    title: str
    db_uid: int = -1 # objects can exists without db connection
    db_project: int = 0
    db_template: int = 0
    joined_template_title: str | None = None  # this feels not right
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
    def from_episode(this: 'Episode') -> 'Folge':
        template_title = None
        if int(this.template_id) > 0 and hasattr(this.template, "title"):
            template_title = this.template.title
        return Folge(
            title=this.title,
            db_uid=this.id,
            db_project=this.project_id,
            db_template=this.template_id,
            joined_template_title=template_title,
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
    tags: str = ""
    db_uid: int = -1

    @staticmethod
    def from_project(this: 'Project') -> 'Playlist':
        return Playlist(
            title=this.name,
            category=this.category,
            description=this.description,
            tags=this.tags,
            db_uid=this.id
        )

@dataclass
class PatternTemplate:
    title: str
    pattern: str = ""
    tags: str = ""
    db_uid: int = -1

    @staticmethod
    def from_TextTemplate(this: 'TextTemplate') -> 'PatternTemplate':
        return PatternTemplate(
            title=this.title,
            pattern=this.pattern,
            db_uid=this.id,
            tags=this.tags  # TODO: implement tags database site
        )

class BaseModel(Model):
    class Meta:
        database = database_proxy

class Project(BaseModel):
    name = CharField()
    category = CharField()
    description = TextField()
    tags = TextField()

    edit_date = DateTimeField(default=datetime.now)
    create_date = DateTimeField(default=datetime.now)

    @staticmethod
    def as_Playlist_by_uid(p_uid) -> Playlist:
        try:
            res = Project.get_by_id(p_uid)
            return Playlist.from_project(res)
        except Project.DoesNotExist:
            return None

    @staticmethod
    def dump() -> list[Playlist] or None:
        res = Project.select()
        if len(res) <= 0:
            return None
        flood = []
        for each in res:
            flood.append(Playlist.from_project(each))
        return flood

    @staticmethod
    def update_or_create(this: Playlist) -> int:
        if this.db_uid <= 0:
            return Project.create_new(this)
        res = (Project.update(
                name=this.title,
                category=this.category,
                description=this.description,
                tags=this.tags,
                edit_date=datetime.now
                )
               .where(Project.id == this.db_uid)
               .execute())
        return res

    @staticmethod
    def create_new(this: Playlist) -> int:
        res = (Project
               .insert(
                name=this.title,
                 category=this.category,
                description=this.description,
                tags=this.tags
                )
               .execute())
        return res

    @staticmethod
    def has_counter2(project_id: int) -> bool | None:
        """
        Checks if the given project has any episodes with counter2, should
        always return true or false, even if the project doesn't exists, because
        logically, then the number of entries is zero.

        :param project_id: id of the project
        :return bool: true if there are any entries, otherwise false
        """
        try:
            res = (Episode
                   .select(Episode.id)
                   .where(Episode.project_id == project_id)
                   .where(Episode.counter2 > 0)
                   .limit(1))
            return bool(res.count())
        except Episode.DoesNotExist:  # this should never happen
            return None

class TextTemplate(BaseModel):
    title = CharField()
    pattern = TextField()
    tags = CharField(512)

    edit_date = DateTimeField(default=datetime.now)
    create_date = DateTimeField(default=datetime.now)

    @staticmethod
    def as_PTemplate_by_uid(uid: int) -> PatternTemplate | None:
        try:
            res = TextTemplate.get_by_id(uid)
            return PatternTemplate.from_TextTemplate(res)
        except TextTemplate.DoesNotExist:
            return None

    @staticmethod
    def dump() -> list[PatternTemplate] | None:
        res = TextTemplate.select().where(TextTemplate.id > 0)
        if len(res) <= 0:
            return None
        flood = []
        for each in res:
            flood.append(PatternTemplate.from_TextTemplate(each))
        return flood

    @staticmethod
    def get_next_id() -> int:
        """
        Returns the current, highest id plus one for reasons
        One of those methods that could also be written on the fly but I abstracted them anyways
        :return: the (theoretically) next id
        """
        res = (TextTemplate.
               select(TextTemplate.id).
               order_by(TextTemplate.id.desc()).
               limit(1).
               get())
        return res.id + 1

    @staticmethod
    def update_or_create(this: PatternTemplate) -> int:
        if this.db_uid <= 0:
            return TextTemplate.create_new(this)
        res = (TextTemplate
               .update(
                title=this.title,
                pattern=this.pattern,
                tags=this.tags,
                edit_date = datetime.now()
                )
               .where(TextTemplate.id == this.db_uid)
               .execute())
        return res

    @staticmethod
    def create_new(this: PatternTemplate) -> int:
        res = (TextTemplate
               .insert(
                title=this.title,
                pattern=this.pattern,
                tags=this.tags,
                create_date=datetime.now(),
                edit_date=datetime.now()
                )
               .execute())
        return res

class Episode(BaseModel):
    title = CharField()
    counter1 = IntegerField()
    counter2 = IntegerField()
    record_date = DateField()
    session = CharField()
    description = TextField()

    template = ForeignKeyField(TextTemplate, lazy_load=True)
    project = ForeignKeyField(Project, lazy_load=True)
    edit_date = DateTimeField(default=datetime.now)
    create_date = DateTimeField(default=datetime.now)

    @staticmethod
    def as_Folge_by_uid(uid: int) -> Folge or None:
        try:
            res = Episode.get_by_id(uid)
            return Folge.from_episode(res)
        except Episode.DoesNotExist:
            return None

    @staticmethod
    def by_project(project_id: int, order: Literal['asc', 'desc'] = "asc") -> list[Folge] | None:
        if order == "asc":
            res = (Episode.select().join(TextTemplate, JOIN.LEFT_OUTER)
                   .order_by(Episode.counter1.asc())
                   .where(Episode.project_id == project_id))
        else:
            res = (Episode.select().join(TextTemplate, JOIN.LEFT_OUTER)
                   .order_by(Episode.counter1.desc())
                   .where(Episode.project_id == project_id))
        if len(res) <= 0:
            return None
        qua_water = []
        for each in res:
            qua_water.append(Folge.from_episode(each))
        return qua_water

    @staticmethod
    def get_latest(project_id: int) -> Folge | None:
        """Returns the episode with the highest counter1 among the current project"""
        try:
            res = (Episode
                   .select()
                   .where(Episode.project == project_id)
                   .order_by(Episode.counter1.desc())
                   .limit(1)
                   .get())
            return Folge.from_episode(res)
        except Episode.DoesNotExist:
            return None
    @staticmethod
    def update_or_create(this: Folge) -> int:
        """

        :param this:
        :return: uid of the new database entry
        """
        if this.db_uid <= 0:
            return Episode.create_new(this)
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

    @staticmethod
    def create_new(this: Folge) -> int:
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

class Settings(BaseModel):
        key = TextField()
        value = TextField()

def init_db(db_path="episoden_names.db"):
    """
    Creates a new db or connects to one if the name exists
    :param str db_path: path to database
    :return:
    """
    db = SqliteDatabase(db_path)
    database_proxy.initialize(db)

    db.connect()
    db.create_tables([Episode, Project, TextTemplate, Settings])

if __name__ == "__main__":
    init_db("../../test.db")
