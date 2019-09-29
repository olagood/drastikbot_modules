#!/usr/bin/env python3
# coding=utf-8

# SYSTEM MODULE
#
# TheGrid: Bot Administration Module for drastikbot
#
# NOTES:
#     * You might want to change the command for this module so that it will be
#       harder to guess.
#         * The variables are: self.commands in Module(): , c in main():
#     * The first time the module will be loaded, the bot owner must register
#       with .grid register <PASS>
#
# DEPENDENCIES:
#     * passlib :: pip3 install passlib
#         * argon2_cffi :: pip3 install argon2_cffi

'''
Copyright (C) 2018-2019 drastik.org


This file is part of drastikbot.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, version 3 only.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from dbot_tools import Config
from user_auth import user_auth


class Module:
    def __init__(self):
        self.commands = ["join", "part", "privmsg", "notice"]


# --- Settings --- #
user_modes = ['~', '&', '@', '%']
####################


# Permission Checks
def is_bot_owner(irc, nickname):
    if nickname in irc.var.owners:
        return True
    else:
        return False


def is_channel_mod(irc, nickname, channel):
    try:
        for m in irc.var.namesdict[channel][1][nickname]:
            if m in user_modes:
                return True
        return False
    except Exception:
        return False


def is_allowed(i, irc, nickname, channel=""):
    if is_bot_owner(irc, nickname):
        if user_auth(i, irc, i.nickname):
            return True
        elif channel and is_channel_mod(irc, nickname, channel):
            return True
        else:
            return False
    elif channel and is_channel_mod(irc, nickname, channel):
        return True
    else:
        return False


# Channel Management
def _join(irc, channel, password=""):
    chan_dict = {channel: password}
    conf_r = Config(irc.cd).read()
    conf_r['irc']['channels']['join'][channel] = password
    Config(irc.cd).write(conf_r)
    irc.var.config_load()
    irc.join(chan_dict)


def _part(irc, channel, message=""):
    conf_r = Config(irc.cd).read()
    if channel not in conf_r['irc']['channels']['join']:
        return False
    del conf_r['irc']['channels']['join'][channel]
    Config(irc.cd).write(conf_r)
    irc.var.config_load()
    irc.part(channel, message)
    return True


# Announcements
def _privmsg(irc, receiver, message):
    irc.privmsg(receiver, message)


def _notice(irc, receiver, message):
    irc.notice(receiver, message)


# User ACL
def _user_acl_add(irc, mask):
    c = Config(irc.cd).read()
    if mask in c['irc']['user_acl']:
        return False  # The mask already exists
    c['irc']['user_acl'].append(mask)
    Config(irc.cd).write(c)
    irc.var.config_load()
    return True


def _user_acl_delete(irc, mask):
    c = Config(irc.cd).read()
    if mask in c['irc']['user_acl']:
        c['irc']['user_acl'].remove(mask)
        Config(irc.cd).write(c)
        irc.var.config_load()
        return True
    else:
        return False  # This mask doesn't exist


def _user_acl_list(irc, nickname):
    for i in irc.var.user_acl:
        irc.privmsg(nickname, i)


# Module Management
def _module_import(i, irc):
    i.mod_import()
    irc.privmsg(i.nickname, '\x0303New module were imported.')


def _module_wb_list_add(i, irc, module, channel, mode):
    if mode == "whitelist":
        edom = "blacklist"
    elif mode == "blacklist":
        edom = "whitelist"
    else:
        raise ValueError("'mode' can only be 'whitelist' or 'blacklist'.")

    c = Config(irc.cd).read()
    ls = c["irc"]["modules"][mode]

    if module not in i.modules:
        return 1  # This module is not loaded
    elif module in c["irc"]["modules"][edom]:
        return 2  # This module has a blacklist set
    elif module not in ls:
        ls.update({module: []})
    elif channel in ls[module]:
        return 3  # This channel has already been added.

    ls[module].append(channel)
    Config(irc.cd).write(c)
    irc.var.config_load()
    return 0


def _module_wb_list_delete(irc, module, channel, mode):
    if mode != "whitelist" and mode != "blacklist":
        raise ValueError("'mode' can only be 'whitelist' or 'blacklist'.")

    c = Config(irc.cd).read()
    ls = c["irc"]["modules"][mode]
    if channel in ls:
        ls.remove(channel)
        Config(irc.cd).write(c)
        irc.var.config_load()
        return True
    else:
        return False  # This channel has not been added.


def _module_wb_list_list(i, irc, channel, list_all=False):
    c = Config(irc.cd).read()
    wl = c["irc"]["modules"]["whitelist"]
    bl = c["irc"]["modules"]["blacklist"]

    wl_message = "\x0301,00WHITELIST\x0F :"
    if not list_all:
        wl_message += f" {channel} :"
    for module in wl:
        if list_all:
            wl_message += f" {module}: {wl['module']} /"
        else:
            if channel in wl[module]:
                wl_message += F" {module} /"

    bl_message = "\x0300,01BLACKLIST\x0F :"
    if not list_all:
        bl_message += f" {channel} :"
    for module in bl:
        if list_all:
            bl_message += f" {module}: {wl['module']} /"
        else:
            if channel in wl[module]:
                bl_message += F" {module} /"

    irc.privmsg(i.nickname, wl_message)
    irc.privmsg(i.nickname, bl_message)


def _module_global_prefix_set(irc, prefix):
    c = Config(irc.cd).read()
    c['irc']['modules']['global_prefix'] = prefix
    Config(irc.cd).write(c)
    irc.var.config_load()


def _module_channel_prefix_set(irc, channel, prefix):
    c = Config(irc.cd).read()
    c['irc']['modules']['channel_prefix'][channel] = prefix
    Config(irc.cd).write(c)
    irc.var.config_load()


# User Interface
def join(i, irc):
    if not is_allowed(i, irc, i.nickname):
        return

    if not i.msg_nocmd:
        irc.notice(i.nickname,
                   f"Usage: {i.cmd_prefix}join <channel> [password]")

    args = i.msg_nocmd.split(" ", 1)
    channel = args[0]
    password = args[1]
    _join(irc, channel, password)


def part(i, irc):
    args = i.msg_nocmd.split(" ", 1)
    channel = args[0]
    message = args[1]
    if not is_allowed(i, irc, i.nickname, channel):
        return

    _part(irc, channel, message)


def main(i, irc):
    func_d = {
        "join": join,
        "part": part
    }
    func_d[i.cmd]
