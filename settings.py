post_template = '''Hi, I'm a glossing bot!

Here is my analysis:

%s'''
    
text_template = '''**Glossed text:**

%s

**Result:**

%s
'''

settings = {
    'user-agent': 'IthkuilGlosser by ebvalaim v0.1',
    'app_key': '',          # FILL IN
    'app_secret': '',       # FILL IN
    'scopes': ['identity', 'read', 'submit'],
    'access_token': '',     # FILL IN (from onetime.py)
    'refresh_token': '',    # FILL IN (from onetime.py)
    'subreddit': 'test',    
    'marker': '@gloss',     # marks a paragraph to be glossed
    # template of a glossing post
    'post_template': post_template,
    'text_template': text_template,
}
