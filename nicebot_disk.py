from slacker import Slacker
import psutil
import sys
import os
import re
import subprocess
import select


def main():
    token = os.environ['NICEBOT_TOKEN']
    slack = Slacker(token)

    # collect gpu info
    message = '```'
    message += '```'

    if cnt > 0:
        slack.chat.post_message('#nicebot-dev', message)
    else:
        slack.chat.post_message('#nicebot-dev', "very nice in this scan!")


if __name__=='__main__':
    main()
