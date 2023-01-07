#!/usr/bin/python3

# MIT License
#
# Copyright (c) 2017 Marcel de Vries
# Copyright (c) 2023 Christopher Suttles
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

## Script has been modified to for updating mods and server installed using LGSM for Post Scriptum found here: https://linuxgsm.com/servers/pstbsserver/
## Make sure to create a user called "psserver" and install the game using LGSM to "/home/psserver". 
## After that just add your modIDs for workshop mods to line 53 and the script will handle the rest each time it is called.
## You have to manually remove mods you don't want anymore.

import os
import os.path
import re
import shutil
import time

from datetime import datetime
from urllib import request

# region Configuration
STEAM_CMD = "/home/psserver/.steam/steamcmd/steamcmd.sh"
STEAM_USER = "anonymous"

PS_SERVER_ID = "746200"
PS_SERVER_DIR = "/home/psserver/serverfiles"
PS_WORKSHOP_ID = "736220"

PS_WORKSHOP_DIR = "{}/steamapps/workshop/content/{}".format(PS_SERVER_DIR, PS_WORKSHOP_ID)
PS_MODS_DIR = "/home/psserver/serverfiles/PostScriptum/Plugins/Mods"

MODPACK_NAME = "[Pibbz] Post Scriptum Server Modlist"
MODPACK_PATH = "/home/psserver/Pibbz Post Scriptum Server Modlist.html"
MODS = {
    "vehicle_armor_training":       "2329787052",
    "psrm":                         "2329787052",
    "psrm_custom_maps":             "2832715076",
    "project_variety":              "2724056597",
    "longues_sur_mer":              "2477584168",
    "ge_siegfried_line":            "2766698808",
    "ge_battle_of_overloon":        "2529532049",
    "creully":                      "2825158852",
    "cagny":                        "2684041969",
    "etreham":                      "2617682055",
    "targnon_363vd":                "2723033451",
    "ob_mont_pincon":               "2313344943",
    "sainte_marie_du_mont":         "2412134525",
    "ob_mont_pincon":               "2313344943",
    "simonskall":                   "2899813903",
    "gh: bastogne":                 "2886181766",
    "gh: dunkirk":                  "2827466692",
    "houlgate":                     "2646717496",
    "saint-lo":                     "2845368691",
    "villersbocage":                "2569424945",
    "cr_op_deadstick":              "2576634813",
    "ne_core":                      "2455406986",
    "ramelle":                      "2387944294",
    "simonskall":                   "2382579481"
}
# Only mod names go here, server/optional mods also need to be listed in MODS
SERVER_MODS = {
    ""
}
OPTIONAL_MODS = {
    ""
}

DLC = {
}
UPDATE_PATTERN = re.compile(r"workshopAnnouncement.*?<p id=\"(\d+)\">", re.DOTALL)
TITLE_PATTERN = re.compile(r"(?<=<div class=\"workshopItemTitle\">)(.*?)(?=<\/div>)", re.DOTALL)
WORKSHOP_CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog"


# endregion

# region Functions
def log(msg):
    print("")
    print("{{0:=<{}}}".format(len(msg)).format(""))
    print(msg)
    print("{{0:=<{}}}".format(len(msg)).format(""))


def call_steamcmd(params):
    os.system("{} {}".format(STEAM_CMD, params))
    print("")


def update_server():
    steam_cmd_params = " +force_install_dir {}".format(PS_SERVER_DIR)
    steam_cmd_params += " +login {} ".format(STEAM_USER)
    steam_cmd_params += " +app_update {}".format(PS_SERVER_ID)
    steam_cmd_params += " +quit"

    call_steamcmd(steam_cmd_params)


def mod_needs_update(mod_id, path):
    if os.path.isdir(path):
        response = request.urlopen("{}/{}".format(WORKSHOP_CHANGELOG_URL, mod_id)).read()
        response = response.decode("utf-8")
        match = UPDATE_PATTERN.search(response)

        if match:
            updated_at = datetime.fromtimestamp(int(match.group(1)))
            created_at = datetime.fromtimestamp(os.path.getctime(path))

            return updated_at >= created_at

    return False


def update_mods():
    for mod_name, mod_id in MODS.items():
        path = "{}/{}".format(PS_WORKSHOP_DIR, mod_id)

        # Check if mod needs to be updated
        if os.path.isdir(path):

            if mod_needs_update(mod_id, path):
                # Delete existing folder so that we can verify whether the
                # download succeeded
                shutil.rmtree(path)
            else:
                print("No update required for \"{}\" ({})... SKIPPING".format(mod_name, mod_id))
                continue

        # Keep trying until the download actually succeeded
        tries = 0
        while os.path.isdir(path) is False and tries < 10:
            log("Updating \"{}\" ({}) | {}".format(mod_name, mod_id, tries + 1))

            steam_cmd_params = " +force_install_dir {}".format(PS_SERVER_DIR)
            steam_cmd_params += " +login {} ".format(STEAM_USER)
            steam_cmd_params += " +workshop_download_item {} {} validate".format(
                PS_WORKSHOP_ID,
                mod_id
            )
            steam_cmd_params += " +quit"

            call_steamcmd(steam_cmd_params)

            # Sleep for a bit so that we can kill the script if needed
            time.sleep(5)

            tries = tries + 1

        if tries >= 10:
            log("!! Updating {} failed after {} tries !!".format(mod_name, tries))


def lowercase_workshop_dir():
    def rename_all(root, items):
        for name in items:
            try:
                os.rename(os.path.join(root, name), os.path.join(root, name.lower()))
            except OSError:
                pass
    for root, dirs, files in os.walk(PS_WORKSHOP_DIR, topdown=False):
        rename_all(root, dirs)
        rename_all(root, files)

def create_mod_symlinks():
    for mod_name, mod_id in MODS.items():
        link_path = "{}/{}".format(PS_MODS_DIR, mod_name)
        real_path = "{}/{}".format(PS_WORKSHOP_DIR, mod_id)

        if os.path.isdir(real_path):
            if not os.path.islink(link_path):
                os.symlink(real_path, link_path)
                print("Creating symlink '{}'...".format(link_path))
        else:
            print("Mod '{}' does not exist! ({})".format(mod_name, real_path))


key_regex = re.compile(r'(key).*', re.I)


def generate_preset():
    f = open(MODPACK_PATH, "w")
    f.write(('<?xml version="1.0" encoding="utf-8"?>\n'
             '<html>\n\n'
             '<!--Created using a3update.py: https://gist.github.com/Freddo3000/a5cd0494f649db75e43611122c9c3f15-->\n'
             '<head>\n'
             '<meta name="arma:Type" content="{}" />\n'
             '<meta name="arma:PresetName" content="{}" />\n'
             '<meta name="generator" content="update.py https://github.com/khaosmaou/arma3server/blob/main/update.py"/>\n'
             ' <title>Post Scriptum</title>\n'
             '<link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet" type="text/css" />\n'
             '<style>\n'
             'body {{\n'
             'margin: 0;\n'
             'padding: 0;\n'
             'color: #fff;\n'
             'background: #000;\n'
             '}}\n'
             'body, th, td {{\n'
             'font: 95%/1.3 Roboto, Segoe UI, Tahoma, Arial, Helvetica, sans-serif;\n'
             '}}\n'
             'td {{\n'
             'padding: 3px 30px 3px 0;\n'
             '}}\n'
             'h1 {{\n'
             'padding: 20px 20px 0 20px;\n'
             'color: white;\n'
             'font-weight: 200;\n'
             'font-family: segoe ui;\n'
             'font-size: 3em;\n'
             'margin: 0;\n'
             '}}\n'
             'h2 {{'
             'color: white;'
             'padding: 20px 20px 0 20px;'
             'margin: 0;'
             '}}'
             'em {{\n'
             'font-variant: italic;\n'
             'color:silver;\n'
             '}}\n'
             '.before-list {{\n'
             'padding: 5px 20px 10px 20px;\n'
             '}}\n'
             '.mod-list {{\n'
             'background: #282828;\n'
             'padding: 20px;\n'
             '}}\n'
             '.optional-list {{\n'
             'background: #222222;\n'
             'padding: 20px;\n'
             '}}\n'
             '.dlc-list {{\n'
             'background: #222222;\n'
             'padding: 20px;\n'
             '}}\n'
             '.footer {{\n'
             'padding: 20px;\n'
             'color:gray;\n'
             '}}\n'
             '.whups {{\n'
             'color:gray;\n'
             '}}\n'
             'a {{\n'
             'color: #D18F21;\n'
             'text-decoration: underline;\n'
             '}}\n'
             'a:hover {{\n'
             'color:#F1AF41;\n'
             'text-decoration: none;\n'
             '}}\n'
             '.from-steam {{\n'
             'color: #449EBD;\n'
             '}}\n'
             '.from-local {{\n'
             'color: gray;\n'
             '}}\n'
             ).format("Modpack", MODPACK_NAME))

    f.write(('</style>\n'
             '</head>\n'
             '<body>\n'
             '<h1>Arma 3  - {} <strong>{}</strong></h1>\n'
             '<p class="before-list">\n'
             '<em>This does not work, it was for Arma 3, ignore draging this anywhere... / Preset / Import.</em>\n'
             '</p>\n'
             '<h2 class="list-heading">Required Mods</h2>'
             '<div class="mod-list">\n'
             '<table>\n'
             ).format("Modpack", MODPACK_NAME))

    for mod_name, mod_id in MODS.items():
        if not (mod_name in OPTIONAL_MODS or mod_name in SERVER_MODS):
            mod_url = "http://steamcommunity.com/sharedfiles/filedetails/?id={}".format(mod_id)
            response = request.urlopen(mod_url).read()
            response = response.decode("utf-8")
            match = TITLE_PATTERN.search(response)
            if match:
                mod_title = match.group(1)
                f.write(('<tr data-type="ModContainer">\n'
                         '<td data-type="DisplayName">{}</td>\n'
                         '<td>\n'
                         '<span class="from-steam">Steam</span>\n'
                         '</td>\n'
                         '<td>\n'
                         '<a href="{}" data-type="Link">{}</a>\n'
                         '</td>\n'
                         '</tr>\n'
                         ).format(mod_title, mod_url, mod_url))
    f.write('</table>\n'
            '</div>\n'
            '<h2 class="list-heading">Optional Mods</h2>'
            '<div class="optional-list">\n'
            '<table>\n'
            )

    for mod_name, mod_id in MODS.items():
        if mod_name in OPTIONAL_MODS:
            mod_url = "http://steamcommunity.com/sharedfiles/filedetails/?id={}".format(mod_id)
            response = request.urlopen(mod_url).read()
            response = response.decode("utf-8")
            match = TITLE_PATTERN.search(response)
            if match:
                mod_title = match.group(1)
                f.write(('<tr data-type="OptionalContainer">\n'
                         '<td data-type="DisplayName">{}</td>\n'
                         '<td>\n'
                         '<span class="from-steam">Steam</span>\n'
                         '</td>\n'
                         '<td>\n'
                         '<a href="{}" data-type="Link">{}</a>\n'
                         '</td>\n'
                         '</tr>\n'
                         ).format(mod_title, mod_url, mod_url))
    f.write('</table>\n'
            '</div>\n'
            '<h2 class="list-heading">DLC</h2>\n'
            '<div class="dlc-list">\n'
            '<table>\n'
            )
    for dlc_name, mod_id in DLC.items():
        mod_url = "https://store.steampowered.com/app/{}".format(mod_id)
        f.write(('<tr data-type="DlcContainer">\n'
                 '<td data-type="DisplayName">{}</td>\n'
                 '<td>\n'
                 '<a href="{}" data-type="Link">{}</a>\n'
                 '</td>\n'
                 '</tr>\n'
                 ).format(dlc_name, mod_url, mod_url))
    f.write('</table>\n'
            '</div>\n'
            '<div class="footer">\n'
            '<span>Created using a3update.py by marceldev89; forked by Freddo3000.</span>\n'
            '</div>\n'
            '</body>\n'
            '</html>\n'
            )

def print_launch_params():
    rel_path = os.path.relpath(PS_MODS_DIR, PS_SERVER_DIR)
    params = "Copy this for launch params:  "
    for mod_name, mod_id in MODS.items():
        params += "{}/{}\;".format(rel_path, mod_name)

    print(params)

# endregion

log("Updating Post Scriptum server ({})".format(PS_SERVER_ID))
update_server()

log("Updating mods")
update_mods()

log("Converting uppercase files/folders to lowercase...")
lowercase_workshop_dir()

log("Creating symlinks... ")
create_mod_symlinks()

log("Generating modpack .html file...")
generate_preset()

log("Printing launch params...")
print_launch_params()

log("Done!")
