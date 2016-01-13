#!/usr/bin/env python
import praw
from prawoauth2 import PrawOAuth2Mini
import time
from datetime import datetime
from settings import settings
from ithkuil.morphology.words import Factory
from ithkuil.morphology.exceptions import IthkuilException
from praw.errors import OAuthInvalidToken

def log(*args, **kwargs):
    now = datetime.now()
    print(now.strftime('[%Y-%m-%d %H:%M:%S]'), *args, **kwargs)

class CommentLog:
    
    def __init__(self, filename):
        self.readComments = set()
        self.filename = filename
        try:
            with open(filename, 'r') as f:
                for line in f:
                    self.readComments.add(line.rstrip())
        except FileNotFoundError:
            return  # we'll just continue with an empty list
                    
    def markRead(self, comment):
        self.readComments.add(comment)
        with open(self.filename, 'a') as f:
            f.write(comment + '\n')
        
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
    counter = 0
    for block in blocks:
        # each list of words is a text to gloss
        blockResult = []
        for word in block:
            try:
                wordObj = Factory.parseWord(word)
                blockResult.append('* %s: %s' % (wordObj.word, wordObj.abbreviatedDescription()))
            except IthkuilException as e:
                blockResult.append('* %s: ERROR: %s' % (word, e))
                continue
        
        result.append(settings['text_template'] % (' '.join(block), '\n'.join(blockResult)))
        counter += len(blockResult)
    
    if result: 
        return settings['post_template'] % '\n\n'.join(result), counter
    else:
        return None, 0
    
def handleSubmission(submission):
    if not submission.selftext:
        return 0
    result, counter = generateResponseText(submission.selftext)
    if result:
        submission.add_comment(result)
        
    return counter

def handleComment(comment):
    result, counter = generateResponseText(comment.body)
    if result:
        comment.reply(result)

    return counter

r = praw.Reddit(user_agent=settings['user-agent'])

oauth_helper = PrawOAuth2Mini(r, app_key=settings['app_key'],
                               app_secret=settings['app_secret'],
                               access_token=settings['access_token'],
                               refresh_token=settings['refresh_token'], scopes=settings['scopes'])

readComments = CommentLog('readComments-%s.txt' % settings['subreddit'])

running = True

while running:
    try:
        sub = r.get_subreddit(settings['subreddit'])
        counter = 0
        handledComments = 0
        
        for submission in sub.get_hot(limit=10):
            if not readComments.contains(submission.id):
                counter += handleSubmission(submission)
                handledComments += 1
                readComments.markRead(submission.id)
            
        for comment in sub.get_comments():
            if not readComments.contains(comment.id):
                counter += handleComment(comment)
                handledComments += 1
                readComments.markRead(comment.id)
        log('Comments handled this pass: %s, words processed: %s' % (handledComments, counter))
        time.sleep(10)
    # stop on ctrl-c
    except KeyboardInterrupt:
        running = False
    # if limit exceeded, wait some more
    except praw.errors.RateLimitExceeded as e:
        log('Rate limit exceeded, waiting %s seconds' % e.sleep_time)
        time.sleep(e.sleep_time)
    # sometimes a HTTPError is thrown - just wait a bit
    except praw.errors.HTTPException:
        log('HTTPError - waiting 30 seconds')
        time.sleep(30)
    # refresh token on OAuthInvalidToken
    except OAuthInvalidToken:
        log('Refreshing token')
        oauth_helper.refresh()
    # other exceptions
    except Exception as e:
        log('Other exception: %s - waiting 60 seconds' % str(e))
        time.sleep(60)

readComments.save()
