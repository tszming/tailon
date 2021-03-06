import os

from time import time, sleep
from random import choice, randint
from datetime import datetime as dt
from threading import Thread, Lock
from functools import partial

agents = (
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.65 Safari/537.31',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/536.29.13 (KHTML, like Gecko) Version/6.0.4 Safari/536.29.13',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31',
    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31',
    'Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.15',
)

paths = (
    '/js/app/app.js',
    '/js/app/router.js',
    '/js/app/model/User.js',
    '/js/app/model/Chat.js',
    '/js/app/model/ChatMessage.js',
    '/js/app/view/NavView.js',
    '/js/app/view/AppView.js',
    '/js/app/view/TrackView.js',
    '/js/app/view/ChatView.js',
    '/js/app/view/HomeView.js',
    '/js/app/view/DiscoverView.js',
    '/js/app/view/SignupView.js',
    '/js/app/view/CreateRoomView.js',
    '/js/app/view/ListenersView.j',
    '/js/app/view/LoginView.js',
    '/index.html',
)

methods = 'POST', 'GET', 'HEAD'
codes = 304, 404, 300, 400, 200
logfmt = '[{now:%d/%b/%Y:%H:%M:%S %z}] "{method} {path} HTTP/1.1" {status} 0 "{agent}"\n'

def generate_logtext():
    while True:
        yield logfmt.format(
            now=dt.now(),
            method=choice(methods),
            path=choice(paths),
            status=choice(codes),
            agent=choice(agents),
            )


class LogFile:
    def __init__(self, fn, mode='w', rate=(1,4), update_msec=(500,1000), truncate_msec=10000):
        self.update_msec = update_msec
        self.truncate_msec = truncate_msec
        self.rate = rate
        self.writelock = Lock()

        self.gen = generate_logtext()
        self.fh = open(fn, mode)

        self.write_t = Thread()
        self.write_t.run = partial(self.run, self.write, update_msec)
        self.truncate_t = Thread()
        self.truncate_t.run = partial(self.run, self.truncate, truncate_msec)

        self.threads = (self.write_t, self.truncate_t)
        self.running = True

    def start(self):
        msg = 'simulating "%s", write %smsec, truncate %smsec'
        print(msg % (self.fh.name, self.update_msec, self.truncate_msec))

        self.write_t.start()
        if self.truncate_msec:
            self.truncate_t.start()

    def stop(self):
        self.running = False

    def join(self):
        for t in self.threads:
            t.join()

    def run(self, cb, interval):
        while self.running:
            cb()
            interval = randint(*interval) if isinstance(interval, (tuple, list)) else interval 
            sleep(interval/1000.)

    def write(self):
        n = self.rate
        n = randint(*n) if isinstance(n, (tuple, list)) else n

        with self.writelock:
            for i in range(n):
                line = next(self.gen)
                self.fh.write(line)
            self.fh.flush()

    def truncate(self):
        with self.writelock:
            self.fh.close()
            self.fh = open(self.fh.name, 'w')


class LogFiles:
    def __init__(self, files, rate, update_msec, truncate_msec):
        self.files = files
        for fn in files:
            dn = os.path.dirname(fn)
            if not os.path.exists(dn):
                os.makedirs(dn)

        self.logfiles = [LogFile(fn, 'w', rate, update_msec, truncate_msec) for fn in files]

    def start(self):
        for i in self.logfiles:
            i.start()

    def stop(self):
        for i in self.logfiles:
            i.stop()


if __name__ == '__main__':
    import argparse

    t_or_i = lambda s: [int(i) for i in s.split(',')] if ',' in s else int(s)

    p = argparse.ArgumentParser()
    p.add_argument('--update-msec', default=1000, type=t_or_i)
    p.add_argument('--truncate-msec', default=10000, type=t_or_i)
    p.add_argument('--rate', default=1, type=t_or_i)
    p.add_argument('mode', choices=('log',))
    p.add_argument('action', choices=('start', 'stop'))
    p.add_argument('files', nargs=argparse.REMAINDER)

    opts = p.parse_args()
    if opts.mode == 'log' and opts.action == 'start':
        l = LogFiles(opts.files, opts.rate, opts.update_msec, opts.truncate_msec)
        l.start()
