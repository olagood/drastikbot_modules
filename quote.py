#!/usr/bin/env python3
# coding=utf-8

# Quote Module for Drastikbot
#
# Save user quotes and send them to a channel upon request.

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

import random


class Module:
    def __init__(self):
        self.commands = ['quote', 'findquote', 'addquote', 'delquote']
        self.helpmsg = [
            "Usage: .quote <Nickname / ID / Query>",
            "       .findquote <Query>",
            "       .addquote <Nickname> <Quote>",
            "       .delquote <ID>",
            " ",
            "Save user quotes and send them upon request.",
            ".quote : If no arguments are given, a random quote will be sent.",
            "         If you pass aguments the bot will first try to match a ",
            "         nickname, then an ID and at last a phrase.",
            ".findquote : Try to match a given phrase and return the match. ",
            "             If there are many matches send a random one.",
            ".addquote : Add a quote to the database.",
            ".delquote : Delete a quote using it's ID."]


def add(channel, quote, made_by, added_by, dbc):
    dbc.execute("INSERT INTO quote(channel, quote, made_by, added_by) "
                "VALUES (?, ?, ?, ?)", (channel, quote, made_by, added_by))
    return f"\x02quote\x0F: #{dbc.lastrowid} Added!"


def delete(quote_id, dbc):
    try:
        dbc.execute('''DELETE FROM quote WHERE num=?;''', (quote_id,))
        return f"\x02quote\x0F: #{quote_id} deleted."
    except Exception:
        pass


def find(channel, query, dbc):
    try:
        dbc.execute(
            '''SELECT num FROM quote_index
            WHERE quote_index MATCH ? AND channel=?;''',
            (f"quote:{query}", channel))
        f = dbc.fetchall()
        num = random.choice(f)[0]
        dbc.execute('''SELECT * FROM quote WHERE num=?''', (num,))
        f = dbc.fetchone()
        return (f"\x02quote\x0F: #{f[0]} | "
                f"{f[2]} \x02-\x0F {f[3]} | "
                f"Added by {f[4]}")
    except Exception as e:
        return "\x02quote\x0F: No results."


def _search_by_nick(channel, text, dbc):
    try:
        if not text:
            dbc.execute('SELECT * FROM quote WHERE channel=?', (channel,))
        else:
            dbc.execute('SELECT * FROM quote WHERE made_by=? AND channel=?;',
                        (text, channel))
        f = dbc.fetchall()
        f = random.choice(f)
        return (f"\x02quote\x0F: #{f[0]} | "
                f"{f[2]} \x02-\x0F {f[3]} | "
                f"Added by {f[4]}")
    except Exception:
        return False


def _search_by_id(channel, text, dbc):
    if not text.isdigit():
        return False

    try:
        dbc.execute('SELECT * FROM quote WHERE num=?;', (text,))
        f = dbc.fetchone()
        return (f"\x02quote\x0F: #{f[0]} | "
                f"{f[2]} \x02-\x0F {f[3]} | "
                f"Added by {f[4]}")
    except Exception:
        return False


def quote(channel, text, dbc):
    sbn = _search_by_nick(channel, text, dbc)
    if sbn:
        return sbn
    sbi = _search_by_id(channel, text, dbc)
    if sbi:
        return sbi

    return find(channel, text, dbc)


def main(i, irc):
    if i.nickname == i.channel:
        irc.privmsg(i.channel, "quote: You can only use this within a channel.")
        return

    dbc = i.db[1].cursor()

    dbc.execute(
        '''
        CREATE TABLE IF NOT EXISTS quote
        (num     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        channel  TEXT,
        quote    TEXT COLLATE NOCASE,
        made_by  TEXT COLLATE NOCASE,
        added_by TEXT COLLATE NOCASE);''')
    dbc.execute(
        '''
        CREATE VIRTUAL TABLE IF NOT EXISTS quote_index
        USING fts5(num, quote, channel, tokenize=porter);''')
    dbc.execute(
        '''
        CREATE TRIGGER IF NOT EXISTS quote_after_insert AFTER INSERT ON quote
        BEGIN
        INSERT INTO quote_index (num, quote, channel)
        VALUES (new.num, new.quote, new.channel);
        END;''')
    dbc.execute(
        '''
        CREATE TRIGGER IF NOT EXISTS quote_after_delete AFTER DELETE ON quote
        BEGIN
        DELETE FROM quote_index WHERE num = old.num;
        END;''')
    i.db[1].commit()

    if 'quote' == i.cmd:
        irc.privmsg(i.channel, quote(i.channel, i.msg_nocmd, dbc))
    elif 'findquote' == i.cmd:
        if not i.msg_nocmd:
            help_msg = f"Usage: {i.cmd_prefix}{i.cmd} <Query>"
            irc.privmsg(i.channel, help_msg)
            return
        irc.privmsg(i.channel, find(i.channel, i.msg_nocmd, dbc))
    elif 'delquote' == i.cmd:
        if not i.msg_nocmd or not i.msg_nocmd.isdigit():
            help_msg = f"Usage: {i.cmd_prefix}{i.cmd} <ID>"
            irc.privmsg(i.channel, help_msg)
            return
        irc.privmsg(i.channel, delete(i.msg_nocmd, dbc))
    elif 'addquote' == i.cmd:
        if not i.msg_nocmd or len(i.msg_nocmd.split()) < 2:
            help_msg = f"Usage: {i.cmd_prefix}{i.cmd} <Nickname> <Quote>"
            irc.privmsg(i.channel, help_msg)
            return
        made_by = i.msg_nocmd.split()[0]
        quote_text = " ".join(i.msg_nocmd.split()[1:])
        irc.privmsg(i.channel,
                    add(i.channel, quote_text, made_by, i.nickname, dbc))

    i.db[1].commit()
