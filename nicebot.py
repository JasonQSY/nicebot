from slacker import Slacker
import psutil
import socket
import os


def main():
    token = os.environ['NICEBOT_TOKEN']
    slack = Slacker(token)
    procs = psutil.process_iter(attrs=['pid', 'name', 'username','nice'])
    hostname = socket.gethostname()
    prefix = "Performing nice scan on {}: ".format(hostname)
    message = prefix + '\n```'
    cnt = 0
    for p in procs:
        info = p.info
        if 'python' not in info['name']:
            continue
        proc = psutil.Process(pid=info['pid'])
        nice = proc.nice()
        if nice < 10:
            message += str(info) + '\n'
            cnt += 1
    # Send a message to #general channel
    message += '```'
    if cnt > 0:
        slack.chat.post_message('#nicebot', message)
    else:
        slack.chat.post_message('#nicebot', prefix + "very nice!")


if __name__=='__main__':
    main()
