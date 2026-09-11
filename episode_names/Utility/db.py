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
from typing import Literal

from dataclasses import dataclass
from datetime import datetime, date

import textdistance
from peewee import (
    DatabaseProxy,
    DateTimeField,
    DateField,
    BooleanField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
    CharField, JOIN, fn, SQL
)

from episode_names.__init__ import __folder_version__
database_proxy = DatabaseProxy()

# TODO: find a better place for this
def normalize_datetime(in_date: str | datetime | None = None, default_on_now: bool = False) -> datetime | None:
    """
    Normalizes a given date which is either isoformat string or nothing which then becomes now
    :param default_on_now: if iso format goes wrong, it now is used if this is **True**
    :param in_date: nothing -> now(), str must be isoformat
    :return: a proper datetime or None
    """
    if not in_date:
        in_date = datetime.now()
    if isinstance(in_date, str):  # quite sure this does nothing in terms of sqlite
        in_date = datetime.fromisoformat(in_date)
    if not isinstance(in_date, datetime):
        if default_on_now:
            return datetime.now()
        return None
    return in_date

@dataclass
class Folge:
    title: str
    joined_template_title: str | None = None  # this feels not right
    project_title: str | None = None # hydrated for now only used in linking recommends 2026-05-01
    counter1: int = 1
    counter2: int = 0
    extra_counter: str | None = None #mostly chars like 'b' for 64b
    session: str = ""
    description: str = ""
    desc_addon: str = ""
    notes: str | None = None
    recording_date: date = date.today()

    # * Youtube Connection (or any other video site I guess?)
    yt_link: str | None = None # TODO make this its own database
    yt_human_touch: bool | None = None

    db_uid: int = 0  # objects can exist without db connection
    db_project: int = 0
    db_template: int = 0
    edit_date: datetime | None = datetime.now()
    create_date: datetime | None = datetime.now()

    def __str__(self):
        if self.counter2 > 0:
            return f"#{self.counter1}##{self.counter2} - {self.title} (ses, rec: {self.session if self.session else 'empty'}, {self.recording_date if self.recording_date else 'empty'}) [desc:{len(self.description)}]"
        return f"#{self.counter1} - {self.title} (ses, rec: {self.session if self.session else 'empty'}, {self.recording_date if self.recording_date else 'empty'}) [desc:{len(self.description)}]"

    def __eq__(self, other: 'Folge') -> bool:
        """
        Actually compares only the non-database parts against each other
        :param other Folge: the other Folge to compare to
        :return:
        """
        if not isinstance(other, Folge):
            raise NotImplemented("'other' is not a Folge")
        if (self.title == other.title
            and self.counter1 == other.counter1
            and self.counter2 == other.counter2
            and self.extra_counter == other.extra_counter
            and self.description == other.description
            and self.desc_addon == other.desc_addon
            and self.notes == other.notes
            and self.recording_date == other.recording_date):
            return True
        return False

    @staticmethod
    def copy_overwrite(other: 'Folge', **attributes) -> 'Folge':
        """
        Copies everything from an existing Folge but overwrites the given attributes with the
        new stuff. Used to make sure that all data are retained in forms
        :param other: another Folge
        :param kwargs: all attributes that a Folge can have
        :return: Folge
        :raises: Attribute Error if inexitent attribute is written, Value Error if no FOlge is provided
        """
        if not isinstance(other, Folge):
            raise ValueError(f"Parameter other is not of type 'Folge', got '{other.__class__.__name__}' instead")
            # TypeSafe Python is a myth
        new_folge = copy.deepcopy(other)
        for key, value in attributes.items():
            if not hasattr(new_folge, key):
                raise AttributeError(f"Folge does not have attribute '{key}'")
            setattr(new_folge, key, value)
        return new_folge


    def get_diff_other(self, other: 'Folge') -> dict[str: int]:
        """
        Gives the precise difference between this object and another Folge. Its not mighty useful when comparing
        to any other Folge (except maybe you want to know if parts are the same) but it has its use if you edit
        one and then want to know how big the difference is
        You get an empty dict aka. a falsy thing if the 'other' is not up to the task
        The compared fields are 'title', 'session', 'description', 'desc_addon', 'notes'

        :param Folge other: the other Folge to be compared to
        :rtype: dict
        :return: a dictionary with a the name of a field and the levenstein difference in that line
        :raises: NotImplemented when 'other' is not a Folge
        """
        if not isinstance(other, Folge):
            raise NotImplemented("'other' is not Folge") # still unsure if I want that or just an empty dict
            #return {}
        _c = ['title', 'session', 'description', 'desc_addon', 'notes']
        diff_set = {}
        for each in _c:
            this_one = self.__getattribute__(each)
            the_other = other.__getattribute__(each)
            # * Notes for instances can be None and levenstein does not like comparing None with ""
            if this_one is None:
                this_one = ""
            if the_other is None:
                the_other = ""
            diff_set[each] = textdistance.levenshtein.distance(this_one, the_other)
        return diff_set

    @staticmethod
    def from_episode(this: 'Episode') -> 'Folge':
        template_title = None
        if int(this.template_id) > 0 and hasattr(this.template, "title"):
            template_title = this.template.title
        if not this.notes: # empty note becomes Null
            this.notes = None
        return Folge(
            title=this.title,
            joined_template_title=template_title,
            project_title=this.project.name if this.project else None,
            counter1=this.counter1,
            counter2=this.counter2,
            extra_counter=this.extra_counter,
            session=this.session,
            description=this.description,
            desc_addon=this.desc_addon,
            notes=this.notes,
            yt_link=this.yt_link,
            yt_human_touch=this.yt_human_touch,
            recording_date=this.record_date,
            db_uid=this.id,
            db_project=this.project_id,
            db_template=this.template_id,
            edit_date=this.edit_date,
            create_date=this.create_date
        )

@dataclass
class Playlist:
    # TODO: Projects have a short name in my world, integrate that
    title: str
    #abbr: str
    category: str = ""
    description: str = ""
    notes: str | None = None
    # * Youtube Connection (or any other video site I guess?)
    yt_link: str | None = None
    yt_human_touch: bool | None = None

    db_uid: int = 0
    opt_newest_episode: datetime | None = None # additional data for tree view

    @staticmethod
    def from_project(this: 'Project') -> 'Playlist':
        if hasattr(this, 'opt_newest_episode'):
            newest = this.opt_newest_episode
        else:
            newest = None
        return Playlist(
            title=this.name,
            #abbr=this.abbr,
            category=this.category,
            description=this.description,
            notes=this.notes,
            yt_link=this.yt_link,
            yt_human_touch=this.yt_human_touch,
            opt_newest_episode=newest,
            db_uid=this.id
        )

    def __eq__(self, other: 'Playlist') -> bool:
        """
        Actually compares only the non-database parts against each other
        :param other:
        :return:
        """
        if not isinstance(other, Playlist):
            return NotImplemented
        if (self.title == other.title
                and self.description == other.description
                and self.category == other.category):
            return True
        return False

    def __bool__(self) -> bool:
        """
        Returns whether a playlist object is empty or not
        :return:
        """
        if not self.title and not self.category and not self.description:
            return False
        return True

@dataclass
class PatternTemplate:
    title: str
    pattern: str = ""
    tags: str = ""
    # see database model for explanation what this is supposed to be
    description_prefix: str = "\\n"
    description_suffix: str = "\\n"
    description_addon_prefix: str = "\\n"
    description_addon_suffix: str = "\\n"
    db_uid: int = 0

    @staticmethod
    def from_TextTemplate(this: 'TextTemplate') -> 'PatternTemplate':
        return PatternTemplate(
            title=this.title,
            pattern=this.pattern,
            db_uid=this.id,
            tags=this.tags,  # TODO: implement tags database site # what? -- 2026-03-10
            description_prefix=this.description_prefix,
            description_suffix=this.description_suffix,
            description_addon_prefix=this.description_addon_prefix,
            description_addon_suffix=this.description_addon_suffix
        )

@dataclass
class YtVideo:
    """
    Technically a Youtube Video that is part of a playlist if this is properly hydrated
    """
    yt_id: str
    title: str
    description: str = ""
    views: int | None = None
    upload_date: datetime | None = None
    publish_date: datetime | None = None
    last_update: datetime | None = None
    last_full_update: datetime | None = None
    template_id: int | None = None
    playlist: str | None = None # not always hydrated
    pl_project_id: int | None = None # not always hydrated
    pl_pos: int | None = None # not always hydrated
    # YtVideo can exist outside a Playlist, so the association only exists in context
    edit_date: datetime | None = datetime.now()
    create_date: datetime | None = datetime.now()

    # TODO: unify usage of methods in DTOs and db objects
    """It appears that the original Episode/Folge stuff follows a different philosophy
    than the later youtube linking things, that annoys me greatly, I am quite sure i have
    written this text already somewhere, maybe in a commit message or so"""

    @staticmethod
    def from_yt_db_vid(this: 'YtDbVid') -> 'YtVideo':
        return YtVideo(yt_id=this.yt_id,# linter complaints, but this works automagically
                       title=this.title,
                       description=this.description,
                       views=this.views,
                       upload_date=this.upload_date,
                       publish_date=this.publish_date,
                       last_update=this.last_update,
                       last_full_update=this.last_full_update,
                       template_id=this.template_id,
                       edit_date=this.edit_date,
                       create_date=this.create_date)

    @staticmethod
    def from_yt_db_vid_hydrated(this: 'YtDbVid', playlist_yt_id: str):
        raise NotImplemented # this is somehow more sexy than just empty returns

@dataclass
class YtPlaylist:
    yt_id: str
    title: str
    description: str = ""
    project_id: int | None = None
    project_title: str | None = None
    publish_date: datetime | None = None
    last_update: datetime | None = None
    entries: int = 0

    @staticmethod
    def from_yt_db_play(this: 'YtDbPlay') -> 'YtPlaylist':
        return YtPlaylist(
            yt_id=this.yt_id,
            title=this.title,
            description=this.description,
            project_id=this.project_id,
            project_title=None, # TODO handle this properly
            publish_date=this.publish_date,
            last_update=this.edit_date,
            entries=this.entries
        )

class BaseModel(Model):
    class Meta:
        database = database_proxy

class Project(BaseModel):
    name = CharField()
    #abbr = CharField()
    category = CharField()
    description = TextField()
    notes = TextField(default="", null=True)

    yt_link = CharField(null=True)
    yt_human_touch = BooleanField(default=False, null=True)

    edit_date = DateTimeField(default=datetime.now)
    create_date = DateTimeField(default=datetime.now)

    def __str__(self):
        return f"Peewee:Project::'{str(self.name)}', cat:'{str(self.category)}', desc:{len(self.description)}, notes:{len(self.notes) if self.notes else 0}"

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
    def get_categories(ordered: Literal['ASC', 'DESC'] | None = None) -> list[str]:
        if not ordered:
            res = Project.select(Project.category).distinct(True)
        elif ordered == "DESC":
            res = (Project
                   .select(Project.category).distinct(True)
                   .join(Episode, JOIN.LEFT_OUTER)  # .join(Episode, on=(Episode.project_id == Project.id))
                   .group_by(Project.category)
                   .order_by(fn.Max(Episode.edit_date).desc())
                   )
        else:  # this seems to not be easier possible
            res = (Project
                   .select(Project.category).distinct(True)
                   .join(Episode, JOIN.LEFT_OUTER)  # .join(Episode, on=(Episode.project_id == Project.id))
                   .group_by(Project.category)
                   .order_by(fn.Max(Episode.edit_date).asc())
                   )
        flood = []
        for each in res:
            flood.append(str(each.category))
        return flood

    @staticmethod
    def get_last_edited():
        """
        Gives the database ID of the project whichs episode was last edited.
        Its **NOT** the last editet project, this would be much simpler.

        Another contender of the most specific bullshit I can come with up. I justify this
        functions existence with the fact that all the static class functions are basically
        just shorthands for queries that could also exist as part of a different utility
        class file but are instead directly joined into the database connection
        layer, as long no names are overwritten this should be okay.
        :return:
        """
        res = (Project
               .select(Project.id).distinct(True)
               .join(Episode, JOIN.LEFT_OUTER)  # .join(Episode, on=(Episode.project_id == Project.id))
               .group_by(Project.id) # necessary?
               .order_by(fn.Max(Episode.edit_date).desc())
               )
        for each in res:
            return int(each.id)

    @staticmethod
    def update_or_create(this: Playlist) -> int:
        if this.db_uid <= 0:
            return Project.create_new(this)
        res = (Project.update(
                name=this.title,
                category=this.category,
                description=this.description,
                notes=this.notes,
                yt_link=this.yt_link,
                yt_title=this.yt_title,
                yt_desc=this.yt_desc,
                yt_last_link=this.yt_last_link,
                edit_date=datetime.now()
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
                notes=this.notes,
                yt_link=this.yt_link,
                yt_human_touch=this.yt_human_touch,
                )
               .execute())
        return res

    @staticmethod
    def create_raw(title: str,
                   category: str = "default",
                   description: str = "",
                   notes: str | None = None,
                   yt_link: str | None = None,
                   yt_human_touch: bool | None = None,
                   edit_date: datetime | str | None = None,
                   create_date: datetime | str | None = None) -> int:
        """
        This creates a new Episode entity, but this time without the help of a playlist and with
        the ability to manually set the created / edited date to arbitrary date.
        I created this to facilitate imports of data

        :param str notes: Project Notes
        :param str yt_link: YouTube url part, e.g. pxdL8y-0eH0
        :param bool yt_human_touch: whether the link was actually approved by someone
        :param title: the title of the project, can not be empty
        :param category: category to be sorted through, defaults to 'default'
        :param description: description, can be empty
        :param edit_date: manually set date for last edit, str must be isoformat
        :param create_date: manually set date for creation, str must be isoformat
        :return:
        """
        create_date = normalize_datetime(create_date)
        edit_date = normalize_datetime(edit_date)
        res = (Project.insert(
                name = title,
                category = category,
                description = description,
                notes=notes,
                yt_link=yt_link,
                yt_human_touch=yt_human_touch,
                edit_date = edit_date,
                create_date = create_date
            ).execute())
        return res

    @staticmethod
    def has_counter2(project_id: int) -> bool | None:
        """
        Checks if the given project has any episodes with counter2, should
        always return true or false, even if the project doesn't exists, because
        logically, then the number of entries is zero.

        I wrote this and some other functions to then realise that I got tired so
        now *list_empty_fields_in_project* exists that basically does this in one
        go, I havent measure performance, in Theory and big Big **BIG** Databases
        it should be faster to do in directly in the database but apart from that,
        *list_empty_fields_in_project* seems to be the easier way to make this more
        ... *agile* or *lean*

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

    @staticmethod
    def list_empty_fields_in_project(project_id: int) -> list | None:
        """
        Checks if the given project has fields in the assigned Episodes that
        are consistently empty, useful if you want to not clutter your interface
        with columns of unneeded information. The possible fields are unfortunately
        hardcoded as I couldn't be bothered with reading the docs to properly extract
        the correct database fields from the class definition

        :param project_id: database uid of the project you are interested in
        :return: either None if something goes wrong or a list of empty fields.
        **IMPORTANT** an *empty* list is also **not** if you check for it, remember
        to properly check for `if res is not Null:` instead of `if res:`
        """
        fields = ['title', 'counter1', 'counter2', 'extra_counter', 'desc_addon', 'description', 'notes', 'session', 'yt_link']
        try:
            res : list[Episode] = Episode.select().where(Episode.project_id == project_id)
            for each in res:
                for field in fields:
                    if each.__getattribute__(field): # ? so, not Null, not '' or not 0
                        fields.remove(field)
                        continue
            return fields
        except Episode.DoesNotExist:  # this should never happen
            return None
    
    @staticmethod
    def get_tree_as_playlist() -> list[Playlist] | None:
        """
        Returns the same as dump() BUT ordered by the edit_date of the entries, starting
        with the newest edit.

        So, this does work, but I am still not entirely happy with it.

        SELECT project.*, MAX(episode.edit_date) AS opt_newest_episode
        FROM project LEFT JOIN episode
        ON project.id = episode.project_id
        GROUP BY project.id, episode.project_id
        ORDER BY MAX(episode.edit_date) DESC
        :return: list[Playlist]
        """
        try:
            res = (Project
                   .select(Project.id,
                     Project.name,
                     Project.description,
                     Project.category,
                     fn.Max(Episode.edit_date).alias("opt_newest_episode"))
                   .join(Episode, JOIN.LEFT_OUTER) #.join(Episode, on=(Episode.project_id == Project.id))
                   .group_by(Project.id, Episode.project_id)
                   .order_by(fn.Max(Episode.edit_date).desc())
                   )
            flood = []
            for each in res:
                flood.append(Playlist.from_project(each))
            return flood
        except Project.DoesNotExist:
            return None

    @staticmethod
    def is_empty(project_id) -> bool:
        """
        Checks if there are any episodes assigned to this project

        :param project_id: DB UID of the project
        :return: True if any episodes are to be found
        """
        res = (Episode.select().where(Episode.project_id == project_id).count())
        return not bool(res)

class TextTemplate(BaseModel):
    title = CharField()
    pattern = TextField(default="", null=True)
    tags = CharField(512, null=True)
    # most annoying extra fields to facilitate little changes in a niché
    """
    So what this does, because why not write 20 Lines of inline comment to explain a feature..
    Features that dont explain themselves are always the best. So, I added the ability for templates
    to have descriptions and description addon directly backed in. The problem now is that those fields
    are in general probably empty and not filled for most projects or episodes, but, if they are there
    it seems annoying to save additional whitespace or new lines. Especially because the only interface
    that currently allows editing those features trims the whitespace anyway. So I add those 4 fields 
    so that one can configure some additional white space, probably I just set the default to new line
    because that is literally the only usecase I can think of. I will probably forever be the only person
    ever that uses this niché tool, but I like to pretend I write for an Audience, so I built features 
    likes this. -- 2026-03-10
    """
    description_prefix = TextField(default="\n", null=True)
    description_suffix = TextField(default="\n", null=True)
    description_addon_prefix = TextField(default="\n", null=True)
    description_addon_suffix = TextField(default="\n", null=True)

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
                description_prefix=this.description_prefix,
                description_suffix=this.description_suffix,
                description_addon_prefix=this.description_addon_prefix,
                description_addon_suffix=this.description_addon_suffix,
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
                description_prefix=this.description_prefix,
                description_suffix=this.description_suffix,
                description_addon_prefix=this.description_addon_prefix,
                description_addon_suffix=this.description_addon_suffix,
                create_date=datetime.now(),
                edit_date=datetime.now()
                )
               .execute())
        return res

    @staticmethod
    def create_raw(title: str,
                   pattern: str | None = "",
                   tags: str | None = "",
                   description_prefix: str | None = "\\n",
                   description_suffix: str | None = "\\n",
                   description_addon_prefix: str | None = "\\n",
                   description_addon_suffix: str | None = "\\n",
                   edit_date: datetime | str | None = None,
                   create_date: datetime | str | None = None) -> int:
        create_date = normalize_datetime(create_date)
        edit_date = normalize_datetime(edit_date)
        if not tags: # TODO null constraint in other logic, database accepts null
            tags = ''
        res = (TextTemplate.insert(
                title=title,
                pattern=pattern,
                tags=tags,
                description_prefix=description_prefix,
                description_suffix=description_suffix,
                description_addon_prefix=description_addon_prefix,
                description_addon_suffix=description_addon_suffix,
                edit_date=edit_date,
                create_date=create_date
               ).execute())
        return res

class Episode(BaseModel):
    title = CharField()
    counter1 = IntegerField(null=False)
    counter2 = IntegerField(default=None, null=True)
    extra_counter = CharField(null=True)
    record_date = DateField()
    session = CharField(default='', null=True)
    description = TextField(default='', null=True)
    desc_addon = TextField(default='', null=True)
    notes = TextField(null=True)
    yt_link = CharField(null=True)
    yt_human_touch = BooleanField(default=False, null=True)
    # IDEA: tag for "uncompleted work" - easy toggle bar to mark things where I am not done

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
        Creates a new Episode entry in the database, OR if the the Folge object contains a
        db_uid it will instead update the corresponding entry in the database..the will totally
        predictable go haywire if you just provide an UID that doesnt exist.

        *Under the hood it just calls Episode.create_new(this) when no db_uid is provided.*

        :param Folge this: a Folge Class object
        :return: uid of the new database entry
        :rtype: int
        """
        if this.db_uid <= 0:
            return Episode.create_new(this)
        if not this.notes: # any none type becomes Null
            this.notes = None
        res = (Episode
               .update(
                title=this.title,
                counter1=this.counter1,
                counter2=this.counter2,
                extra_counter=this.extra_counter,
                record_date=this.recording_date,
                session=this.session,
                description=this.description,
                desc_addon=this.desc_addon,
                notes=this.notes,
                yt_link=this.yt_link,
                yt_human_touch=this.yt_human_touch,
                template_id=this.db_template,
                project_id=this.db_project,
                edit_date=datetime.now()
                )
               .where(Episode.id == this.db_uid)
               .execute())
        return res

    @staticmethod
    def create_new(this: Folge) -> int:
        """
        Uses a Folge class to create a new entry.
        Note: I knew that I could, in theory use the same object for it all..but the DTOs are somewhat
        hydrated and can contain additional info...for the price of having to handle two structures.

        :param Folge this:
        :return:
        """
        if not this.notes: # ? why?
            this.notes = None
        res = (Episode.insert(
            title=this.title,
            counter1=this.counter1,
            counter2=this.counter2,
            extra_counter=this.extra_counter,
            record_date=this.recording_date,
            session=this.session,
            description=this.description,
            desc_addon=this.desc_addon,
            notes=this.notes,
            yt_link=this.yt_link,
            yt_human_touch=this.yt_human_touch,
            template_id=this.db_template,
            project_id=this.db_project
        ).execute())
        return res

    @staticmethod
    def create_raw(title: str,
                   project_id: int,
                   counter1: int = 1,
                   counter2: int | None = 0,
                   extra_counter: str | None = None,
                   record_date: str | None = None,
                   session: str = "",
                   description: str = "",
                   desc_addon: str = "",
                   notes: str | None = None,
                   yt_link: str | None = None,
                   yt_human_touch: bool | None = None,
                   template_id: int | None = None,
                   edit_date: datetime | str | None = None,
                   create_date: datetime | str | None = None) -> int:
        """
        Creates a new Episode by manually writing it all out..mostly used for the import logic to
        save the step of going via an Folge Class.

        :param str title: assigned title of the episode
        :param int project_id: assigned project by id
        :param int counter1: first counter
        :param int counter2: second counter, both should auto-increment
        :param str extra_counter: additional character for counter, like '64**b**'
        :param str record_date: date of recording of this video, not an actual datetime
        :param str session: free text, Session information
        :param str description: pure text description without compiled data
        :param str desc_addon: additional description stuff like timestamps
        :param str notes: Episode Notes
        :param str yt_link: YouTube url part, e.g. pxdL8y-0eH0
        :param bool yt_human_touch: whether the link was actually approved by someone
        :param int template_id: assigned template for text generation
        :param datetime edit_date: datetime of last edit
        :param datetime create_date: datetime of the original creation
        :return: ressource object of pewee, probably 1
        """
        # TODO: normalize record_date
        create_date = normalize_datetime(create_date)
        edit_date = normalize_datetime(edit_date)
        res = (Episode.insert(
            title=title,
            counter1=counter1,
            counter2=counter2,
            extra_counter=extra_counter,
            record_date=record_date,
            session=session,
            description=description,
            desc_addon=desc_addon,
            notes=notes,
            yt_link=yt_link,
            yt_human_touch=yt_human_touch,
            template_id=template_id,
            project_id=project_id,
            edit_date=edit_date,
            create_date=create_date
        ).execute())
        return res

class Settings(BaseModel):
    key = TextField(unique=True)
    value = TextField()

    @staticmethod
    def update_or_set_key(this_key: str, this_value: str) -> bool:
        (Settings
            .insert(key=this_key, value=this_value)
            .on_conflict(
                conflict_target=Settings.key,
                update={Settings.value: this_value})
            .execute()
        )

    @staticmethod
    def save_retrieve_key(this_key: str, default=None) -> str | None:
        try:
            res = (Settings
             .select()
             .where(Settings.key == this_key)
             .limit(1)
             .get())
            if res.value is None:
                return default
            return res.value
        except Settings.DoesNotExist:
            return default

    @staticmethod
    def get_keys(keys: list[str], error_fallback: bool = True) -> dict[str: str] | None:
        """
        Retrieves multiple keys at once
        :param list[str] keys: list of settings keys to be retrieved
        :param bool error_fallback: if False will return None if **any** of the keys doesn't exist
            but won't return partial lists either
        :rtype dict[str: str] | None
        :return: either a dictionary key: value with the keys or None
        """
        try:
            res = (Settings
                   .select(Settings.key, Settings.value)
                   .where(Settings.key << keys))
            response: dict = {}
            for item in res:
                response[item.key] = item.value
                keys.remove(item.key)
            if keys and not error_fallback: # something left in keys
                return None
            return response
        except Settings.DoesNotExist:
            return None

# ! Youtube Stuff - Walls of Text ahead to explain the mess
""" 2026-03-18
So, I think I have to write this in prose to make my thoughts a bit more clear
and less opaque. There is a rate limit on requesting stuff from youtube, also
I envisioned this tool as something that works without internet in a situation
like a train. So I cache everything and act as if for every request we have to
send an expedition to the holy data vaults on the other side of the tundra. 
Paranoid, I know. Anyway, initially I thought my special use case only needs 
videos that reside in a playlist, and that is mostly true, episode_names works
for episodic stuff that has an amount of repeating features, but then it occured
me that my own channel has multiple playlist with the same videos in it, its mostly
stuff like DLCs getting their own playlist for visibility while the original 
main game still got the DLC content in the order of recording.
Therefore, 3 tables, one for the playlist, another for videos so we dont have
redundancy and then a third table that contains just the order of each playlists 
videos. Holding this all in my head creates an headache tbh.
"""

class YtDbPlay(BaseModel): # ? this name is hell
    yt_id = CharField(max_length=36, primary_key=True, unique=True) # actually its 34
    project = ForeignKeyField(Project, lazy_load=True, null=True)
    title = CharField(max_length=150)
    description = TextField(null=True)
    entries = IntegerField()

    publish_date = DateTimeField(null=True)
    edit_date = DateTimeField(default=datetime.now)
    create_date = DateTimeField(default=datetime.now)

    @staticmethod
    def get_all_from_db() -> list['YtPlaylist'] | None:
        try:
            res = (YtDbPlay.select())
            flood = []
            for each in res:
                flood.append(YtPlaylist.from_yt_db_play(each))
            return flood
        except BaseModel.DoesNotExist:
            return None

    @staticmethod
    def assign_videos(playlist_id: str, vids: list[YtVideo]) -> bool:
        # purge numbering for this playlist
        YtDbNumbering.purge_playlist_links(playlist_id)
        for each in vids:
            YtDbVid.update_or_create(each)
            # create connection
            YtDbNumbering.update_or_create(playlist_id, each.yt_id, each.pl_pos)
        return True

    @staticmethod
    def get_playlist_videos(playlist_id: str, start_position: int = 0) -> list[YtVideo] | None :
        try: # first check if that playlist even exsits
            playlist = YtDbPlay.get_by_id(playlist_id)
        except YtDbPlay.DoesNotExists:
            return None
        try:
            res = (YtDbNumbering
                   .select(YtDbNumbering.video, YtDbNumbering.position)
                   .join(YtDbVid, JOIN.LEFT_OUTER)
                   .where(YtDbNumbering.playlist_id == playlist_id)
                   .where(YtDbNumbering.position >= start_position)
                   .order_by(YtDbNumbering.position))
            if not res:
                return None
            hydrated_videos = []
            for each in res:
                one = YtVideo.from_yt_db_vid(each.video)
                one.playlist=playlist_id
                one.pl_pos = each.position
                one.pl_project_id = playlist.project_id
                hydrated_videos.append(one)
            return hydrated_videos
        except YtDbPlay.DoesNotExist:
            return None

    @staticmethod
    def update_or_create(this: YtPlaylist) -> str:
        # TODO: on conflict rules not working, investigate
        res = (YtDbPlay.insert(
            yt_id=this.yt_id,
            title=this.title,
            description=this.description,
            entries=this.entries,
            publish_date=this.publish_date,
            project_id=this.project_id,
            edit_date=datetime.now(),
            create_date=datetime.now(),
        ).on_conflict(
            conflict_target=(YtDbPlay.yt_id,),
            preserve=(YtDbPlay.title,
                      YtDbPlay.description,
                      YtDbPlay.entries,
                      YtDbPlay.publish_date,
                      YtDbPlay.project,
                      YtDbPlay.edit_date),
            update={
                YtDbPlay.edit_date: datetime.now(),
            }
        ).execute())
        return res

    @staticmethod
    def update_or_create_raw(yt_id: str,
                             title: str,
                             description: str | None = None,
                             entries: int = 0,
                             project_id: int | None = None,
                             publish_date: str | datetime | None = None,
                             edit_date: str | datetime | None = None,
                             create_date: str | datetime | None = None) -> str:
        # ! as only function this can, if no entry exists, fuck around with edit/create date
        res = (YtDbPlay.insert(
            yt_id=yt_id,
            title=title,
            description=description,
            entries=entries,
            publish_date=publish_date,
            project_id=project_id,
            edit_date=normalize_datetime(edit_date, True),
            create_date=normalize_datetime(create_date, True),
        ).on_conflict(
            conflict_target=(YtDbPlay.yt_id,),
            preserve=(YtDbPlay.create_date,YtDbPlay.project),
            update={
                YtDbPlay.title: title,
                YtDbPlay.description: description,
                YtDbPlay.entries: entries,
                YtDbPlay.publish_date: normalize_datetime(publish_date),
                YtDbPlay.edit_date: datetime.now(),
            }
        ).execute())
        return res

"""
I was considering just making on big table called "YtRessource" and combine 
playlists and videos and just distinguish them with one more field but in the 
end I decided to not be lazy and wrote two seperate tables, although I am 
not sure if it wouldnt have been easier, more headache, shore, but in the 
end less duplicated text that has to be taken care of in other places like
the export things. 
"""
class YtDbVid(BaseModel):
    yt_id = CharField(max_length=12, primary_key=True, unique=True) # its 11 actually?

    title = CharField(max_length=100)
    description = TextField(null=True)
    views = IntegerField(null=True)
    upload_date = DateTimeField(null=True)
    publish_date = DateTimeField(null=True)

    template = ForeignKeyField(TextTemplate, lazy_load=True) # overwrites playlist template

    last_update = DateTimeField(null=True) # general update, like from playlistItems
    last_full_update = DateTimeField(null=True) # when extra video data was retrieved

    edit_date = DateTimeField(default=datetime.now)
    create_date = DateTimeField(default=datetime.now)

    # ? boilerplate functions because I insist of using DTOs
    # I wrote these all by hand btw..no llms involved
    # * the methods are slightly different because the primary key is external

    @staticmethod
    def update_or_create(this: YtVideo) -> str:
        res = (YtDbVid.insert(
            yt_id=this.yt_id,
            title=this.title,
            description=this.description,
            views=this.views,
            upload_date=this.upload_date,
            publish_date=this.publish_date,
            template_id=this.template_id,
            last_update=datetime.now(),
            last_full_update=this.last_full_update,
            edit_date=datetime.now(),
            create_date=datetime.now(),
        ).on_conflict(
            conflict_target=(YtDbVid.yt_id,),
            preserve=(YtDbVid.title,
                YtDbVid.description,
                YtDbVid.views,
                YtDbVid.upload_date,
                YtDbVid.publish_date,
                YtDbVid.template,
                YtDbVid.last_full_update),
            update={
                YtDbVid.last_update: datetime.now(),
                YtDbVid.edit_date: datetime.now(),
            }
        ).execute())
        return res

    @staticmethod
    def create_or_update_raw(yt_id: str,
                   title: str,
                   description: str | None = None,
                   views: int | None = None,
                   upload_date: str | datetime | None = None,
                   publish_date: str | datetime | None = None,
                   template_id: int | None = None,
                   last_update: str | datetime | None = None,
                   last_full_update: str | datetime | None = None,
                   edit_date: str | datetime | None = None,
                   create_date: str | datetime | None = None) -> str:
        """

        :param yt_id: actual id on youtube.com
        :param title: title, mandatory
        :param description: description
        :param views: amount of views, might be null
        :param upload_date: upload day of the video
        :param publish_date: day the video was actually published
        :param template_id: textemplate for reverse operations
        :param last_update: last fetch from the internet
        :param last_full_update: last full fetch as video ressource
        :param edit_date: internal db operations, self explanatory
        :param create_date: internal db operations date
        :return:
        """
        res = (YtDbVid.insert(
            yt_id = yt_id,
            title = title,
            description = description,
            views = views,
            upload_date = normalize_datetime(upload_date),
            publish_date = normalize_datetime(publish_date),
            template_id = template_id,
            last_update = normalize_datetime(last_update),
            last_full_update = normalize_datetime(last_full_update),
            edit_date = normalize_datetime(edit_date, True),
            create_date = normalize_datetime(create_date, True)
        ).on_conflict(
            conflict_target=(YtDbVid.yt_id,),
            preserve=(YtDbVid.title,
                YtDbVid.description,
                YtDbVid.views,
                YtDbVid.upload_date,
                YtDbVid.publish_date,
                YtDbVid.template_id,
                YtDbVid.last_full_update),
            update={
                YtDbVid.edit_date: datetime.now(),
            }
        ).execute())
        return res

class YtDbNumbering(BaseModel):
    playlist = ForeignKeyField(YtDbPlay, lazy_load=True)
    video = ForeignKeyField(YtDbVid, lazy_load=True)
    position = IntegerField()

    @staticmethod
    def update_or_create(playlist_id: str, video_id: str, position: int):
        # TODO: this isnt working potentially
        res = (YtDbNumbering.insert(
            playlist_id=playlist_id,
            video_id=video_id,
            position=position
        ).execute())
        return res

    @staticmethod
    def purge_playlist_links(playlist_id: str) -> int:
        res = (YtDbNumbering.delete().where(YtDbNumbering.playlist_id == playlist_id).execute())
        return res

class EditDelta(BaseModel):
    size = IntegerField(default=0)
    note = TextField(null=True) # ? this has no immediate use, but I thought i might add the kind of change later
    episode = ForeignKeyField(Episode, null=True, lazy_load=True)
    project = ForeignKeyField(Project, null=True, lazy_load=True)
    template = ForeignKeyField(TextTemplate, null=True, lazy_load=True)
    edit_date = DateTimeField(default=datetime.now)  # yes yes, its basically the _CREATE_ time..but then
    # we are comparing edits here no?

    # the following is opiniated and I wonder if I can make this part of a config somehow
    # limits for Episode
    desc_diff:int = 20 # characters
    desc_addon: int = 10 # Characters
    title_diff:int = 5 # characters

    @staticmethod
    def maybe_add_episode_delta(folge_a: Folge, folge_b: Folge) -> bool:
        """
        Adds an entry to the EditDelta table if the difference between two Folge is big enough, "big enought" is
        currently defined as:
        Description: 20 characters
        Desc_Addon: 10 Characters
        Titel: 5 Characters
        :param folge_a:
        :param folge_b:
        :return:
        """
        # ! probably fails for description and desc addon alone
        if not isinstance(folge_a, Folge):
            return False
        if not folge_a.db_uid: # floating Folges dont work here
            return False
        # ? maybe check if both are actually the same Folge_ID?
        diff_set = folge_a.get_diff_other(folge_b)
        if not diff_set:
            return False
        if diff_set['description'] < EditDelta.desc_diff \
            and diff_set['desc_addon'] < EditDelta.desc_addon \
            and diff_set['title'] < EditDelta.title_diff:
            return False
        combined_size = diff_set['description'] + diff_set['desc_addon'] + diff_set['title']
        res = (EditDelta.insert(
            size=combined_size,
            note=None,
            episode_id=folge_a.db_uid,
            edit_date=datetime.now()
            ).execute())
        if not res:
            return False
        return True

    @staticmethod
    def get_all_episode_edits(episode_id: int, ordered: Literal['desc', 'asc'] = 'asc') -> list[tuple[datetime, int]]:
        """
        Get all edits of one episode in order of datetime as size in changed characters

        :param episode_id: the internal database id of the episode
        :param ordered: asc or desc for ascending vs descending from now to cavepeople
        :return: a list, containing a tuple of datetime, (int) characters changed per entry
        """
        # ? I think in theory I could have used the datetime as key for an dictionary or rather the ISO String
        # ? but that would open up the edge case that for some weird reason two edits happened on the same millisecond
        # * blantant
        # ! more
        try:
            if ordered == "asc":
                res: list[EditDelta] = (EditDelta  # its a blantant lie, res is NOT just a list
                                        .select(EditDelta.edit_date, EditDelta.size)
                                        .order_by(EditDelta.edit_date.asc())
                                        .where(EditDelta.episode_id == episode_id)
                                        )
            else:
                res: list[EditDelta] = (EditDelta  # its a blantant lie, res is NOT just a list
                                        .select(EditDelta.edit_date, EditDelta.size)
                                        .order_by(EditDelta.edit_date.desc())
                                        .where(EditDelta.episode_id == episode_id)
                                        )
        except EditDelta.DoesNotExist:
            return []
        if len(res) <= 0:
            return []
        edits = []
        for each in res:
            print(each)
            edits.append((each.edit_date, each.size))
        return edits

    @staticmethod
    def get_all_project_edits(project_id: int, order: str = "asc") -> list[tuple[datetime, int]]:
        pass

def init_db(db_path="episoden_names.db",  creation=False):
    """
    Creates a new db or connects to one if the name exists

    For historic reasons this is one function even when the creation of
    a new blank database is something very different, but for now this
    works reasonable well enough I suppose
    :param str db_path: path to database
    :return:
    """
    db = SqliteDatabase(db_path)
    database_proxy.initialize(db)

    db.connect()
    if creation:
        db.create_tables([Episode, Project, TextTemplate, Settings,
                          YtDbPlay, YtDbVid, YtDbNumbering, EditDelta])
        Project.create_raw("Default Project")
        (Settings # is that a global variable? how do it even have that here?
            .insert(key='db_version', value=__folder_version__)
            .on_conflict(
                conflict_target=Settings.key, # TODO is that the correct on conflict form?
                update={Settings.value: __folder_version__})
            .execute()
        )
        # default settings
        Settings.update_or_set_key("bad_words_project", "Let's, Play")
        Settings.update_or_set_key("bad_words_video", "der, die, das, the, and, und, bei, von, from, to, zu, auf, nach, vor, dann, mit, zum, zur, kein, wie, was, wer, wo, welche, des, dem, viel, ein, eine, in, of, -, Let's, Play")
    return True

if __name__ == "__main__":
    init_db("../../test.db", creation=True)
