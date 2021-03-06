import os
from urllib.parse import urlparse

DB_URL = os.environ.get('DATABASE_URL')
PARSED_URL = urlparse(DB_URL)

class InvalidEnvironVariableError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "INVALID ENV_VAR: "+self.msg

bot_token = os.environ.get('BOTTOKEN')

if bot_token is None:
    raise InvalidEnvironVariableError('BOTTOKEN')

DATABASE = {
    "DATABASE_HOST": PARSED_URL.hostname,
    "DATABASE": PARSED_URL.path[1:],
    "DATABASE_USER": PARSED_URL.username,
    "DATABASE_PORT": PARSED_URL.port,
    "DATABASE_PASSWORD": PARSED_URL.password
}

apps = [
    'cogs.tag.default',
    'cogs.bookmarks.default',
    'cogs.base'
]

tester_ids = [
    "981191793083306074"
]

admin_guild_id = [
    "981191793083306074"
]

manage_channel_id = "981195630305214536"

embed_supporter_text = "[밥주세요](https://buymeacoffee.com/sservekr)"

print("Config loaded.")