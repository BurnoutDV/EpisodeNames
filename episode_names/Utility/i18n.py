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

from rich.text import Text

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    filename="i18n.log")

class LanguageArchive(dict):
    color_map: dict|None = None # map of colors for Rich Theme texts
    # TODO: look up how python works, this is global when i change it for the class?

    def __init__(self, seq=None, **kwargs):  # known special case of dict.__init__
        """
        dict() -> new empty dictionary
        dict(mapping) -> new dictionary initialized from a mapping object's
            (key, value) pairs
        dict(iterable) -> new dictionary initialized as if via:
            d = {}
            for k, v in iterable:
                d[k] = v
        dict(**kwargs) -> new dictionary initialized with the name=value pairs
            in the keyword argument list.  For example:  dict(one=1, two=2)
        # (copied from class doc)
        """
        self.combo_template: dict|None = None
        super().__init__(seq, **kwargs)

    def __getitem__(self, item):
        if not item in self:
            logging.warning(f"Unknown token '{item}'")
            return f"F:{item}"
        return super().get(item)

    def r(self, item: str, style: str) -> Text:
        """
        Uses rich Text to enrich a given translation text.

        Mostly used for color.
        :param item:
        :return:
        """
        if not item in self:
            logging.warning(f"Unknown token '{item}'")
            return Text(f"F:{item}")
        return Text(super().get(item), style)

    def c(self, combo_template) -> str | Text:
        """
        Combines two entries with the combo_template
        :param combo_template:
        :return:
        """
        # ? all this only to get colored titles for some tooltip :/
        if not combo_template in self.combo_template:
            logging.warning(f"Unknown combo template '{combo_template}'")
            return Text(f"F:{combo_template}")
        # TODO: finish this, its more than I expected tbh.

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
    'Discard': "Discard",
    'Tags': "Tags",
    'Current': "Current",
    'Category': "Category",
    'dateformat': "Dateformat",
    'Style': "Style",
    'Backup': "Backup",
    'Projects': "Projects",

    'Entry Group': "Edit, Create, Assign a Template to Entry",
    'CopyPaste Group': "Copy templated, markdown or tags",
    'Notes Group': "Write Notes, Description, Addon Descriptions",
    'Create New': "Create New",
    'Create MD': "Create MD",
    'Toogle Help': "Toogle Help",
    'New Entry': "New Episode Entry",
    'New Entry Tooltip': "Creates a new entry, if there are any other Episodes in this project it starts with date, session, record date prefilled and counter1&2 pre-incremented.",
    'Edit Entry': "Edit Episode Entry",
    'Edit Entry Tooltip': "Opens the edit entry menu, either [enter] as [e] will work as shortcut.",
    'Copy Tags': "Copy Tags",
    'Copy Tags Tooltip': "Copies the tags from the assigned Template to the clipboard as comma-separated list (like youtube takes it).\nNote, tags are assigned by template, not to individual episodes.",
    'Copy Text': "Copy Text according to Template",
    'Copy2Md': "Copies Text to markdown templating",
    'Copy Text MD Tooltip': "Copies the text according to the assigned template and THEN uses a fixed mark down template.",
    'Copy Text Tooltip': "Puts the currently selected entry into the clipboard by using the assigned templating for the text transformation. See [F2] for templates.",
    'Assign Template': "Template",
    'Assign Template Tooltip': "Opens the 'assign template' dialogue for the currently selected episode entry.",
    'Episode Note': "Episode Notes",
    'Episode Note Tooltip': "Writes a 'show note' for this Episode that does not appear anywhere in the template for your personal reference.\nThe 'All Notes' tab above lists all episodes notes in one view.",
    'Project notes': "Project notes",
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
    'Description': "Description",
    'Description Tooltip': "A short cut menu to directly write the description the selected episode.\nThe same functionality is available in the 'edit episode' menu.",
    'Description Addon': "Description Addon",
    'Description Addon Tooltip': "A short cut menu to directly write the description addon for the selected episode.\nThe same functionality is available in the 'edit episode' menu.\nA description addon is basically 'description2' that can be placed elsewhere in the template. It was created to easily realise chapter markers without accessing the actual description.",


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
    'The Settings Screen': "The Settings Screen",
    'Project Notes': "Project Notes",
    'Episode Notes Summary': "Episode Notes Summary",
    'All Notes': "All Notes",
    'Project Notes Summary': "Project Notes Summary",
    'Placeholder Variables': "Placeholder Variables",
    'there is no project note, yet': "There is no project note, yet..",
    'Enter Filter here': "Enter Filter here",
    'Duplicate Current': "Duplicate Current",
    'Database2JSON Import': "Database2JSON Import",
    'Database2JSON Export': "Database2JSON Export",
    'Delete old data': "Delete old data",
    'Copy of': "Copy of",
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
    'app: app: Debug Command': "app: Debug Command",
    'Project does not contain episodes': "Project does not contain episodes",
    'Does whatever the current debug command does': "Does whatever the current debug command does",
    'Thanks for choosing EpisodeNames': "Thanks for choosing EpisodeNames",
    'warning_delete_current_data': "Importing a new set of data will delete all current data including settings",
    'Data has changed, you really want to abort?': "Data has changed, you really want to abort?",
    'Quit episode_names and return to the command line': 'Quit episode_names and return to the command line',
    'Confirm that this was read': 'Confirm that this was read',
    'Old_Version_blues': "# Older Database Files detected\n\nUpon occassion a revision of the internal database is necessary. Likely due a recent update the current one has changed, *episode_names* detected older files for the version(s): %%versions%%.\n\nIf the data you are used to is not present this is most likely the reason for that.\n\n## What to do?\n\n*There is no need to panic*\n\nNo data was lost. You just have to revert back to the old version/release, and then export all the data in the setting menu, **then** you update again and import again. \n\n This *should* always work.",
    'missing_settings_general': "# Missing Settings\n\nThis screen connects with an external source, some settings like that its always YouTube are already hard coded, but some additional setup is necessary to properly use this function.\nCurrently the following things are missing:\n",
    'missing_yt_api': "* **Youtube API Key**, not the fancy kind where you need to do an OAuth2 Setup but a more basic one that is just used to retrieve data, a one way street. This tool is self contained and is not capable of external change, that is all up to you. You find the key in ... *some better instructions here Alan*\n",
    'missing_channel_id': "* A **Channel ID** so *episode_names* actually knows from which channel to fetch playlists and video data. *Note that* episode_names *does not support multiple channels in the current moment, if the need arises there is only the possibility of using multiple instances*\n\n The **Channel ID** usually can be found in the URL when you view a channel, it should be around *24* characters long\n",
    'missing_settings_tail': "## What to do now?\n\nFirst of all, *dont panic*.\n\nSecond, go to the settings menu (*F3*) and enter the strings needed.\n\n*Note that at that point no check of validity will be done, you will know if everything is in working order when you fetch all playlists for the first time.*\n\nIf the entered data does not work *episode_names* will reset the corresponding setting.\n\n*Also note, the API key will never be part of an export, if you come from an older database revision you need to reenter it again.*",

    'tooltip_datetime': "strftime is at use.\n%d day of month, zero padded\n%m Month, zero padded\n%y Year, no century, zero padded\n%Y Year with century\n%H Hours, zero padded\n%M Minute, zero padded\n%S Seconds, zero padded\n%f Microsecond",

    'combo_words': "%%number%% words",
    'combo_chars': "%%number%% chars"
}) # Cheap Trick to make sure there is always something
i18n.combo_template = {
    'New Entry': {
        1: 'New Entry',
        2: 'Edit Entry Tooltip',
        't': "%%item1\n%%item2",
        'r': ['bold $$accent$$']
    }
}

# i18n['']

if __name__ == "__main__":
    print("This file is not meant to be executed, it was a stop gap measure in the first place.")
