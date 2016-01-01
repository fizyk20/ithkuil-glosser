#!/usr/bin/env python
import praw
import time
from settings import settings
from ithkuil.morphology import fromString
from ithkuil.morphology.exceptions import IthkuilException
from argparse import ArgumentError

class CommentLog:
    
    ID_LENGTH = 7  # ids have length 6
    
    def __init__(self, filename):
        self.readComments = set()
        self.filename = filename
        try:
            with open(filename, 'r') as f:
                for line in f:
                    if len(line) >= self.ID_LENGTH:
                        self.readComments.add(line[0:self.ID_LENGTH])
        except FileNotFoundError:
            return  # we'll just continue with an empty list
                    
    def markRead(self, comment):
        if len(comment) != self.ID_LENGTH:
            raise ArgumentError('Invalid comment id: %s' % comment)
        self.readComments.add(comment)
        
    def save(self):
        with open(self.filename, 'w') as f:
            for comment in self.readComments:
                f.write(comment + '\n')
                
    def contains(self, comment):
        return comment in self.readComments
    
def parseComment(comment):
    blocks = comment.split('\n\n')
    
    def words(block):
        return block.split()
    
    def toBeHandled(block):
        return len(block) > 1 and block[0] == settings['marker']
    
    return [block[1:] for block in map(lambda x: words(x), blocks) if toBeHandled(block)]

def generateResponseText(postText):
    blocks = parseComment(postText) # returns a list of lists of words
    result = []
    for block in blocks:
        # each list of words is a text to gloss
        blockResult = []
        for word in block:
            try:
                wordObj = fromString(word)
                blockResult.append('* %s: %s' % (wordObj.word, wordObj.abbreviatedDescription()))
            except IthkuilException as e:
                blockResult.append('* %s: ERROR: %s' % (word, e))
                continue
        
        result.append(settings['text_template'] % (' '.join(block), '\n'.join(blockResult)))
    
    if result: 
        return settings['post_template'] % '\n\n'.join(result)
    else:
        return None

def handleComment(comment):
    result = generateResponseText(comment.body)
    if result:
        comment.reply(result)

    return len(result)

r = praw.Reddit(user_agent=settings['user-agent'])
r.login(username=settings['username'], password=settings['password'], disable_warning=True)

readComments = CommentLog('readComments-%s.txt' % settings['subreddit'])

running = True

while running:
    try:
        sub = r.get_subreddit(settings['subreddit'])
        counter = 0
        handledComments = 0
        for comment in sub.get_comments():
            if not readComments.contains(comment.id):
                counter += handleComment(comment)
                handledComments += 1
                try:
                    readComments.markRead(comment.id)
                except ArgumentError as e:
                    print(e)
        print('Comments handled this pass: %s, words processed: %s' % (handledComments, counter))
        time.sleep(10)
    # stop on ctrl-c
    except KeyboardInterrupt:
        running = False
    # if limit exceeded, wait some more
    except praw.errors.RateLimitExceeded as e:
        print('Rate limit exceeded, waiting %s seconds' % e.sleep_time)
        time.sleep(e.sleep_time)

readComments.save()
