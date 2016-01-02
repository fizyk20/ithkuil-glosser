#!/usr/bin/env python
import praw
from prawoauth2 import PrawOAuth2Server
from settings import settings

r = praw.Reddit(user_agent=settings['user-agent'])

oauthserver = PrawOAuth2Server(r, settings['app_key'], settings['app_secret'],
                                state=settings['user-agent'], scopes=settings['scopes'])

oauthserver.start()

print(oauthserver.get_access_codes())