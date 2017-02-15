#!/usr/bin/env python3

###################################
#   Instant Runoff Vote Counter   #
###################################

# Written by Avery Robinson to count name votes for the Snitchcock Scav team.

import csv
from optparse import OptionParser
import re

# Options and usage
usage = "%prog [options] file i j\n" \
    "    `file` is the CSV file from Google Forms.\n" \
    "    `i` is the index of the first results column.\n" \
    "    `j` is the index of the last results column."
parser = OptionParser(usage=usage)
parser.add_option("-p", "--pattern", dest="regex",
        help="A regular expression to find the relevant part of the option " \
        "name.", default=None)
parser.add_option("-d", "--depth", dest="recursion_limit",
        help="Integer. The maximum depth of recursion to use to break ties " \
        "for last. Cannot be set less than 1.", default=None)
parser.add_option("-r", "--reckless", action="store_true", dest="reckless",
        help="This option hurts democracy. When running under reckless mode " \
        "ties are broken in a non-deterministic way.", default=False)
(options, args) = parser.parse_args()

# Usage message
if len(args) < 3:
    parser.error("Not enough arguments were supplied")

filename = args[0]
i = int(args[1])
j = int(args[2])

class Vote(object):
    '''Represents a vote.'''

    def __init__(self, titles, i, j, line, do_nothing=False):
        '''Sets self.preferences to be a list of this vote's preferences, in
        order.'''
        if do_nothing:
            return
        ranks = [int(x) for x in line[i:j+1]]
        decorated_titles = list(enumerate(titles))
        decorated_titles.sort(key=lambda it: ranks[it[0]])
        self.preferences = [t for (i,t) in decorated_titles]

    def remove(self, title):
        '''Removes the title from preference list.'''
        self.preferences = list(filter(lambda t: t != title, self.preferences))

    def first_choice(self):
        '''Returns this vote's first choice.'''
        if len(self.preferences) >= 1:
            return self.preferences[0]
        else:
            return None

    def dup(self):
        '''Returns a duplicate of self.'''
        ret = Vote(None, None, None, None, do_nothing=True)
        ret.preferences = self.preferences
        return ret

    def filter(self, titles):
        '''Produces a NEW Vote object with only titles in the preference list.'''
        prefs_prime = list(filter(lambda t: t in titles, self.preferences))
        copy = Vote(None, None, None, None, do_nothing=True)
        copy.preferences = prefs_prime
        if len(copy.preferences) > 0:
            return copy
        else:
            return None

def instant_runoff(votes, verbose=True, recursion_limit=5, reckless=False):
    '''Actually does the instant-runoff process.'''
    n = len(votes)
    round = 1
    results = []

    # Reckless warning
    if reckless and verbose:
        print("WARNING: You are using the --reckless option. Results may not " \
                "be well-defined.")

    while 1:
        tally = {}
        for vote in votes:
            favorite = vote.first_choice()
            if favorite:
                if favorite not in tally:
                    tally[favorite] = 0
                tally[favorite] += 1
        if verbose:
            print("Round {}:".format(round))
            for k, v in tally.items():
                print("    {}:\t{} votes".format(k, v))

        # Find if there is a majority
        for k, v in tally.items():
            if v >= n // 2 + 1:
                if verbose:
                    print("{} is the winner.".format(k))
                results.insert(0, k)
                return results
        
        # Find last place
        lowest_vote_count = n
        for k, v in tally.items():
            if v < lowest_vote_count:
                lowest_vote_count = v
        losers = []
        for k, v in tally.items():
            if v == lowest_vote_count:
                losers.append(k)

        # If we have one loser, it's easy to figure out who it is
        if len(losers) == 1:
            loser = losers[0]

        # Reckless
        elif len(losers) > 1 and reckless:
            loser = losers[0]

        # Multiple losers, but out of recursion
        elif len(losers) > 1 and recursion_limit <= 0:
            print("ERROR: Reached recursion limit.")
            return None

        # Multiple losers, but we can recurse
        elif len(losers) > 1 and recursion_limit > 0:
            sub_result = None
            changed = False
            for this_loser in losers:
                votes_prime = []
                for vote in votes:
                    vote_prime = vote.dup()
                    vote_prime.remove(this_loser)
                    votes_prime.append(vote_prime)
                this_sub_results = instant_runoff(votes_prime, verbose=False,
                        recursion_limit=recursion_limit-1, reckless=reckless)
                if this_sub_results != None and len(this_sub_results) >= 1:
                    this_sub_result = this_sub_results[0]
                else:
                    this_sub_result = None
                if sub_result == None:
                    sub_result = this_sub_result
                elif sub_result != this_sub_result:
                    sub_result = None
                    break

            if sub_result != None:
                loser = losers[0]
            else:
                if verbose:
                    print("ERROR: Instant-runoff failed. Winner " \
                            "cannot be determined.")
                    print("       Run with --reckless to see results anyway.")
                return None

        else:
            print("ERROR: this should never happen")
            exit()

        # Eliminate loser
        for vote in votes:
            vote.remove(loser)
        results.insert(0, loser)
        if verbose:
            print("{} is eliminated.".format(loser))
        round += 1

        if verbose:
            print()

# Read CSV file
with open(filename, 'r') as f:
    reader = csv.reader(f)

    # Get field titles
    title_line = reader.__iter__().__next__()
    titles = title_line[i:j+1]

    # Apply regex if necessary
    if options.regex != None:
        new_titles = []
        for title in titles:
            m = re.search(options.regex, title)
            if m:
                new_title = m.group(0)
            else:
                new_title = title
            new_titles.append(new_title)
        titles = new_titles

    # Iterate over remaining lines
    votes = []
    for line in reader:
        votes.append(Vote(titles, i, j, line))

args = {}
if options.recursion_limit != None and int(options.recursion_limit) >= 1:
    args['recursion_limit'] = int(options.recursion_limit)
args['reckless'] = options.reckless

instant_runoff(votes, **args)
