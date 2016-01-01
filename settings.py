post_template = '''Hi, I'm a glossing bot!

Here is my analysis:

%s'''
    
text_template = '''**Glossed text:**

%s

**Result:**

%s
'''

settings = {
    'username': 'IthkuilGlosser',
    'user-agent': 'IthkuilGlosser by ebvalaim v0.1',
    'password': '',         # change in production
    'subreddit': 'test',    # change in production
    'marker': '@gloss',     # marks a paragraph to be glossed
    # template of a glossing post
    'post_template': post_template,
    'text_template': text_template
}
