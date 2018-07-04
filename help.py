#!/usr/bin/env python3
# coding=utf-8

# Help Module for Drastikbot

'''
Copyright (C) 2018 drastik.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


class Module:
    def __init__(self):
        self.commands = ['help']


def _hidden_module(i, module):
    """
    Check if the 'module' is hidden.
    Hidden modules must set self.helpmsg = ["__hidden__"] in their Module()
    class.
    If a module still wants to provide help through this module but just not
    be listed with the .help command "__hidden__" sould be the first string in
    their 'helpmsg' list.
    Return:
        True if the module does not have a 'helpmsg' attribute.
        False if the module has a 'helpmsg' attribute.
    """
    try:
        i.modules[module].Module().helpmsg
        return False
    except AttributeError:
        return True


def module_help(i, irc, module):
    try:
        blacklist = ', '.join(irc.var.modules_obj[
            'settings'][module]['blacklist'])
    except KeyError:
        irc.privmsg(i.nickname, f'Help: "{module}" is not an imported module.')
        return
    if blacklist:
        blacklist = f"  \x0312blacklisted\x0F: {blacklist}"
    else:
        blacklist = ""

    try:
        whitelist = ', '.join(irc.var.modules_obj[
            'settings'][module]['whitelist'])
    except KeyError:
        irc.privmsg(i.nickname, f'Help: "{module}" is not an imported module.')
        return
    if whitelist:
        whitelist = f"  \x0312whitelisted\x0F: {whitelist}"
    else:
        whitelist = ""

    try:
        # Make a copy of the module's help message.
        helpmsg = i.modules[module].Module().helpmsg[:]
    except AttributeError:
        irc.privmsg(i.nickname,
                    'Help: No help message was found for this module.')
        return

    try:
        commands = '\x0F, \x0303'.join(i.modules[module].Module().commands)
        commands = f"\x0303{commands}"
    except AttributeError:
        commands = ""

    static_output_list = [f"\x0311{module}\x0F: {commands}", blacklist,
                          whitelist]
    output_list = []
    for line in helpmsg:
        output_list.append(line)

    for line in static_output_list:
        irc.privmsg(i.nickname, line)

    for line in output_list:
        line = f"  {line}"
        irc.privmsg(i.nickname, line)


def command_list(i, irc):
    module_dict = {}
    for command, module in i.command_dict.items():
        if _hidden_module(i, module):
            continue
        if i.blacklist(module, i.channel):
            continue
        if not i.whitelist(module, i.channel):
            continue
        # Make a dictionary of {module: values} to removed duplicate module
        # references that exist in 'command_dict'
        try:
            module_dict[module].append(command)
        except KeyError:
            module_dict[module] = [command]

    text = "Help: "
    # Command based modules
    for module, cmd_ls in module_dict.items():
        text += f"\x0311{module}\x0F: {', '.join(cmd_ls)} | "
    # Automatic modules
    for module in i.auto_list:
        if _hidden_module(i, module):
            continue
        if i.blacklist(module, i.channel):
            continue
        if not i.whitelist(module, i.channel):
            continue
        if module not in module_dict:
            text += f"\x0311{module}\x0F | "

    text += f"Use: {i.cmd_prefix}help [Module] for detailed information."
    return text


def main(i, irc):
    if i.msg_nocmd:
        args = i.msg_nocmd.split()
        module_help(i, irc, args[0])
    else:
        irc.privmsg(i.channel, command_list(i, irc))
