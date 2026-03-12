__version__ = '0.2.3'
__author__ = "Bruno DeVries"
__license__ = "GPL-3"
__appname__ = "episode_names"
__appauthor__ = "BurnoutDV" # my preferred name so to speak
__folder_version__ = "1.1-dev" # in case of breaking changes, change this

__previous_db_versions__ = ['1.0', '1.1'] # ? maybe enrich these with information about the deltas
"""
# Patch Notes
## 0.0.3
* Initial, first use able build
* no project creation menu, only episodes copy
* rough database design
## 0.0.4
* added template menu
* changed database pattern, added create/edit for all
## 0.0.5
* project menu
* change to textual 0.86.1 for theming
* tags aren now derived from template
* autocomplete field for projects names -> external dependency
* added dynamic palette commands because i can
* some restyling which is mighty inconsistent now with the rest of the interface
## 0.0.6
* changed project structure a bit to be _more_ proper python?
## 0.0.7
* Project Creation / Edit Menu overhaul
* Notes on Episodes now work
* Project Delete
## 0.1.0
* Settings Page
* Export to Markdown Button
* Im/Export from json (no check, might go horribly wrong)
* Episode Notes
* Update to Textual 3.0.0, textual-autocomplete 4.0.4
* new dependency textual-fspicker
## 0.2.x
Bigger Update to add some features I dreamed up in 6 Months
* additional Columns for Episodes: alt_title, alt_title2, yt_link, description
* additional Column for Playlist: description
* added notes for Projects
* added foundations for youtube link
* added "additional description", mostly for time markers
* updated export function
* design overhaul 
* different setting screen
## 0.2.4
* Dialogue for Previous Versions
* Additional 'Note' entries in the DataTable to show all the informations that might be present
"""
