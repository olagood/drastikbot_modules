#!/usr/bin/env python3
# coding=utf-8

# Quote Module for Drastikbot
#
# Save user quotes and send them to a channel upon request.


# Copyright (C) 2019-2021 drastik.org
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


import requests

from irc.message import remove_formatting
from admin import is_allowed
from admin import is_bot_owner


class Module:
    startup = True
    bot_commands = ["quote",
                    # Add quotes aliases
                    "quote-add", "add-quote", "addquote", "quoteadd",
                    "quote_add", "add_quote",
                    # Others
                    "quote-del", "quote-search",
                    "quote-match", "quote-list-mentioned",
                    "quote-initialize"]
    manual = {
        "desc": "Saves user quotes and posts them when requested.",
        "bot_commands": {
            "quote": {
                "usage": lambda x: (
                    f"[channels]: {x}quote [nickname/id/text]"
                    f" | [queries]: {x}quote <#channel> [nickname/id/text]"
                ),
                "info": ("Without any arguments, a random quote will be"
                         " posted. If arguments are given the bot will try"
                         " to first match a nickname, then an ID and then"
                         " the text of a quote.")
            },
            "quote-find": {
                "usage": lambda x: (
                    f"[channels]: {x}quote-find <text>"
                    f" | [queries]: {x}quote-find <#channel> <text>"
                ),
                "info": ("Try to match the given text to a quote."
                         " If a quote is found, it is posted.")
            },
            "quote-add": {
                "usage": lambda x: f"{x}quote-add <nickname> <quote>",
                "info": "Add a quote to the database."
            },
            "quote-del": {
                "usage": lambda x: f"{x}quote-del <id>",
                "info": "Delete a quote using its ID"
            },
            "quote-list-mentioned": {
                "usage": lambda x: f"{x}quote-list-mentioned",
                "info": ("List all the quotes in which the the caller is"
                         " mentioned in. The list is sent in a query.")
            }
        }
    }


logo = "\x02quote\x0F"


def format_quote(q):
    return f"{logo} #{q[0]} (added by {q[3]}): <{q[2]}> {q[1]}"


# ====================================================================
# Database Initializer: Called during bot startup
# ====================================================================

def db_init(dbc):
    dbc.executescript("""

    -- TABLES

    CREATE TABLE IF NOT EXISTS quote_quotes (
           id           INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
           quote        TEXT COLLATE NOCASE NOT NULL,
           quotee       TEXT COLLATE NOCASE NOT NULL,
           added_by     TEXT COLLATE NOCASE NOT NULL,
           views        INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS quote_channels (
           id           INTEGER NOT NULL,
           channel      TEXT COLLATE NOCASE NOT NULL,
           quote_id     INTEGER NOT NULL,  -- The actual quote id
           FOREIGN KEY(quote_id) REFERENCES quote_quotes(id),
           PRIMARY KEY(id, channel)
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS quote_fts5 USING fts5 (
           id, quote, tokenize = porter
    );


    -- FTS5 - TRIGGERS

    CREATE TRIGGER IF NOT EXISTS quote_fts5_t_insert
    AFTER INSERT ON quote_quotes
    BEGIN
        INSERT INTO quote_fts5 (id, quote) VALUES (new.id, new.quote);
    END;

    CREATE TRIGGER IF NOT EXISTS quote_fts5_t_update
    AFTER UPDATE ON quote_quotes
    BEGIN
        UPDATE quote_fts5 SET quote = new.quote WHERE id = old.id;
    END;

    CREATE TRIGGER IF NOT EXISTS quote_fts5_t_delete
    AFTER DELETE ON quote_quotes
    BEGIN
        DELETE FROM quote_fts5 WHERE id = old.id;
    END;


    -- CHANNEL QUOTES / QUOTES - TRIGGERS

    CREATE TRIGGER IF NOT EXISTS quote_quotes_t_delete_noref
    AFTER DELETE ON quote_channels
    BEGIN
        DELETE FROM quote_quotes WHERE id = old.quote_id;
    END;

    """)


def quote_initialize(i, irc, dbc):
    nickname = i.msg.get_nickname()
    if is_bot_owner(irc, nickname):
        db_init(dbc)
        irc.out.notice(nickname, "quote: database initialized")


# ====================================================================
# Database functions
# ====================================================================

# Insertion functions

def db_is_quote_in_channel(dbc, quote, channel):
    sql = """
        SELECT c.id
        FROM quote_channels AS c
        INNER JOIN quote_quotes AS q ON q.id = c.quote_id
        WHERE c.channel = ? AND q.quote = ?
    """
    dbc.execute(sql, (channel, quote))
    ret = dbc.fetchone()
    if ret is None:
        return None  # The quote is not in the channel
    return ret[0]  # The channel id of the quote


def db_add_quote(dbc, quote, quotee, added_by, channel):
    sql = """
        INSERT INTO quote_quotes (quote, quotee, added_by)
        VALUES (?, ?, ?);
    """
    dbc.execute(sql, (quote, quotee, added_by))

    quote_id = dbc.lastrowid
    mcq_id = db_max_channel_quote_id(dbc, channel)
    mcq_id += 1

    sql = """
        INSERT INTO quote_channels (id, channel, quote_id)
        VALUES (?, ?, ?);
    """
    dbc.execute(sql, (mcq_id, channel, quote_id))

    return mcq_id


def db_max_channel_quote_id(dbc, channel):
    sql = """
        SELECT MAX(id) FROM quote_channels WHERE channel = ?;
    """
    dbc.execute(sql, (channel,))
    ret = dbc.fetchone()
    if ret[0] is None:
        return 0
    else:
        return ret[0]


# Views

def db_increment_views(dbc, quote_id):
    sql = """
        UPDATE quote_quotes
        SET views = (SELECT views FROM quote_quotes
                     WHERE id = ?) + 1
        WHERE id = ?
    """
    dbc.execute(sql, (quote_id, quote_id))


# Deletion functions

def db_delete_channel_quote(dbc, channel, qcid):
    sql = """
        DELETE FROM quote_channels WHERE id = ? AND channel = ?;
    """
    dbc.execute(sql, (qcid, channel))
    return True


# Retrieval functions

def db_get_quotes_for_quotee(dbc, quotee):
    sql = """
        SELECT c.id, c.channel, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_channels AS c
        INNER JOIN quote_quotes AS q ON q.id = c.quote_id
        WHERE q.quotee = ?
    """
    dbc.execute(sql, (quotee,))
    return dbc.fetchall()


def db_get_random_channel_quote_for_quotee(dbc, quotee, channel):
    sql = """
        SELECT c.id, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_channels AS c
        INNER JOIN quote_quotes AS q ON q.id = c.quote_id
        WHERE q.quotee = ? AND c.channel = ?
        ORDER BY RANDOM()
        LIMIT 1
    """
    dbc.execute(sql, (quotee, channel))
    return dbc.fetchone()


def db_get_quotes_for_added_by(dbc, added_by):
    sql = """
        SELECT c.id, c.channel, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_channels AS c
        INNER JOIN quote_quotes AS q ON q.id = c.quote_id
        WHERE q.added_by = ?
    """
    dbc.execute(sql, (added_by,))
    return dbc.fetchall()


def db_get_channel_quotes_for_added_by(dbc, added_by, channel, limit=1):
    sql = """
        SELECT c.id, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_channels AS c
        INNER JOIN quote_quotes AS q ON q.id = c.quote_id
        WHERE q.added_by = ? AND c.channel = ?
        LIMIT ?
    """
    dbc.execute(sql, (added_by, channel, limit))
    return dbc.fetchall()


def db_get_random_quote_from_channel(dbc, channel):
    sql = """
        SELECT c.id, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_channels AS c
        INNER JOIN quote_quotes AS q ON q.id = c.quote_id
        WHERE c.channel = ?
        ORDER BY RANDOM()
        LIMIT 1;
    """
    dbc.execute(sql, (channel,))
    return dbc.fetchone()


def db_find_by_channel_id(dbc, cqid, channel):
    sql = """
        SELECT c.id, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_quotes AS q
        INNER JOIN quote_channels AS c ON q.id = c.quote_id
        WHERE c.channel = ? AND c.id = ?
        LIMIT 1;
    """
    dbc.execute(sql, (channel, cqid))
    return dbc.fetchone()


def db_find_random_fts5(dbc, query, channel):
    sql = """
        SELECT c.id, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_quotes AS q
        INNER JOIN quote_channels AS c ON q.id = c.quote_id
        INNER JOIN quote_fts5 AS f ON f.id = q.id
        WHERE c.channel = ? AND f.quote MATCH ?
        ORDER BY RANDOM()
        LIMIT 1;
    """
    # Make the query an FTS5 string
    q = query.replace('"', '')
    q = f'"{q}"'

    dbc.execute(sql, (channel, q))
    return dbc.fetchone()


def db_find_channel_fts5(dbc, query, channel, limit=10):
    sql = """
        SELECT c.id, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_quotes AS q
        INNER JOIN quote_channels AS c ON q.id = c.quote_id
        INNER JOIN quote_fts5 AS f ON f.id = q.id
        WHERE c.channel = ? AND f.quote MATCH ?
        LIMIT ?;
    """
    # Make the query an FTS5 string
    q = query.replace('"', '')
    q = f'"{q}"'

    dbc.execute(sql, (channel, q, limit))
    return dbc.fetchall()


def db_find_fts5(dbc, query, limit=10):
    sql = """
        SELECT c.id, c.channel, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_quotes AS q
        INNER JOIN quote_channels AS c ON q.id = c.quote_id
        INNER JOIN quote_fts5 AS f ON f.id = q.id
        WHERE f.quote MATCH ?
        LIMIT ?;
    """
    # Make the query an FTS5 string
    q = query.replace('"', '')
    q = f'"{q}"'

    dbc.execute(sql, (q, limit))
    return dbc.fetchall()


def db_match_random(dbc, query, channel):
    sql = """
        SELECT c.id, q.quote, q.quotee, q.added_by, q.views, q.id
        FROM quote_quotes AS q
        INNER JOIN quote_channels AS c ON q.id = c.quote_id
        WHERE c.channel = ? AND q.quote LIKE ?
        ORDER BY RANDOM()
        LIMIT 1;
    """
    dbc.execute(sql, (channel, query))
    return dbc.fetchone()


# ====================================================================
# Web sharing APIs
# ====================================================================

def pomf_plaintext_upload(data):
    url = "https://pomf.lain.la/upload.php"
    files = {"files[]": ("quotes.txt", data, "text/plain")}
    r = requests.post(url, files=files)
    return r.json()["files"][0]["url"]


# ====================================================================
# IRC callbacks
# ====================================================================

# quote : Multilayered command for viewing and finding quotes.
#         See quote_handler() to understand what it does.

def quote(i, irc, dbc):
    if i.msg.is_pm():
        quote_pm(i, irc, dbc)
    else:
        quote_channel(i, irc, dbc)


def quote_channel(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    args = i.msg.get_args()

    m = quote_handler(dbc, args, msgtarget)
    irc.out.notice(msgtarget, m)


def quote_pm(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    argv = args.split(" ", 1)
    argc = len(argv)

    if not args:
        m = f"{logo}: Usage: {prefix}{botcmd} <#channel> <nickname/id/text>"
        irc.out.notice(msgtarget, m)
        return

    if argc == 1:
        channel = argv[0]
        query = False
    else:
        channel, query = argv

    if not channel[:1] in irc.chantypes:
        m = f"{logo}: Enter the channel with its prefix: #channel"
        irc.out.notice(msgtarget, m)
        return

    if channel not in irc.channels:
        m = f"{logo}: The bot has not joined the channel: {channel}"
        irc.out.notice(msgtarget, m)
        return

    m = quote_handler(dbc, query, channel)
    irc.out.notice(msgtarget, m)


def quote_handler(dbc, query, channel):
    if not query:
        return quote_hdl_no_query(dbc, channel)

    if len(query.split()) > 1:  # Can't be a nick or an id, do a fts
        return quote_search_handler(dbc, query, channel)

    # Assume query is a channel quote id

    # q = c.id, q.quote, q.quotee, q.added_by, q.views, q.id
    q = db_find_by_channel_id(dbc, query, channel)
    if q:
        db_increment_views(dbc, q[5])
        return format_quote(q)

    # Assume query is quotee

    # q = c.id, q.quote, q.quotee, q.added_by, q.views, q.id
    q = db_get_random_channel_quote_for_quotee(dbc, query, channel)
    if q:
        db_increment_views(dbc, q[5])
        return format_quote(q)

    return f"{logo}: No results"


def quote_hdl_no_query(dbc, channel):
    # q = c.id, q.quote, q.quotee, q.added_by, q.views, q.id
    q = db_get_random_quote_from_channel(dbc, channel)
    if not q:
        return f"{logo}: No results"

    db_increment_views(dbc, q[5])

    return format_quote(q)


# quote-search : Search for a quote using FTS5 with the porter tokenizer.
#     This allows for finding quotes even if the query is not precise.

def quote_search(i, irc, dbc):
    if i.msg.is_pm():
        quote_search_pm(i, irc, dbc)
    else:
        quote_search_channel(i, irc, dbc)


def quote_search_channel(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if not args:
        m = f"{logo}: Usage: {prefix}{botcmd} <text>"
        irc.out.notice(msgtarget, m)
        return

    m = quote_search_handler(dbc, args, msgtarget)
    irc.out.notice(msgtarget, m)


def quote_search_pm(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    argv = args.split(" ", 1)
    argc = len(argv)

    if not args or argc < 2:
        m = f"{logo}: Usage: {prefix}{botcmd} <#channel> <text>"
        irc.out.notice(msgtarget, m)
        return

    channel, query = argv

    if not channel[:1] in irc.chantypes:
        m = f"{logo}: Usage: {prefix}{botcmd} <#channel> <text>"
        irc.out.notice(msgtarget, m)
        return

    if channel not in irc.channels:
        m = f"{logo}: The bot has not joined the channel: {channel}"
        irc.out.notice(msgtarget, m)
        return

    m = quote_search_handler(dbc, query, channel)
    irc.out.notice(msgtarget, m)


def quote_search_handler(dbc, query, channel):
    # q = c.id, q.quote, q.quotee, q.added_by, q.views, q.id
    q = db_find_random_fts5(dbc, query, channel)
    if not q:
        return f"{logo}: No results"

    db_increment_views(dbc, q[5])

    return format_quote(q)


# quote-match : Search for a quote using an exact string

def quote_match(i, irc, dbc):
    if i.msg.is_pm():
        quote_match_pm(i, irc, dbc)
    else:
        quote_match_channel(i, irc, dbc)


def quote_match_channel(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if not args:
        m = f"{logo}: Usage: {prefix}{botcmd} <text>"
        irc.out.notice(msgtarget, m)
        return

    m = quote_match_handler(dbc, args, msgtarget)
    irc.out.notice(msgtarget, m)


def quote_match_pm(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    argv = args.split(" ", 1)
    argc = len(argv)

    if not args or argc < 2:
        m = f"{logo}: Usage: {prefix}{botcmd} <#channel> <text>"
        irc.out.notice(msgtarget, m)
        return

    channel, query = argv

    if not channel[:1] in irc.chantypes:
        m = f"{logo}: Usage: {prefix}{botcmd} <#channel> <text>"
        irc.out.notice(msgtarget, m)
        return

    if channel not in irc.channels:
        m = f"{logo}: The bot has not joined the channel: {channel}"
        irc.out.notice(msgtarget, m)
        return

    m = quote_match_handler(dbc, query, channel)
    irc.out.notice(msgtarget, m)


def quote_match_handler(dbc, query, channel):
    # q = c.id, q.quote, q.quotee, q.added_by, q.views, q.id
    q = db_match_random(dbc, query, channel)
    if not q:
        return f"{logo}: No results"

    db_increment_views(dbc, q[5])

    return format_quote(q)


# quote-add : Insert channel quotes

def quote_add(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if i.msg.is_pm():
        m = f"{logo}: Quotes must be submitted from a channel."
        irc.out.notice(msgtarget, m)
        return

    argv = args.split(" ", 1)
    argc = len(argv)

    if not args or argc < 2:
        m = f"{logo}: Usage: {prefix}{botcmd} <nickname> <quote>"
        irc.out.notice(msgtarget, m)
        return

    quotee, quote = argv
    quotee = nickname_cleanup(irc, quotee)

    qcid = db_is_quote_in_channel(dbc, quote, msgtarget)
    if qcid:
        m = f"{logo}: This quote has already been added. (See #{qcid})"
        irc.out.notice(msgtarget, m)
        return

    qcid = db_add_quote(dbc, quote, quotee, nickname, msgtarget)
    m = f"{logo}: #{qcid} Added!"
    irc.out.notice(msgtarget, m)


def nickname_cleanup(irc, nickname):
    """Cleanup nickname copy/paste artifacts"""
    nickname = remove_formatting(nickname)
    nickname = nickname.replace("<", "").replace(">", "")
    for p in irc.prefix.values():
        nickname = nickname.replace(p, "")
    return nickname


# quote-del : Remove channel quotes

def quote_del(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if i.msg.is_pm():
        m = f"{logo}: This command can only be used within a channel."
        irc.out.notice(msgtarget, m)
        return

    if not args or not args.isnumeric():
        m = f"{logo}: Usage: {prefix}{botcmd} <ID>"
        irc.out.notice(msgtarget, m)
        return

    if not is_allowed(i, irc, nickname, msgtarget):
        m = f"{logo}: Only channel operators are allowed to delete quotes."
        irc.out.notice(msgtarget, m)
        return

    if db_delete_channel_quote(dbc, msgtarget, args):
        m = f"{logo}: Quote #{args} deleted."
    else:
        # If there really is an error this will never be executed.
        m = f"{logo}: Database error. The quote was not deleted."

    irc.out.notice(msgtarget, m)


# quote-list-mentioned

def quote_list_mentioned(i, irc, dbc):
    nickname = i.msg.get_nickname()

    acc = "Channel ID | Channel | Quote | Quotee | Added by | Views | ID\n\n"

    acc += "-- Quotes in which you are the quotee: \n\n"

    # q[0] = c.id, c.channel, q.quote, q.quotee, q.added_by, q.views, q.id
    q = db_get_quotes_for_quotee(dbc, nickname)
    if q is not None:
        for i in q:
            acc += (f"{i[0]} | {i[1]} | {i[2]} | {i[3]} | {i[4]} | {i[5]}"
                    f" | {i[6]}\n")

    acc += "\n\n-- Quotes that you added: \n\n"

    # q[0] = c.id, c.channel, q.quote, q.quotee, q.added_by, q.views, q.id
    q = db_get_quotes_for_added_by(dbc, nickname)
    if q is not None:
        for i in q:
            acc += (f"{i[0]} | {i[1]} | {i[2]} | {i[3]} | {i[4]} | {i[5]}"
                    f" | {i[6]}\n")

    acc += "\n\n-- Quotes that include your nickname: \n\n"

    # q[0] = c.id, c.channel, q.quote, q.quotee, q.added_by, q.views, q.id
    q = db_find_fts5(dbc, nickname, limit=-1)
    if q is not None:
        for i in q:
            acc += (f"{i[0]} | {i[1]} | {i[2]} | {i[3]} | {i[4]} | {i[5]}"
                    f" | {i[6]}\n")

    pomf_url = pomf_plaintext_upload(acc)
    m = f"{logo}: Your quotes can be found here: {pomf_url}"
    irc.out.notice(nickname, m)  # Send as PM for privacy reasons.


# ====================================================================
# Main
# ====================================================================

dispatch = {
    "__STARTUP": lambda _i, _irc, dbc: db_init(dbc),
    "quote-initialize": quote_initialize,
    "quote": quote,
    "quote-search": quote_search,
    "quote-match": quote_match,
    "quote-del": quote_del,
    "quote-list-mentioned": quote_list_mentioned,
    # Quote add aliases
    "quote-add": quote_add,
    "add-quote": quote_add,
    "addquote": quote_add,
    "quoteadd": quote_add,
    "quote_add": quote_add,
    "add_quote": quote_add,
}


def main(i, irc):
    try:
        botcmd = i.msg.get_botcmd()
    except AttributeError:
        botcmd = i.msg.get_command()  # __STARTUP

    db = i.db_disk
    dbc = db.cursor()

    dispatch[botcmd](i, irc, dbc)

    db.commit()  # Save any changes
