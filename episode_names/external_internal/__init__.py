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

"""
I would love to not have this, but some external dependencies are not updated regularly, so I have to
roll my own..which is more error prone than anything
"""

from episode_names.external_internal.textual_autocomplete import AutoComplete, CompletionStrategy, \
    Dropdown, DropdownItem, InputState

__all__ = [
    "AutoComplete",
    "CompletionStrategy",
    "Dropdown",
    "DropdownItem",
    "InputState",
]