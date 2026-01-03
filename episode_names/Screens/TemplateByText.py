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
Idea: define the actual layout of buttons by a text document that generates dynamic options for easy copy and paste texts
"""
from peewee import Select

from episode_names.Utility.custom_widgets import EnPageMarker

test_easy = """OPTION Camera
    📷 Olympus O-M E-M10 Mk IV
    📷 Olympus PEN E-P7
    📷 Panasonic GH5s
    📷 Samsung S20 FE 5G
OPTION Lense
    🔭 12-32mm f3.5-5.6
    🔭 12-40mm f2.8
    🔭 14-140mm f3.5-5.6
    🔭 17mm f1.8
    🔭 20mm f1.7
    🔭 25mm f1.4
    🔭 45mm f1.8
    🔭 75mm f1.8
OPTION Aperture
    ⚙️ ƒ/1.4
    ⚙️ ƒ/1.7
    ⚙️ ƒ/1.8
    ⚙️ ƒ/2.8
    ⚙️ ƒ/4.0
    ⚙️ ƒ/5.6
    ⚙️ ƒ/???
OPTION ISO 
    💡 ISO-200
    💡 ISO-400
    💡 ISO-800
    💡 ISO-1600
    💡 ISO-3200
    💡 ISO-???
OPTION Capturetime
    ⏱️ 1/400s
    ⏱️ 1/200s
    ⏱️ 1/100s
    ⏱️ 1/60s
    ⏱️ 1/40s
    ⏱️ 1/20s
    ⏱️ 1/6s
    ⏱️ ???
TEXT tags
"""

from textual import on, events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import ListView, ListItem, Footer, Input, Select, Label, TextArea, Collapsible
from textual.screen import Screen

class ModularInterface(Screen):

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        """I feel deep in my bones that there is a way more pythonic way to
        make this way better and more compartmentalized"""
        magic_input_text = test_easy
        pattern = magic_input_text.splitlines()
        i = 0
        yield EnPageMarker("f6")
        with ScrollableContainer():
            while True:
                if i > len(pattern)-1:
                    break
                parts = pattern[i].split(" ")
                if parts[0] == "OPTION":
                    stepup = 0
                    entries = []
                    while True:
                        stepup = stepup + 1
                        if pattern[i+stepup][:4] == "    ":
                            entries.append(pattern[i+stepup][4:])
                        else:
                            break
                    yield Select([(text, text) for text in entries], id=parts[1])
                    i = i + stepup - 1
                if parts[0] == "TEXT":
                    yield Input(id=parts[1])
                i = i + 1


    def _on_mount(self) -> None:
        return