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

"""Temporarily language things

Should probably replace this with gettext or something"""
import logging, re

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    filename="i18n.log")

class LanguageArchive(dict):
    def __getitem__(self, item):
        if not item in self:
            logging.warning(f"Unknown token '{item}'")
            return f"F:{item}"
        return super().get(item)

    def t(self, item:str, replace_list: dict[str: str] | None = None) -> str:
        if not item in self:
            logging.warning(f"Unknown token '{item}'")
            return f"F:{item}"
        if not replace_list:
            return super().get(item)

        def multisub(subs, subject):
            """Simultaneously perform all substitutions on the subject string."""
            # https://stackoverflow.com/a/765835
            pattern = '|'.join('(%s)' % re.escape(p) for p, s in subs)
            substs = [s for p, s in subs]
            replace = lambda m: substs[m.lastindex - 1]
            return re.sub(pattern, replace, subject)
        return multisub([(str(x), str(y)) for x,y in replace_list.items()], super().get(item))

i18n = LanguageArchive({
    'Save': "Save",
    'Cancel': "Cancel",
    'Yes': "Yes",
    'No': "No",
    'Quit': "Quit",
    'Reset': "Reset",
    'Tags': "Tags",
    'Current': "Current",
    'Category': "Category",
    'Projects': "Projects",
    'Create New': "Create New",
    'Toogle Help': "Toogle Help",
    'New Entry': "New",
    'Edit Entry': "Edit",
    'Copy Tags': "Copy Tags",
    'Copy Text': "Copy Text",
    'Assign Template': "Template",
    'Episode Note': "Notes",
    'New Entry created': "New Entry Created",
    'Create Episode': "Create Episode",
    'episode: Create Episode': "episode: Create Episode",
    'Create Episode helper': "Opens a menu to create a new episode for the current project (%%P%%).\nCopies everything from previous episode except the title, iterates counter by one.",
    'Create Episode helper blank': "Opens the creation menu for the first blank episode of project %%P%%",
    'Edit Episode': "episode: Edit Episode '%%E%%'",
    'Edit Episode Helper': "Opens a menu to edit episode '%%E%%' of project %%P%%",
    'Create Project': "Create",
    'Edit Project': "project: Edit Project '%%P%%'",
    'Edit Project Helper': "Opens a menu to edit project '%%P%%' (ID: %%DB%%)",
    'Edit current Project': "Edit",
    'Create a new Project': "Create a new Project",
    'project: Create a new Project': "project: Create a new Project",
    'Project Note': "Project Note",
    'Delete Project': "🔥🔥Delete Project🔥🔥", # feeling edgy
    'Opens a menu to create an entire new project from scratch': "Opens a menu to create an entire new project from scratch",
    'Editing an existing Project': "Editing an existing Project",
    'No project currently selected.': "No project currently selected.",
    'Selected project has no ID, this should not be happen.':
        "Selected project has no ID, this should not be happen.",
    'Session': "Session",
    'Record Date': "Record Date",
    'Title': "Title",
    'Notes': "Notes",
    'Template': "Template",
    'Pattern Name': "Pattern Name",
    'Template Content': "Template Content",
    'Template Management': "Template Management",
    'Description': "Description",
    'Description Addon': "Description Addon",
    'No Template': "No Template",
    'Settings': "Settings",
    'Modular': "Modular",
    'Name': "Name",
    'Date': "Date",
    'Templates': "Templates",
    'Template Edit': "Template Edit",
    'Pre & Suffix': "Description Pre & Suffixes",
    'DescPrefix': "Desc. Prefix", # one of the rare cases were key is not plaintext
    'DescSuffix': "Desc. Suffix",
    'DescASuffix': "Desc. Addon Suffix",
    'DescAPrefix': "Desc. Addon Prefix",
    'empty': "  [empty]",
    'Tags copied to clipboard': "Tags copied to clipboard",
    'Episode': "Episode",
    'Episodes': "Episodes",
    'All Notes': "All Notes",
    'Project Notes': "Project Notes",
    'Enter Filter here': "Enter Filter here",
    'Duplicate Current': "Duplicate Current",
    'Copy of': "Copy of",
    'Project Notes Summary': "Project Notes Summary",
    'Edit/Write note for episode': "Edit/Write note for episode",
    'Save Current': "Save Current",
    'Delete Current': "Delete Current",
    'Discard Current': "Discard Current",
    'Switch to Mainscreen': "Switch to Mainscreen",
    'No Option ID': "No Option ID",
    'Do you want to quit?': "Do you want to quit?",
    'No Template assigned': "No Template assigned/found",
    'Description copied to clipboard': "Description copied to clipboard",
    'theme: Change theme': "theme: Change theme",
    'Change the current theme': "Change the current theme",
    'help: Hide keybindings sidebar': "help: Hide keybindings sidebar",
    'Hide the keybindings sidebar': "Hide the keybindings sidebar",
    'Opens the menu to create an entire new project from scratch': "Opens the menu to create an entire new project from scratch",
    'help: Show keybindings sidebar': "help: Show keybindings sidebar",
    'Display keybindings for the focused widget in a sidebar': "Display keybindings for the focused widget in a sidebar",
    'app: Quit episode_names': "app: Quit episode_names",
    'warning_delete_current_data': "Importing a new set of data will delete all current data including settings",
    'Data has changed, you really want to abort?': "Data has changed, you really want to abort?",
    'Quit episode_names and return to the command line': 'Quit episode_names and return to the command line'
}) # Cheap Trick to make sure there is always something


# i18n['']

if __name__ == "__main__":
    print("This file is not meant to be executed, it was a stop gap measure in the first place.")
