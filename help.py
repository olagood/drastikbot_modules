# coding=utf-8

# Help Module for drastikbot modules.
#
# This module provides help messages for the loaded drastikbot modules.
#
# Usage
# -----
# Calling the command without arguments returns a list of all the
# loaded modules with help information.  Example: .help
#
# Giving the name of a module as an argument returns the available
# bot_commands of that module.  Example: .help text
#
# Giving the name of a module followed by one of its bot_commands
# returns a help message of that command:  Example: .help text ae
#
# API
# ---
# To  provide help  messages through  this module  other modules  must
# include  the manual  variable  in  their Module  class.  If no  such
# variable is provided or if there is no Module class the  module will
# be unlisted.


# Copyright (C) 2021 drastik.org
#
# This file is part of drastikbot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from irc.modules import get_object_from_name


class Module:
    bot_commands = ["help"]


# ====================================================================
# Module checks
# ====================================================================

def is_hidden(module_object):
    """Is ``module'' a hidden module?"""
    try:
        return module_object.Module.manual == "hidden"
    except AttributeError:
        # No module class
        # No manual entry
        return True


def is_allowed(i, module_object):
    msgtarget = i.msg.get_msgtarget()
    name = i.bot["modules"]["modules_d"][module_object].stem
    conf = i.bot["conf"]

    return not is_hidden(module_object)\
        and not conf.has_channel_module_blacklist(name, msgtarget) \
        and not conf.has_channel_module_whitelist(name, msgtarget)


def check_then_get_module_class(i, irc, module_name):
    msgtarget = i.msg.get_msgtarget()

    modules = i.bot["modules"]
    conf = i.bot["conf"]

    try:
        module_c = get_object_from_name(modules, module_name).Module
    except AttributeError:
        m = f"Help: `{module_name}' has not been loaded."
        irc.out.notice(msgtarget, m)
        return False

    if conf.has_channel_module_blacklist(module_name, msgtarget):
        m = "Help: This module has been disabled."
        irc.out.notice(msgtarget, m)
        return False

    if conf.has_channel_module_whitelist(module_name, msgtarget):
        m = "Help: This module has been disabled."
        irc.out.notice(msgtarget, m)
        return False

    if not hasattr(module_c, "manual"):
        m = "Help: This module does not have a manual."
        irc.out.notice(msgtarget, m)
        return False

    return module_c


# ====================================================================
# Help functions
# ====================================================================

def module_help(i, irc, module_name):
    msgtarget = i.msg.get_msgtarget()
    prefix = i.msg.get_botcmd_prefix()

    module_c = check_then_get_module_class(i, irc, module_name)

    if not module_c:
        return

    commands = ""
    if hasattr(module_c, "bot_commands"):
        commands = ", ".join(module_c.bot_commands)
        commands = f"Commands: {commands} | "

    info = ""
    if "desc" in module_c.manual:
        info = module_c.manual["desc"]
        info = f"Info: {info}"

    t = f"\x0311{module_name}\x0F: {commands}{info}"
    t += f" | Use: {prefix}help <module> <command> for command info."

    irc.out.notice(msgtarget, t)


def command_help(i, irc, module_name, command):
    msgtarget = i.msg.get_msgtarget()
    prefix = i.msg.get_botcmd_prefix()

    module_c = check_then_get_module_class(i, irc, module_name)

    if not module_c:
        return

    if not hasattr(module_c, "bot_commands"):
        m = "Help: This module does not provide commands."
        irc.out.notice(msgtarget, m)
        return

    if "bot_commands" not in module_c.manual:
        m = "Help: No manual entry for this command."
        irc.out.notice(msgtarget, m)
        return

    command_manual = module_c.manual["bot_commands"]

    if command not in command_manual:
        m = "Help: No manual entry for this command."
        irc.out.notice(msgtarget, m)
        return

    command_entry = command_manual[command]

    t = []

    if "usage" in command_entry:
        usage = command_entry["usage"](prefix)
        usage = f"Usage: {usage}"
        t.append(usage)

    if "info" in command_entry:
        info = command_entry["info"]
        info = f"Info: {info}"
        t.append(info)

    if "alias" in command_entry:
        alias = ", ".join(command_entry["alias"])
        alias = f"Aliases: {alias}"
        t.append(alias)

    t = " | ".join(t)
    t = f"{command}: {t}"

    irc.out.notice(msgtarget, t)


def module_list(i, irc):
    msgtarget = i.msg.get_msgtarget()
    prefix = i.msg.get_botcmd_prefix()

    s = i.bot["modules"]

    m = filter(lambda x: is_allowed(i, x), s["modules_d"].keys())
    m = map(lambda x: s["modules_d"][x].stem, m)

    m = "Help: " + ", ".join(sorted(m))
    m += f" | Use: {prefix}help <module> for module info."

    irc.out.notice(msgtarget, m)


# ====================================================================
# Main
# ====================================================================

def main(i, irc):
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if not args:
        module_list(i, irc)
        return

    argv = args.split()
    argc = len(argv)

    if argc == 1:  # Module help
        module_help(i, irc, argv[0])
    elif argc == 2:  # Command help
        command_help(i, irc, argv[0], argv[1])
    else:
        m = f"Usage: {prefix}help [module] [command]"
        irc.out.notice(i.channel, m)
