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

"""Temporarily language things

Should probably replace this with gettext or something"""
import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    filename="../../i18n.log")

class LanguageArchive(dict):
    def __getitem__(self, item):
        if not item in self:
            logging.warning(f"Unknown token '{item}'")
            return f"F:{item}"
        return super().get(item)


i18n = LanguageArchive({
    'Save': "Save",
    'Cancel': "Cancel",
    'Quit': "Quit",
    'New Entry': "New Entry",
    'Edit Entry': "Edit Entry",
    'Session': "Session",
    'Record Date': "Record Date",
    'Title': "Title",
    'Template': "Template",
    'Name': "Name",
    'Date': "Date",
    'Copy Text': "Copy Text",
    'Templates': "Templates",
    'Template Edit': "Template Edit",
    'Episode': "Episode",
    'Enter Filter here': "Enter Filter here",
    'Duplicate Current': "Duplicate Current",
    'Save Current': "Save Current",
    'Delete Current': "Delete Current",
    'Discard Current': "Discard Current",
    'Switch to Mainscreen': "Switch to Mainscreen",
    'No Template assigned': "No Template assigned/found",
    'Description copied to clipboard': "Description copied to clipboard"
}) # Cheap Trick to make sure there is always something

# i18n['']

if __name__ == "__main__":
    print("This file is not meant to be executed, it was a stop gap measure in the first place.")
