# coding=utf-8

# Wikipedia (MediaWiki) module for drastikbot2
#
# This module is making use of the MediaWiki API to find articles from
# Wikipedia.  The code  should be  able to  work with  other MediaWiki
# websites
#
# Depends
# -------
# pip: requests, beautifulsoup4

# Copyright (C) 2017, 2021 drastik.org
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
import bs4
import urllib.parse
from dbot_tools import p_truncate


def usage(prefix, command):
    return (f"{prefix}{command} <article> [--full] [--search]"
            " [--sections] [-l <lang>] [--resuult <num>]")


class Module:
    bot_commands = ["wikipedia", "wiki", "w"]
    info = ("--info: Get the full section in a query."
            " / --search: Search and get the results in a query."
            " / --sections: Get all the sections of an article in a query."
            " / -l: Post an article from a specific language"
            " / --result: Select specific result."
            " <num> is the index of the result returned by --search"
            " / Use #section after the article's name to get a specific"
            " section. Example: .w irc#Technical information")
    manual = {
        "desc": ("Search wikipedia and post a snippet from the resulting"
                 " article."),
        "bot_commands": {
            "wikipedia": {"usage": lambda x: usage(x, "wikipedia"),
                          "info": info,
                          "alias": ["w", "wiki"]},
            "wiki": {"usage": lambda x: usage(x, "wiki"),
                     "info": info,
                     "alias": ["w", "wikipedia"]},
            "w": {"usage": lambda x: usage(x, "w"),
                  "info": info,
                  "alias": ["wikipedia", "wiki"]}
        }
    }


# ----- Global Constants ----- #
r_timeout = 10
bs4_parser = "html.parser"
settings_name = "wikipedia"
# ---------------------------- #


def mw_opensearch(query, url, max_results=1):
    '''
    Uses the MediaWiki API:Opensearch
    https://en.wikipedia.org/w/api.php?action=help&modules=opensearch

    Search MediaWiki for articles relevant to the search `query'
    It returns a [query, [titles], [descriptions], [urls]] list of relevant
    results to the search query.

    'query' is the string to search for
    'url' is the url of the MediaWiki website
    'max_results' is the maximum amount of results to get
    '''
    u = (f'{url}/w/api.php'
         f'?action=opensearch&format=json&limit={max_results}&search={query}')
    r = requests.get(u, timeout=r_timeout)
    return r.json()


def mw_list_sections(page, url):
    '''
    Uses the MediaWiki API:Parsing_wikitext#parse
    https://www.mediawiki.org/wiki/Special:MyLanguage/API:Parsing_wikitext#parse

    Get a list of all the available sections for a given article.
    Returns a tuple with the title of the article and a
    list [[sections],[indexes]]

    'page' should be the name of the MediaWiki article as returned
    by mw_opensearch()
    'url' is the url of the MediaWiki website
    '''
    u = f'{url}/w/api.php?action=parse&format=json&prop=sections&page={page}'
    r = requests.get(u, timeout=r_timeout)
    parse = r.json()
    title = parse['parse']['title']
    sections_ = parse['parse']['sections']
    section_list = [[], []]
    for i in sections_:
        section_list[0].append(i['line'])
        section_list[1].append(i['index'])
    return (title, section_list)


def text_cleanup(soup):
    try:
        for sup in soup('sup'):
            soup.sup.decompose()
    except AttributeError:
        pass
    try:
        for small in soup('small'):
            soup.small.decompose()
    except AttributeError:
        pass
    return soup


def mw_parse_intro(url, page, limit):
    '''
    Uses the MediaWiki API:Parsing_wikitext#parse
    https://www.mediawiki.org/wiki/Special:MyLanguage/API:Parsing_wikitext#parse

    This function calls the MediaWiki API, which returns a JSON
    document containing the html of the introduction section
    of an article, which is parsed by beautifulsoup4, limited
    to the specified amount of characters and returned.

    'url' is the url of the MediaWiki website
    'page' should be the name of the MediaWiki article as
    returned by mw_opensearch()
    'limit' if True truncate the text
    '''
    u = (f'{url}/w/api.php'
         f'?action=parse&format=json&prop=text&section=0&page={page}')
    r = requests.get(u, timeout=r_timeout)
    html = r.json()['parse']['text']['*']
    soup = bs4.BeautifulSoup(html, bs4_parser)
    soup = text_cleanup(soup)

    text = ""
    for p in soup.find_all('p'):
        text += p.text

    if text == 'Redirect to:':
        n_title = soup.find('a').text
        n_text = mw_parse_intro(url, n_title, limit)
        text = f'\x0302[Redirect to: {n_title}]\x0F {n_text}'
    if limit:
        text = p_truncate(text, msg_len, 85, True)
    return text


def mw_parse_section(url, section_list, page, sect, limit):
    '''
    Uses the MediaWiki API:Parsing_wikitext#parse
    https://www.mediawiki.org/wiki/Special:MyLanguage/API:Parsing_wikitext#parse

    This function finds the position of the section ('sect')
    requested in 'section_list' and calls the MediaWiki API,
    which returns a JSON document containing the html of the
    requested section which is parsed by beautifulsoup4,
    limited to the specified amount of characters and returned.

    'url' is the url of the MediaWiki website
    'section_list' is the second item returned by mw_list_sections()
    'page' should be the name of the MediaWiki article as
    returned by mw_opensearch()
    'sect' is the section requested to be viewed
    'limit' if True truncate the text
    '''
    id_index = section_list[0].index(sect)
    u = (f'{url}/w/api.php'
         '?action=parse&format=json&prop=text'
         f'&section={section_list[1][id_index]}&page={page}')
    r = requests.get(u, timeout=r_timeout)
    html = r.json()['parse']['text']['*']
    soup = bs4.BeautifulSoup(html, bs4_parser)
    soup = text_cleanup(soup)
    text = soup.find('span', id=sect)
    text = text.find_next('p').text
    if limit:
        text = p_truncate(text, msg_len, 85, True)
    return text


def str2url(url):
    return urllib.parse.quote_plus(url)


def language(argv, config, channel):
    '''Set the language used to search for wikipedia articles'''
    if '-l' in argv:
        # Check if the language command has been used and
        # use the given value instead of the configuration
        index = argv.index('-l')
        return argv[index + 1]
    else:
        settings = config.get_module_settings("wikipedia")
        try:
            return settings["lang"][channel]
        except KeyError:
            try:
                return settings["lang"]["default"]
            except KeyError:
                return 'en'  # Default if nothing is set.


def search_query(args):
    args = args.copy()
    cmds = ['--search', '--sections', '--full']
    cmds_args = ['--result', '-r', '-l']

    for i in cmds_args:
        try:
            idx = args.index(i)
            del args[idx]
            del args[idx]
        except ValueError:
            pass

    for i in cmds:
        try:
            idx = args.index(i)
            del args[idx]
        except ValueError:
            pass

    return ' '.join(args)


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if not args:
        m = (f'Usage: {prefix}{botcmd} <Article> '
             '[--full, --search, --sections -l], [--result <NUM>]')
        irc.out.notice(msgtarget, m)
        return

    argv = args.split()
    config = i.bot["conf"]

    lang = language(argv, config, msgtarget)

    mw_url = f'https://{lang}.wikipedia.org'
    logo = '\x0301,00Wikipedia\x0F'

    limit = True
    search_q = search_query(argv)

    global msg_len
    msg_len = irc.msg_len - 9 - 22

    if '--search' in argv:
        opensearch = mw_opensearch(search_q, mw_url, 10)
        rs_string = ''
        for n in opensearch[1]:
            rs_string += f'[{opensearch[1].index(n) + 1}:{n}] '
        m = (f'{logo}: \x0302[search results for: '
             f'{search_q}]\x0F: {rs_string}')
        irc.out.notice(nickname, m)
        return

    if '--full' in argv:
        limit = False
        msgtarget = nickname

    if '--result' in argv or '-r' in argv:
        try:
            r_index = argv.index('--result')
        except ValueError:
            r_index = argv.index('-r')
        os_limit = int(argv[r_index + 1])
        opensearch = mw_opensearch(search_q, mw_url, os_limit)
        try:
            title = opensearch[1][os_limit - 1]
        except IndexError:
            m = f'{logo}: No article was found for \x02{search_q}\x0F'
            irc.out.notice(msgtarget, m)
            return
    else:
        opensearch = mw_opensearch(search_q, mw_url, 1)
        try:
            title = opensearch[1][0]
        except IndexError:
            m = f'{logo}: No article was found for \x02{search_q}\x0F'
            irc.out.notice(msgtarget, m)
            return

    wikiurl = f'{mw_url}/wiki/{title.replace(" ", "_")}'

    if '--sections' in argv:
        sections_out = mw_list_sections(title, mw_url)
        sec_out_str = ' | '.join(sections_out[1][0])
        m = (f'{logo}: \x0302 [sections for {sections_out[0]}]\x0F: '
             f'{sec_out_str} [ {wikiurl} ]')
        irc.out.notice(nickname, m)
    elif '#' in search_q:
        ts_list = search_q.split('#')
        sections_out = mw_list_sections(title, mw_url)
        snippet = mw_parse_section(
            mw_url, sections_out[1], title, ts_list[1], limit)
        m = f'{logo}: \x02{title}#{ts_list[1]}\x0F | {snippet} | {wikiurl}'
        irc.out.notice(msgtarget, m)
    else:
        snippet = mw_parse_intro(mw_url, title, limit)
        m = f'{logo}: \x02{title}\x0F | {snippet} | {wikiurl}'
        irc.out.notice(msgtarget, m)
