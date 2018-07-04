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

import time
import json
from passlib.hash import argon2
from dbot_tools import Config


class Module:
    def __init__(self):
        self.commands = ['grid']


# --- Settings --- #
user_modes = ['~', '&', '@', '%']
####################


class TheGrid:
    def __init__(self, irc, user, command, db, botsys):
        self.conf_r = Config(irc.cd).read()
        self.conf_w = Config(irc.cd).write
        self.owners = irc.var.owners
        self.irc = irc
        self.db = db[1]  # disk database
        self.dbc = self.db.cursor()
        self.botsys = botsys
        self.user = user
        self.cmd = command
        self.admins = {}  # {nickname: ['#channel']}
        self.userdict = {}  # {channel: ['@']}
        for key, val in irc.var.namesdict.items():
            if user in val[1]:
                self.userdict[key] = val[1][user]
        for o in self.owners:
            # Give access to the owners to access ALL channels
            self.admins[o] = ["ALL"]
        self.logged = {}  # Logged in users
        try:
            # get a list of the registered admins
            self.dbc.execute('''SELECT user, access FROM TheGrid''')
            fetch = self.dbc.fetchall()
            for f in fetch:
                if f[0] in self.owners:
                    continue
                self.admins[f[0]] = json.loads(f[1])
        except Exception:
            pass
        try:
            # get a dictionary of the logged in users and the log in time
            self.dbc.execute('''SELECT user, time FROM TheGrid''')
            fetch = self.dbc.fetchall()
            for f in fetch:
                if time.time() - f[1] > 600:
                    try:
                        del self.logged[f[0]]
                    except Exception:
                        pass
                else:
                    self.logged[f[0]] = f[1]
        except Exception:
            pass

    # --- Check permition status --- #
    def perm_owner(self, reg=True):
        if self.user not in self.owners:
            return False
        elif reg and self.user not in self.logged:
            return False
        return True

    def perm_admin(self, channel=False):
        if self.user not in self.admins:
            return False
        elif self.user not in self.logged:
            return False

        if not channel:
            return True
        elif channel in self.admins[self.user]:
            return True
        else:
            return False

    def perm_user(self, channel):
        if self.perm_owner(reg=True):
            return True
        elif self.perm_admin(channel=channel):
            return True
        for m in self.userdict[channel]:
            if m in user_modes:
                return True
        else:
            return False

    # --- Argument Functions --- #
    def arg_len(self, args, equal=False, more=False, less=False):
        argl = len(args)
        if less or more:
            if less and argl < less:
                return False
            if more and argl > more:
                return False
        elif equal:
            if argl != equal:
                return False
        return True

    def cmd_check(self, sec, sec_arg, args, txt,
                  equal=False, more=False, less=False):
        '''
        Function to check if the command given is correct and should be
        executed.

        "sec"   -> "onwer" : perm_owner
                -> "admin" : perm_admin
                -> "user"  : perm_user
        "sec_arg": The arguments to be passed to the "sec" function.
        "args"   : The arguments given to the function.
        "txt"    : The help text that will be sent to the user if they provide
                   a wrong command.
        "equal"  : The number of arguments required by the function.
        "more"   : Do comparison for more arguments. Takes INTEGER.
        "less"   : Do comparison for less arguments. Takes INTEGER.
        '''
        if sec == "owner":
            sec_res = self.perm_owner(sec_arg)
        elif sec == "admin":
            sec_res = self.perm_admin(sec_arg)
        elif sec == "user":
            sec_res = self.perm_user(sec_arg)
        else:
            sec_res = False
        if not sec_res:
            self.irc.privmsg(self.user, "\x0308You are not authorized.")
            return False
        arg_res = self.arg_len(args, equal=equal, more=more, less=less)
        if not arg_res:
            self.irc.privmsg(self.user, f'Usage: {self.cmd} {txt}')
            return False
        return True

    # --- Authentication --- #
    def password_hash(self, password):
        return argon2.hash(password)

    def password_verify(self, password, saved_hash):
        return argon2.verify(password, saved_hash)

    def login(self, args):
        '''
        .grid login <PASSWORD>

        Permition :: admin
        Check if the user is in the database and authenticate them.
        '''
        if self.user not in self.admins:
            return
        if not self.arg_len(args, equal=2):
            return self.irc.privmsg(self.user,
                                    f'Usage: {self.cmd} login <PASSWORD>')
        self.dbc.execute(
            '''SELECT password FROM TheGrid WHERE user=?;''', (self.user,))
        fetch = self.dbc.fetchone()
        if self.password_verify(args[1], fetch[0]):
            self.dbc.execute(
                '''UPDATE TheGrid SET time = strftime('%s', 'now')
                WHERE user=?;''', (self.user,))
            self.db.commit()
            return self.irc.privmsg(self.user, '\x0303You are now logged in.')
        else:
            return self.irc.privmsg(self.user, '\x0304Login incorrect')

    def logout(self, args):
        '''
        .grid logout

        Permition :: admin
        Deauthenticate a user. Remove them from "self.logged" and set their
        database time to 0.
        '''
        if self.user not in self.logged:
            return self.irc.privmsg(self.user, '\x0308You are not logged in.')
        elif len(args) != 1:
            return self.irc.privmsg(self.user, 'Usage: {self.cmd} logout')
        del self.logged[self.user]
        self.dbc.execute('''UPDATE TheGrid SET time = 0 WHERE user=?;''',
                         (self.user,))
        self.db.commit()
        return self.irc.privmsg(self.user, '\x0303You are now logged out.')

    # --- User management --- #
    def register(self, args):
        '''
        .grid register <PASSWORD>

        Permition :: owner (unregistered)
        Register function used to create the database table and the onwers'
        accounts.
        '''
        if not self.cmd_check("owner", False, args, 'register <PASSWORD>',
                              equal=2):
            return
        self.dbc.execute(
            '''CREATE TABLE IF NOT EXISTS TheGrid (user TEXT COLLATE NOCASE
            PRIMARY KEY, password TEXT, access TEXT, time INTEGER);''')
        try:
            self.dbc.execute(
                '''INSERT INTO TheGrid (user, password, access, time)
                VALUES (?, ?, 'ALL', 0);''',
                (self.user, self.password_hash(args[1])))
        except Exception:
            self.irc.privmsg(self.user,
                             '\x0308This nickname is already registered.')
            return
        self.irc.privmsg(self.user, '\x0303Created owner account')
        self.db.commit()

    def password(self, args):
        '''
        .grid password <PASSWORD>

        Permition :: admin
        Change the current user's password.
        '''
        if not self.cmd_check("owner", False, args, 'password <PASSWORD>',
                              equal=2):
            return
        self.dbc.execute('''UPDATE TheGrid SET password=? WHERE user=?;''',
                         (self.password_hash(args[1]), self.user))
        self.db.commit()
        self.irc.privmsg(self.user, '\x0303Password change successful.')

    def user_add(self, args):
        '''
        .grid user add <NICK> <PASSWORD> <CHANNEL1> <CHANNEL2>...

        Permition :: onwer (registered)
        Add admin accounts to the database.
        '''
        if not self.cmd_check("owner", True, args, 'user add <NICK> '
                              '<PASSWORD> <CHANNEL1> <channel2>...', less=5):
            return
        nick = args[2]
        password = args[3]
        c = " ".join(args).split(' ', 4)[4].split()
        channels = json.dumps(c)
        self.dbc.execute(
            '''INSERT INTO TheGrid (user, password, access, time)
            VALUES (?, ?, ?, 0);''',
            (nick, self.password_hash(password), channels))
        self.db.commit()
        self.irc.privmsg(self.user,
                         f'\x0303Added user: {nick} with permitions for: {c}')

    def user_rm(self, args):
        '''
        .grid user rm <USER>

        Permition :: owner (registered)
        Remove admin accounts from the database.
        '''
        if not self.cmd_check("owner", True, args, 'user rm <USER>', equal=3):
            return
        self.dbc.execute('''DELETE FROM TheGrid WHERE user=?;''', (args[2],))
        self.db.commit()
        self.irc.privmsg(self.user, f'Deleted user: {args[2]}')

    def user_pass(self, args):
        '''
        .grid user password <USER> <PASSWORD>

        Permition :: owner (registered)
        Change the specified user's password.
        '''
        if not self.cmd_check("owner", True, args, 'user password <USER> '
                              '<PASSWORD>', equal=4):
            return
        self.dbc.execute('''UPDATE TheGrid SET password=? WHERE user=?;''',
                         (self.password_hash(args[3]), args[2]))
        self.db.commit()
        self.irc.privmsg(self.user,
                         f'\x0303Password update for {args[2]} successful')

    def user_chan_add(self, args):
        '''
        .grid user channel add <USER> <CHANNEL>

        Permition :: owner (registered)
        Add a channel to the specified user's access list.
        '''
        if not self.cmd_check("owner", True, args, 'user channel add <USER> '
                              '<CHANNEL>', equal=5):
            return
        user = args[2]
        channel = args[3]
        self.dbc.execute(
            '''SELECT access FROM TheGrid WHERE user=?;''', (user,))
        fetch = json.loads(self.dbc.fetchone()[0])
        fetch.append(channel)
        fetch = json.dumps(fetch)
        self.dbc.execute(
            '''UPDATE TheGrid SET access=? WHERE user=?;''', (fetch, user))
        self.db.commit()
        return self.irc.privmsg(self.user,
                                f"\x0303Added channel {channel} to {user}'s "
                                "access list.")

    def user_chan_rm(self):
        pass

    def user_ls(self, args):
        '''
        .grid user ls

        Permition :: onwer (registered)
        List all registered admins/owners.
        '''
        if not self.cmd_check("owner", True, args, 'user ls', equal=2):
            return
        self.dbc.execute('''SELECT user, access FROM TheGrid;''')
        for f in self.dbc.fetchall():
            self.irc.privmsg(self.user, str(f).replace(
                "'", '').strip("()").replace('"', ''))
            ##Potential Issue with maxing out the RecvQ. Add a delay

    # --- Channel management --- #
    def join(self, args):
        '''
        .grid join <CHANNEL> <password>

        Permition :: onwer (registered)
        Join a channel and add it to the bot's configuration file.
        '''
        if not self.cmd_check("owner", True, args, 'join <CHANNEL> <password>',
                              less=2, more=3):
            return
        channel = args[1]
        try:
            password = args[2]
        except IndexError:
            password = ''
        chan_dict = {channel: password}
        self.conf_r['irc']['channels']['join'][channel] = password
        self.conf_w(self.conf_r)
        self.irc.var.config_load()
        self.irc.join(chan_dict)
        return self.irc.privmsg(self.user, f'\x0303Joined {channel}')

    def part(self, args):
        '''
        .grid part <CHANNEL> <msg>

        Permition :: user
        Part from a channel and remove it to the bot's configuration file.
        '''
        if not self.cmd_check("user", args[1], args, 'part <CHANNEL> <msg>',
                              less=2):
            return
        a = " ".join(args).split(" ", 2)
        channel = a[1]
        try:
            msg = a[2]
        except IndexError:
            msg = None
        self.irc.part(channel, msg)
        try:
            del self.conf_r['irc']['channels']['join'][channel]
        except KeyError:
            return self.irc.privmsg(self.user,
                                    f'\x0304Channel {channel} is not joined')
        self.conf_w(self.conf_r)
        self.irc.var.config_load()
        return self.irc.privmsg(self.user, f'\x0303Left {channel}')

    def privmsg(self, args):
        '''
        .grid privmsg <RECIEVER> <TEXT>

        Permition :: onwer (registered)
        Part from a channel and remove it to the bot's configuration file.
        '''
        if not self.cmd_check("user", args[1], args,
                              'privmsg <RECIEVER> <TEXT>', less=3):
            return
        out = args[:]
        del out[0:2]
        self.irc.privmsg(args[1], ' '.join(out))

    def notice(self, args):
        '''
        .grid notice <RECIEVER> <TEXT>

        Permition :: onwer (registered)
        Part from a channel and remove it to the bot's configuration file.
        '''
        if not self.cmd_check("user", args[1], args,
                              'notice <RECIEVER> <TEXT>', less=3):
            return
        out = args[:]
        del out[0:2]
        self.irc.privmsg(args[1], ' '.join(out))

    # --- Nicknames and normal users --- #
    def nick_bl_add(self, args):
        '''
        .grid nick blacklist add <NICKNAME>

        Permition :: user
        Blacklist a user from using the bot (uses irc.var.user_blacklist).
        Reload the configuration file.
        '''
        if not self.cmd_check("admin", '', args,
                              'nick blacklist add <NICKNAME>', equal=4):
            return
        nick = args[3]
        if nick in self.admins:
            return self.irc.privmsg(self.user, f"You cannot blacklist an "
                                    "administrator")
        try:
            c = self.conf_r['irc']['user_blacklist']
            if nick in c:
                self.irc.privmsg(self.user, f"{nick} is already blacklisted")
                return
        except KeyError:
            pass
        try:
            self.conf_r['irc']['user_blacklist'].append(nick)
        except Exception as e:
            if e.args[0] == 'user_blacklist':
                self.conf_r['irc'].update({'user_blacklist': [nick]})
        self.conf_w(self.conf_r)
        self.irc.var.config_load()
        self.irc.privmsg(self.user, '\x0303Success.')

    def nick_bl_rm(self, args):
        '''
        .grid nick blacklist rm <NICKNAME>

        Permition :: user
        Remove a user from the bot's user_blacklist.
        Reload the configuration file.
        '''
        if not self.cmd_check("admin", '', args,
                              'nick blacklist rm <NICKNAME>', equal=4):
            return
        nick = args[3]
        c = self.conf_r['irc']['user_blacklist']
        if nick in c:
            c.remove(nick)
            self.conf_w(self.conf_r)
            self.irc.var.config_load()
            self.irc.privmsg(self.user, '\x0303Success.')
        else:
            self.irc.privmsg(self.user, f'{nick} is not blacklisted')

    # --- Module management --- #
    def mod_reimport(self, args):
        '''
        .grid mod reimport

        Permition :: onwer (registered)
        Import a module in the bot and add it in the configuration's file
        import list.
        Reload the configuration file.
        '''
        if not self.cmd_check("owner", True, args, 'mod reimport', equal=2):
            return
        self.botsys[1]()
        self.irc.privmsg(self.user, '\x0303Re-imported modules')

    def mod_ls_add(self, args):
        '''
        .grid mod {white|black}list add <MODULE> <CHANNEL>

        Permition :: user
        Add a "module" to the bot's whitelist/blacklist (depeneds on "mode")
        in the configuration file.
        Reload the configuration file.
        '''
        if not self.cmd_check("user", args[4], args,
                              'mod {whitelist|blacklist} add <MODULE> '
                              '<CHANNEL>', equal=5):
            return
        ls = args[1]
        mod = args[3]
        channel = args[4]
        if ls == 'whitelist':
            sl = 'blacklist'
        elif ls == 'blacklist':
            sl = 'whitelist'
        if mod not in self.botsys[0]:
            self.irc.privmsg(self.user,
                             f'\x0304[!] Module "{mod}" is not loaded.')
            return
        try:
            c = self.conf_r['irc']['modules']['settings'][mod]
            if sl in c and len(c[sl]) != 0:
                self.irc.privmsg(self.user, f'\x0304Failed to add a {ls}. '
                                 f'A {sl} for "{mod}" has already been set.')
                return
            if channel in c[ls]:
                self.irc.privmsg(self.user, f'\x0308Module "{mod}" is already '
                                 f'{ls}ed from "{channel}"')
                return
        except KeyError:
            pass
        try:
            self.conf_r['irc']['modules']['settings'][mod][ls].append(channel)
        except Exception as e:
            if e.args[0] == ls:
                self.conf_r['irc']['modules']['settings'][mod].update(
                    {ls: [channel]})
            elif e.args[0] == mod:
                self.conf_r['irc']['modules']['settings'].update(
                    {mod: {ls: [channel]}})
            elif e.args[0] == 'settings':
                print(e)
                self.conf_r['irc']['modules'].update(
                    {"settings": {mod: {ls: [channel]}}})
        self.conf_w(self.conf_r)
        self.irc.var.config_load()
        self.irc.privmsg(self.user, '\x0303Success.')

    def mod_ls_rm(self, args):
        '''
        .grid mod {white|black}list rm <MODULE> <CHANNEL>

        Permition :: user
        Delete a "module" from the bot's whitelist/blacklist
        (depeneds on "mode") in the configuration file.
        Reload the configuration file.
        '''
        if not self.cmd_check("user", args[4], args,
                              'mod {whitelist|blacklist} rm <MODULE> '
                              '<CHANNEL>', equal=5):
            return
        ls = args[1]
        mod = args[3]
        channel = args[4]
        c = self.conf_r['irc']['modules']['settings'][mod][ls]
        if channel in c:
            c.remove(channel)
            self.conf_w(self.conf_r)
            self.irc.var.config_load()
            self.irc.privmsg(self.user, '\x0303Success.')
            return
        self.irc.privmsg(self.user, f'\x0308Module "{mod}" has no {ls} for '
                         'channel "{channel}"')

    def mod_ls_ls(self, args):
        '''
        .grid mod ls <CHANNEL>

        Permition :: users
        Show the module whitelist and blacklist for a channel. If "ALL" is
        given as a channel then check if the user is an owner and show the
        list for all channels.
        '''
        def mod_ls_iter():
            mod_bl_dict = {}
            mod_wl_dict = {}
            for m in self.botsys[0]:
                try:
                    c = self.conf_r['irc']['modules'][
                        'settings'][m]['blacklist']
                    mod_bl_dict[m] = c
                except KeyError:
                    pass
                try:
                    c = self.conf_r['irc']['modules'][
                        'settings'][m]['whitelist']
                    mod_wl_dict[m] = c
                except KeyError:
                    pass
            return mod_bl_dict, mod_wl_dict
        try:
            if not self.cmd_check("user", args[2], args, 'mod ls <CHANNEL>',
                                  equal=3):
                return
        except IndexError:
            self.cmd_check("user", '', args, 'mod ls <CHANNEL>', equal=3)
            return
        mod_bl_dict, mod_wl_dict = mod_ls_iter()
        if args[2] == "ALL":
            if not self.cmd_check("owner", True, args, 'mod ls <CHANNEL>',
                                  equal=3):
                return
            self.irc.privmsg(self.user, '\x0300,01BLACKLIST:')
            for k, v in mod_bl_dict.items():
                self.irc.privmsg(self.user, f"[{k}]: {v}")
            self.irc.privmsg(self.user, '\x0301,00WHITELIST:')
            for k, v in mod_wl_dict.items():
                self.irc.privmsg(self.user, "[{k}]: {v}")
        else:
            self.irc.privmsg(self.user, '\x0300,01BLACKLIST:')
            for k, v in mod_bl_dict.items():
                if args[2] in v:
                    self.irc.privmsg(self.user, "[{k}]")
            self.irc.privmsg(self.user, '\x0301,00WHITELIST:')
            for k, v in mod_wl_dict.items():
                if args[2] in v:
                    self.irc.privmsg(self.user, "[{k}]")

    def mod_prefix(self, args):
        '''
        .grid mod prefix <PREFIX> <CHANNEL>

        Permition :: user
        Set the "prefix" for the commands in the configuration file.

        PPermition :: owner (registered)
        If <channel> == ALL, check for owner status and change the global
        prefix.
        Reload the configuration file.
        '''
        def global_prefix():
            self.conf_r['irc']['modules']['global_prefix'] = prefix
            self.conf_w(self.conf_r)
            self.irc.var.config_load()
            self.irc.privmsg(self.user,
                             'Changed the global_prefix to "{prefix}"')

        def channel_prefix():
            try:
                self.conf_r['irc']['channels']['settings'][channel][
                    'prefix'] = prefix
            except Exception as e:
                print(e)
                if e.args[0] == "prefix":
                    self.conf_r['irc']['channels']['settings'][channel].update(
                        {"prefix": prefix})
                elif e.args[0] == channel:
                    self.conf_r['irc']['channels']['settings'].update(
                        {channel: {"prefix": prefix}})
                elif e.args[0] == "settings":
                    print(e)
                    self.conf_r['irc']['channels'].update(
                        {"settings": {channel: {"prefix": prefix}}})
            self.conf_w(self.conf_r)
            self.irc.var.config_load()
            self.irc.privmsg(self.user, 'Success.')

        if not self.cmd_check("user", args[3], args,
                              'mod prefix <PREFIX> <CHANNEL>', equal=4):
            return
        prefix = args[2]
        channel = args[3]
        if args[3] == "ALL":
            global_prefix()
        else:
            channel_prefix()

    def helper(self, user):
        # add a list of all the commands to be send as a privmsg to the user
        pass


def main(i, irc):
    user = i.nickname
    command = f"{i.cmd_prefix}{i.cmd}"
    args = i.msg_nocmd.split()
    if not args:
        return
    botsys = [i.modules, i.mod_import]
    grid = TheGrid(irc, user, command, i.db, botsys)
    grid_cmds = {
        'login':    grid.login,
        'logout':   grid.logout,
        'register': grid.register,
        'password': grid.password,
        'join':     grid.join,
        'part':     grid.part,
        'privmsg':  grid.privmsg,
        'notice':   grid.notice,
        'help':     grid.helper,
        'nick blacklist add': grid.nick_bl_add,
        'nick blacklist rm':  grid.nick_bl_rm,
        'user add':         grid.user_add,
        'user rm':          grid.user_rm,
        'user password':    grid.user_pass,
        'user channel add': grid.user_chan_add,
        'user channel rm':  grid.user_chan_rm,
        'user ls':          grid.user_ls,
        'mod reimport':      grid.mod_reimport,
        'mod whitelist add': grid.mod_ls_add,
        'mod blacklist add': grid.mod_ls_add,
        'mod whitelist rm':  grid.mod_ls_rm,
        'mod blacklist rm':  grid.mod_ls_rm,
        'mod ls':            grid.mod_ls_ls,
        'mod prefix':        grid.mod_prefix
    }

    try:
        grid_cmds[args[0]](args)
    except KeyError:
        try:
            grid_cmds[args[0] + ' ' + args[1]](args)
        except KeyError:
            try:
                grid_cmds[args[0] + ' ' + args[1] + ' ' + args[2]](args)
            except KeyError:
                pass
