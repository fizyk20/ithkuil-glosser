#!/usr/bin/env python
import praw
import time
from settings import settings
from ithkuil.morphology import fromString
from ithkuil.morphology.exceptions import IthkuilException

class CommentLog:
    
    ID_LENGTH = 6  # ids have length 6
    
    def __init__(self, filename):
        self.readComments = set()
        self.filename = filename
        try:
            with open(filename, 'r') as f:
                for line in f:
                    if len(line) >= self.ID_LENGTH:
                        self.readComments.add(line[0:6])
        except FileNotFoundError:
            return  # we'll just continue with an empty list
                    
    def markRead(self, comment):
        if len(comment) != self.ID_LENGTH:
            return
        self.readComments.add(comment)
        
    def save(self):
        with open(self.filename, 'w') as f:
            for comment in self.readComments:
                f.write(comment + '\n')
                
    def contains(self, comment):
        return comment in self.readComments
    
def parseComment(comment):
    blocks = comment.split('\n\n')
    return [x[1:] for x in map(lambda y: y.split(), blocks) if x[0] == settings['marker']]

def handleComment(comment):
    words = parseComment(comment.body)
    result = []
    for word in words:
        try:
            wordObj = fromString(word)
            result .append('%s: %s' % (wordObj.word, wordObj.abbreviatedDescription()))
        except IthkuilException as e:
            result.append('%s: ERROR: %s' % (word, e))
            continue
    if result:
        comment.reply(settings['post_template'] % result)

    return len(result)

r = praw.Reddit(user_agent=settings['user-agent'])
r.login(username=settings['username'], password=settings['password'], disable_warning=True)

readComments = CommentLog('readComments-%s.txt' % settings['subreddit'])

try:
    while True:
        sub = r.get_subreddit(settings['subreddit'])
        counter = 0
        handledComments = 0
        for submission in sub.get_hot(limit=10):
            comments = praw.helpers.flatten_tree(submission.comments)
            for comment in comments:
                if not readComments.contains(comment.id):
                    counter += handleComment(comment)
                    handledComments += 1
                    readComments.markRead(comment.id)
        print('Comments handled this pass: %s, words processed: %s\n' % (handledComments, counter))
        time.sleep(10)
finally:
    readComments.save()
