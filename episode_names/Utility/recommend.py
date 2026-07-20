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
import logging
from typing import Union

from episode_names.Utility.db import Episode, YtVideo, YtPlaylist, Folge, TextTemplate, PatternTemplate, init_db, \
    YtDbVid, YtDbPlay, Project

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

# ? this is all for development and should only really work on my machine if I ever commit this
# ? sorry
import os
import re

from difflib import SequenceMatcher
from platformdirs import user_data_dir
__appname__ = "episode_names"
__appauthor__ = "BurnoutDV"
__folder_version__ = "1.2-dev"

from episode_names.Utility.order import multisub


def wlen(text: str) -> int:
    """
    Counts the word in a text, strips new lines for counting
    :param text:
    :return:
    """
    text = text.replace("\n", "")
    text = text.replace("\r", "")
    text = text.replace("\t", "")
    return len(re.findall(r'\w+', text))

def find_related_project(YtDbPlay_id: str,
                         max_hits: int = 10,
                         additional_bad_words: list[str] | None = None) -> dict[int: str] | None:
    # videos got the exact playlist id in the description
    # similar title in any of the projects
    # look through templates if there is something in it (the raw one without placeholders set)
    # same title as project, need to extra actual title?
    # date correlation? weak sauce tbh
    yt_play : YtDbPlay = YtDbPlay.get_by_id(YtDbPlay_id)
    final_hits = {}
    #### #### #### #### #### #### #### #### #### #### ####
    # exact Id in Template Description
    #### #### #### #### #### #### #### #### #### #### ####
    try:
        res : list[TextTemplate] = (TextTemplate
                                    .select(TextTemplate.id)
                                    .where(TextTemplate.pattern
                                           .contains(YtDbPlay_id)))
        for many in res:
            try:
                episodes : list[Episode] = (Episode
                            .select(Project)
                            .where(Episode.template_id == many.id)
                            .join(Project, JOIN.LEFT_OUTER)
                            .group_by(Episode.project))
                for each in episodes:
                    if each.project.id in final_hits:
                        continue
                    final_hits[each.project.id] = {'name': each.project.name, 'note': "template_desc", 'dist': 1}
                    if len(final_hits) > max_hits:
                        break
            except Episode.DoesNotExist:
                continue
    except TextTemplate.DoesNotExist:
        pass  # TODO: srsly, where is da logging Alan
    #### #### #### #### #### #### #### #### #### #### ####
    # Project Name similarity
    #### #### #### #### #### #### #### #### #### #### ####
    if len(final_hits) < max_hits:
        # ? hand chiseled db queries, not so shore about that one tbh
        single_chars = ['-', '=', '/', '\\', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        # ! my friend regex called and thinks that you need her in your life
        sentence_parts = ['(', ')', '[', ']', '{', '}', '"', "'", '?', '!', '.','=', '&','+']
        title = str(yt_play.title)
        # optional oblivion
        if additional_bad_words:
            for each in additional_bad_words:
                title = title.replace(each, "")  # TODO make this more sophisticated so its words, not part of word
        for each in sentence_parts: # this is so wasteful, must be a better way
            title = title.replace(each, "")
        t_parts = title.split(" ")
        for part in t_parts:
            if part in single_chars: # list.remove() only removes the first hit
                t_parts.remove(part)
        hits = {}
        if len(t_parts):
            for part in t_parts:
                if len(part) <= 0:
                    continue
                # * so many queries..there must be a better SQLite solution right?
                try:
                    res = (Project
                           .select()
                           .where(Project.name.ilike(f'%{part}%')))
                    for each in res:
                        if each.id not in hits:
                            hits[each.id] = each.name
                except Project.DoesNotExist:
                    pass # TODO: logging here Alan
    if hits:
        # rank stuff
        for key, value in hits.items():
            dist = SequenceMatcher(None, title, value)
            hits[key] = {'name': value, 'dist': dist.ratio(), 'note': 'title_matcher'}
        sortiert = sorted(hits, key=lambda x: hits[x]['dist'], reverse=True)
        for each in sortiert:
            if each not in final_hits:
                final_hits[each] = hits[each]
            if len(final_hits) > max_hits:
                break
    #### #### #### #### #### #### #### #### #### #### ####
    # Template Text Similarity
    #### #### #### #### #### #### #### #### #### #### ####
    if len(final_hits) < max_hits:
        try:
            res: list[Episode] = (Episode.select() # this cast is a blatant lie
                                  .join(TextTemplate, JOIN.LEFT_OUTER)
                                  .join(Project, on=(Episode.project_id == Project.id))
                                  .group_by(Episode.template.id)) # ? Projects can have multiple templates
            template_matches = {}
            for tt in res:
                dist = SequenceMatcher(None, title, tt.template.pattern)
                template_matches[tt.project.id] = {'name': tt.project.name, 'dist': dist.ratio(), 'note': 'template_matcher'}
            if template_matches: # can it ever be empty?
                moar_sort = sorted(template_matches, key=lambda x: template_matches[x]['dist'], reverse=True)
                for each in moar_sort:
                    if each not in final_hits:
                        final_hits[each] = template_matches[each]
                    if len(final_hits) > max_hits:
                        break
        except TextTemplate.DoesNotExist:
            pass # TODO: moar logging ALAN! Moar!
    # ! Return
    if final_hits: # maybe do something if distant is lower than 0.10?
        return final_hits
    return None

# ? Idee: bestimmte Teile automatisiert erkenne, wie Meta daten blöcke anhand von
# ? playlist links oder chapter notes daran das sie ein bestimmtes zeit format ham

def find_related_folge(rev_entity: Folge | YtVideo,
                       max_hits: int= 10,
                       additional_bad_words: list | None = None) -> dict[int: Folge] | None:
    folgen_list = {}
    if isinstance(rev_entity, Folge):
        deep_knowledge = True
    elif isinstance(rev_entity, YtVideo):
        deep_knowledge = False
    else:
        return None # cannot handle whatever else there might be
    # ? do not show projects that already have a link?
    #! Step 1: direct hits with 100% same title
    if deep_knowledge: # this really does only work if we have a perfectly fine extracted Folge
        hits = None
        if rev_entity.db_project: # decreases search hits:
            try:
                hits = (Episode.select()
                        .where(Episode.project == rev_entity.db_project)
                        .where(Episode.title.contains(rev_entity.title)).
                        limit(15))
            except Episode.DoesNotExist:
                pass # nothing happened
        else:
            try:
                hits = (Episode.select()
                        .where(Episode.title.contains(rev_entity.title)).
                        limit(15))
            except Episode.DoesNotExist:
                pass
        if hits:
            for episode in hits:
                folgen_list[episode.id] = Folge.from_episode(episode)
                if len(folgen_list) > max_hits:
                    return folgen_list
    #! Step 2: we look for chunks of title shards in other titles..this is where the spam begins
    # TODO: this is language thing, has to be configurable
    sentence_parts = ["der", "die", "das", "the", "and", "und", "bei", "von", "from", "to",
                      "zu", "auf", "nach", "vor", "dann", "mit", "zum", "zur", "kein", "wie",
                      "was", "wer", "wo", "welche", "des", "dem", "viel", "ein", "eine", "in"]
    if additional_bad_words: # TODO: make those be regex aware # TODO: write texts that explain that
        sentence_parts = sentence_parts + additional_bad_words
    # YtVideo and Folge both got a title
    pieces = rev_entity.title.split(" ") # I boldly assume multi-word titles
    shatter = []
    for each in pieces: # I think this is "expensive" and can be done "cheaper" in a pythonic way
        if each not in sentence_parts:
            shatter.append(each)
    hits = {}
    project = rev_entity.db_project if deep_knowledge else rev_entity.pl_project_id
    if len(shatter): # ? for all sentence parts we search everywhere
        for part in shatter:
            if len(part) <= 0: # shouldnt happen
                continue
            try:
                if project:
                    res: list[Episode] = (Episode
                           .select()
                           .where(Episode.project == project)
                           .where(Episode.title.ilike(f'%{part}%')))
                else:
                    res: list[Episode] = (Episode
                           .select()
                           .where(Episode.title.ilike(f'%{part}%')))
                for each in res:
                    if each.id not in hits:
                        hits[each.id] = Folge.from_episode(each) # THIS is expensive..i think
            except Project.DoesNotExist:
                pass  # TODO: logging here Alan
    if hits:
        # rank stuff
        for key, other_folge in hits.items():
            dist = SequenceMatcher(None, rev_entity.title, other_folge.title)
            hits[key] = {'folge': other_folge, 'dist': dist.ratio(), 'note': 'title_matcher'}
        sortiert = sorted(hits, key=lambda x: hits[x]['dist'], reverse=True)
        for each in sortiert:
            if each not in folgen_list:
                hits[each]['folge'].notes = str(hits[each]['dist']) # * cross miss use of a field that isnt used here
                folgen_list[each] = hits[each]['folge']
            if len(folgen_list) > max_hits:
                return folgen_list
    # ! Step 3: by episode number, pretty forward when in project, otherwise not
    # search by regex?
    if not folgen_list:
        return None
    return folgen_list

def use_template_as_reverse_extractor(vid: YtVideo,
                                      tmple: PatternTemplate,
                                      first_line_title: bool = True,
                                      diagnostic: bool = False) -> Folge | None | tuple[str, str]:
    """
    This assumes a lot. Mostly that you write a Template first that captures the essence a repeating
    thing you always do. The use case is that you have always done episodic content following a certain
    structure and this program, going forward generates it the 'compiled' yt descriptions from raw fields
    but for now you want to import whole playlists as backup or you started midway through and want to
    fill up the empty files. So we use a template to go back to raw data. It needs YOU to write a human
    template first that matches what is on youtube..this is really a prime case for stupid machine learning
    and in the far future i might dabble into that, but for we are 100% deterministic and throw regex at
    the problem

    :param first_line_title: we boldly assume that the first line of a template is the title
    :param vid: a yt video file
    :param tmple: a template, usually either the one from the playlist or an individual assigned one
    :param diagnostic: if True the (regex pattern, match block) are returned as tuple instead
    :return:
    """
    if not first_line_title:
        # if the title is somewhere else we need a vastly different approach
        logging.warning("use_template_as_reverse_extractor: first_line_title not supported yet")
        return None
    # ? for some reason I thought $$variable$$ would be better than %%variable%%..so here were are
    # TODO: maybe just change this with a small script on startup for future versions, its not a hard change
    group_names = ['counter1', 'counter2', 'session', 'desc_addon', 'description', 'record_date', 'title']
    # TODO: Folge can have extra_counter
    # TODO: give ability to return re_format and match_blockw
    re_format = multisub([
            ("$$counter1$$", "%%counter1%%"),
            ("$$counter2$$", "%%counter2%%"),
            ("$$session$$", "%%session%%"),
            ("$$desc_addon$$", "%%desc_addon%%"),
            ("$$description$$", "%%description%%"),
            ("$$record_date$$", "%%record_date%%"),
            ("$$title$$", "%%title%%")
        ], tmple.pattern)
    re_format = re.escape(re_format).strip()
    re_format = re_format.replace("/", "\\/") # for some reasons this is not in re.escape
    re_format = multisub([
        ("%%counter1%%", "(?P<counter1>.*)"),
        ("%%counter2%%", "(?P<counter2>.*)"),
        ("%%session%%", "(?P<session>.*)"),
        ("%%desc_addon%%", "(?P<desc_addon>.*)?"),
        ("%%description%%", "(?P<description>.*)"),
        ("%%record_date%%", "(?P<record_date>.*)"),
        ("%%title%%", "(?P<title>.*)")
    ], re_format)
    match_block = vid.title + "\n" + vid.description + "\n"
    if diagnostic: # ? diagnostic return for user site trouble shooting
        return re_format, match_block
    match = re.match(re_format, match_block, re.DOTALL)
    if not match:
        logging.warning("use_template_as_reverse_extractor: No regex match")
        return None
    proto_episode = {}
    for name in group_names:
        try:
            proto_episode[name] = match.group(name)
        except IndexError: # dont care
            continue
    if not proto_episode.get('title', '').strip():
        logging.warning("use_template_as_reverse_extractor: regex match got no title")
        return None
    return Folge(title=proto_episode.get('title'),
                 counter1=proto_episode.get('counter1', 1),
                 counter2=proto_episode.get('counter2', 0),
                 session=proto_episode.get('session', ""),
                 description=proto_episode.get('description', "").strip(),
                 desc_addon=proto_episode.get('desc_addon', "").strip(),
                 recording_date=proto_episode.get('record_date', ""),
                 db_template=tmple.db_uid,
                 joined_template_title=tmple.title # as it happens can we just add this with no cost
                 )

def setup_test_environment():
    user_dir = user_data_dir(__appname__, __appauthor__, version=__folder_version__)
    os.chdir(user_dir)
    init_db("episode_names.db")

if __name__ == "__main__":
    setup_test_environment()
    match_girl = False
    reverse_boy = True
    # matchy girl
    if match_girl:
        import json
        # Rogue Trader:
        random_vid_id = "1w3Tanmb9pc"
        random_playlist_id = "PLAFz5ZZJ21wOLutvyiLs6xpntxRyyO2PX"
        print(f"find relate projects for playlist '{random_playlist_id}'")
        raw_dict = find_related_project(random_playlist_id)
        print(json.dumps(raw_dict, indent=2))
    if reverse_boy:
        tpl = PatternTemplate.from_TextTemplate(TextTemplate.get_by_id(12)) # rogue trader
        vid = YtVideo.from_yt_db_vid(YtDbVid.get_by_id("vWYzPNBNkIM")) # Rogue Trader 47
        print(use_template_as_reverse_extractor(vid, tpl))
    # ! Tests here Alan