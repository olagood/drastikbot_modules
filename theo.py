#!/usr/bin/env python3
# coding=utf-8

# Quotes from mg's theo.c
# http://cvsweb.openbsd.org/cgi-bin/cvsweb/src/usr.bin/mg/Attic/theo.c

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
    bot_commands = ['theo']
    manual = {
        "desc": ("Post quotes from OpenBSD mg's theo.c mode. This mode has"
                 " been removed from mg. This module includes all the"
                 " quotes from the last commit to theo.c before it was"
                 " removed: "
                 "http://cvsweb.openbsd.org/cgi-bin/cvsweb/src/usr.bin/"
                 "mg/Attic/theo.c"),
        "bot_commands": {"theo": {"usage": lambda x: f"{x}theo"}}
    }


talk = [
    "Write more code.",
    "Make more commits.",
    "That's because you have been slacking.",
    "slacker!",
    "That's what happens when you're lazy.",
    "idler!",
    "slackass!",
    "lazy bum!",
    "Stop slacking you lazy bum!",
    "slacker slacker lazy bum bum bum slacker!",
    "I could search... but I'm a lazy bum ;)",
    "sshutup sshithead, ssharpsshooting susshi sshplats ssharking assholes.",
    "Lazy bums slacking on your asses.",
    "35 commits an hour? That's pathetic!",
    "Fine software takes time to prepare. Give a little slack.",
    "I am just stating a fact",
    "you bring new meaning to the terms slackass. I will have to invent a new term.",
    "if they cut you out, muddy their back yards",
    "Make them want to start over, and play nice the next time.",
    "It is clear that this has not been thought through.",
    "avoid using abort(). it is not nice.",
    "That's the most ridiculous thing I've heard in the last two or three minutes!",
    "I'm not just doing this for crowd response. I need to be right.",
    "I'd put a fan on my bomb.. And blinking lights...",
    "I love to fight",
    "No sane people allowed here. Go home.",
    "you have to stop peeing on your breakfast",
    "feature requests come from idiots",
    "henning and darren / sitting in a tree / t o k i n g / a joint or three",
    "KICK ASS. TIME FOR A JASON LOVE IN! WE CAN ALL GET LOST IN HIS HAIR!",
    "shame on you for following my rules.",
    "altq's parser sucks dead whale farts through the finest chemistry pipette's",
    "screw this operating system shit, i just want to drive!",
    "Search for fuck. Anytime you see that word, you have a paragraph to write.",
    "Yes, but the ports people are into S&M.",
    "Buttons are for idiots.",
    "We are not hackers. We are turd polishing craftsmen.",
    "who cares. style(9) can bite my ass",
    "It'd be one fucking happy planet if it wasn't for what's under this fucking sticker.",
    "I would explain, but I am too drunk.",
    "you slackers don't deserve pictures yet",
    "Vegetarian my ass",
    "Wait a minute, that's a McNally's!",
    "don't they recognize their moral responsibility to entertain me?",
    "#ifdef is for emacs developers.",
    "Many well known people become net-kooks in their later life, because they lose touch with reality.",
    "You're not allowed to have an opinion.",
    "tweep tweep tweep",
    "Quite frankly, SSE's alignment requirement is the most utterly retarded idea since eating your own shit.",
    "Holy verbose prom startup Batman.",
    "Any day now, when we sell out.",
    "optimism in man kind does not belong here",
    "First user who tries to push this button, he pounds into the ground with a rant of death.",
    "we did farts. now we do sperm. we are cutting edge.",
    "the default configuration is a mixture of piss, puke, shit, and bloody entrails.",
    "Stop wasting your time reading people's licenses.",
    "doing it with environment variables is OH SO SYSTEM FIVE LIKE OH MY GOD PASS ME THE SPOON",
    "Linux is fucking POO, not just bad, bad REALLY REALLY BAD",
    "penguins are not much more than chickens that swim.",
    "i am a packet sniffing fool, let me wipe my face with my own poo",
    "Whiners. They scale really well.",
    "in your world, you would have a checklist of 50 fucking workarounds just to make a coffee.",
    "for once, I have nothing to say.",
    "You have no idea how fucked we are",
    "You can call it fart if you want to.",
    "wavelan is a battle field",
    "You are in a maze of gpio pins, all alike, all undocumented, and a few are wired to bombs.",
    "And that is why humppa sucks... cause it has no cause.",
    "cache aliasing is a problem that would have stopped in 1992 if someone had killed about 5 people who worked at Sun.",
    "Don't spread rumours about me being gentle.",
    "If municipal water filtering equipment was built by the gcc developers, the western world would be dead by now.",
    "kettenis supported a new machine in my basement and all I got to do was fix a 1 character typo in his html page commit.",
    "industry told us a lesson: when you're an asshole, they mail you hardware",
    "I was joking, really. I think I am funny :-)",
    "the kernel is a harsh mistress",
    "Have I ever been subtle? If my approach ever becomes subtle, shoot me.",
"the acpi stabs you in the back. the acpi stabs you in the back. you die ...",
    "My cats are more observant than you.",
    "our kernels have no bugs",
    "style(9) has all these fascist rules, and i have a problem with some of them because i didn't come up with them",
    "I'm not very reliable",
    "I don't like control",
    "You aren't being conservative -- you are trying to be a caveman.",
    "nfs loves everyone",
    "basically, dung beetles fucking. that's what kerberosV + openssl is like",
    "I would rather run Windows than use vi.",
    "if you assign that responsibility to non-hikers I will walk over and cripple you now.",
    "i ojbect two yoru splelng of achlhlocis.",
    "We have two kinds of developers - those that deal with their own shit and those that deal with other people's shit.",
    "If people keep adding such huge stuff, soon mg will be bigger than emacs.",
    "this change comes down to: This year, next year, 5 years from now, 10 years from now, or Oh fuck.",
    "backwards compatibility is king, and will remain king, until 2038.",
    "I don't know if the Internet's safe yet.",
    "Those who don't understand Unix are condemned to reinvent Multics in a browser",
    "Don't tell anybody I said that.",
    "Complaint forms are handled in another department.",
    "You'd be safer using Windows than the code which was just deleted.",
    "Shit should not be shared.",
    "the randomization in this entire codebase is a grand experiment in stupid",
    "My mailbox is full of shock.",
    "my integer overflow spidey senses are tingling.",
    "I'm just trying to improve the code...",
    "It's a pleasure to work on code you can't make worse.",
    "It's largely bad style to do (int)sizeof",
    "When I see Makefile.in, I know that \"in\" is short for \"insane\".",
    "This is the beer. And that's why we need a hackathon.",
    "Kill the past with fire, and declare Duran Duran is less cool today. Await remixes of the same thing performed by new talent.",
    "Where did my \"fuck backwards compat\" compatriots go?",
    "I want a new vax, one that's not so slow.",
    "This sausage is made from unsound meat.",
    "The people who wrote this code are not on your side.",
    "Well finally everyone can see that the shit is really shitty.",
    "All that complexity stopped us from getting flying cars by today."
]


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()

    msg = f"{nickname}: {random.SystemRandom().choice(talk)}"
    irc.out.notice(msgtarget, msg)
