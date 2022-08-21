#!/usr/bin/env python3
# coding=utf-8

# Reminder Module for Drastikbot
#
# It sends user requested messages after a period of time.

'''
Remind module for drastikbot.
Copyright (C) 2022 drastik.org

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

from threading import Thread
import time
from zoneinfo import ZoneInfo

from dbothelper import get_day_str, get_month_str  # type: ignore


class Module:
    irc_commands = ["376", "422", "311"]


# Database ###########################################################

def get_due_receivers(db):
    dbc = db.cursor()

    sql = """
        SELECT receiver, timestamp
        FROM remind
        WHERE timestamp <= strftime('%s', 'now')
        GROUP BY receiver;
    """
    dbc.execute(sql)
    return dbc.fetchall()


def get_due_by_receiver(db, receiver):
    dbc = db.cursor()
    sql = """
        SELECT id, receiver, added_by, message, channel, timestamp
        FROM remind
        WHERE timestamp <= strftime('%s', 'now')
              AND receiver = ?;
    """
    dbc.execute(sql, (receiver,))
    return dbc.fetchall()


def delete_reminder(db, id):
    dbc = db.cursor()
    dbc.execute("DELETE FROM remind WHERE id = ?;", (id,))
    db.commit()


def clear_expired(db):
    """An expired reminder is a reminder that was not sent to its
    receiver 5 days after it was supposed to. This can happen because
    the user is not present on the IRC network.
    """
    dbc = db.cursor()
    sql = """
        DELETE FROM remind
        WHERE (strftime('%s', 'now') - timestamp) > (3600 * 24 * 5)
    """
    dbc.execute(sql)
    db.commit()


# ====================================================================
# Output preparation and formatting
# ====================================================================

def msg_reminder(id, receiver, added_by, message, channel, timestamp):
    if receiver == added_by:
        head = "You asked me to remind you:"
    elif receiver == channel:
        head = f"{receiver} asked me in private to remind you:"
    else:
        head = f"{receiver} asked me in {channel} to remind you:"

    return head, message


# ====================================================================
# Worker
# ====================================================================

def worker(i, irc):
    db = i.db_disk

    while True:
        # Stop if the IRC connection was lost. A new worker will be
        # started on reconnection.
        if irc.conn_state == 0:
            return

        acc = []
        for row in get_due_receivers(db):
            receiver, timestamp = row

            acc.append(receiver)
            if (len(acc) >= 12):
                irc.send(("WHOIS", ",".join(acc)))
                acc = []
                # Prevent being throttled by the server if a user
                # abuses the module to set reminders for many
                # unknown nicks.
                time.sleep(5)

        if acc:
            irc.send(("WHOIS", ",".join(acc)))

        clear_expired(db)  # Remove expired unsent reminders

        time.sleep(5)  # Wait before retrying


def rpl_whoisuser_311(i, irc):
    db = i.db_disk
    params = i.msg.get_params()

    receiver = params[1]

    for reminder in get_due_by_receiver(db, receiver):
        id, receiver, _adder, _msg, _ch, _ts = reminder
        heading, message = msg_reminder(*reminder)
        irc.out.privmsg(receiver, heading)
        irc.out.privmsg(receiver, message)
        delete_reminder(db, id)
        time.sleep(1.5)  # Prevent server throttling


# ====================================================================
# Intialization
# ====================================================================

def init_thread(i, irc):
    log = i.bot["runlog"]

    thread = Thread(target=worker, args=(i, irc))
    thread.start()
    log.debug("[module: remind] Worker thread started")


# ====================================================================
# Main
# ====================================================================

def main(i, irc):
    irc_command = i.msg.get_command()

    # On MOTD or ERR_NOMOTD start the worker thread
    if irc_command == "376" or irc_command == "422":
        init_thread(i, irc)

    # On RPL_WHOISUSER (generated by the worker) send the reminders.
    # We do this to ensure that the nickname exists on the server.
    if irc_command == "311":
        rpl_whoisuser_311(i, irc)
