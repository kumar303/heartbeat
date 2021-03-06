from contextlib import contextmanager
from datetime import datetime
import json
import optparse
import os
import re
import subprocess
import time
import traceback

import daemon
import requests

space = re.compile(r'[\t ]+')
DATA_DIR = None  # set by options in main()


class Dstat:
    whitespace = re.compile(r'\s+')
    cols = ('--cpu', '--disk', '--mem', '--net', '--load', '--page',
            '--sys', '--proc', '--io', '--fs', '--proc-count',
            '--top-cpu', '--top-mem')

    def __init__(self):
        self.cmd = 'dstat %s --nocolor 1 1' % ' '.join(self.cols)

    def parse(self, lines):
        hdr = lines.pop(0)
        # Ignore the header but assert that it's there.
        if not hdr.startswith('-'):
            raise ValueError('Expected a header: %s' % hdr)

        data = {}
        legend = lines.pop(0).split('|')
        if len(legend) != len(self.cols):
            raise ValueError('Unexpected legend %r for cols: %r' % (legend,
                                                                    self.cols))
        avg = lines.pop(0).split('|')
        data['average'] = self._line(self.cols, legend, avg)
        sample = lines.pop(0).split('|')
        data['sample'] = self._line(self.cols, legend, sample)
        return data

    def sample(self):
        cmd = 'dstat %s --nocolor 1 1' % ' '.join(self.cols)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        ret = p.wait()
        assert ret == 0
        return self.parse([self._clean_line(ln)
                           for ln in p.stdout.readlines()])

    def _clean_line(self, ln):
        return ln.strip().replace('\x1b[7l', '')

    def _line(self, cols, legend, line):
        data = {}
        for i, cflag in enumerate(cols):
            if not cflag.startswith('--'):
                raise ValueError('Unexpected column flag: %s' % cflag)
            cname = cflag[2:]
            data[cname] = self._extract_line(legend[i], line[i])
        return data

    def _extract_line(self, legend, line):
        legend = self.whitespace.split(legend.strip())
        line = self.whitespace.split(line.strip())
        if len(legend) != len(line):
            # e.g. legend: ['cpu', 'process'], line: ['']
            # Return an empty dict. TODO: Maybe log this?
            line = [None for ln in legend]

        return dict(zip(legend, line))


def daemonize(main, args=[], kw={},
              pidfile='/var/run/daemon.pid',
              log='/var/log/daemon.log'):

    @contextmanager
    def pidfile_ctx():
        with open(pidfile, 'w') as f:
            f.write(str(os.getpid()))
        yield
        os.unlink(f.name)

    out = open(log, 'w+')

    with daemon.DaemonContext(pidfile=pidfile_ctx(),
                              stdout=out, stderr=out):
        print 'starting daemon at %s' % datetime.now()
        main(*args, **kw)


class Data(object):

    def __init__(self):
        self.dir = DATA_DIR
        if not self.dir:
            raise EnvironmentError('DATA_DIR was empty')
        if not os.path.exists(self.dir):
            raise EnvironmentError('DATA_DIR %s does not exist' % self.dir)

    def get_id(self):
        if not os.path.exists(self.file('id.txt')):
            return False
        else:
            with open(self.file('id.txt')) as f:
                return f.read()

    def set_id(self, val):
        with open(self.file('id.txt'), 'w') as f:
            f.write(str(val))
        return val

    def file(self, path):
        return os.path.join(self.dir, path)


def update(data, request):
    pass


def loop(server=None, tick=3):
    data = Data()
    id = data.get_id()
    backoff = tick * 5
    while 1:
        try:
            if not id:
                res = requests.get('%s/hello' % server)
                id = data.set_id(res.json()['id'])

            dstat = Dstat()
            status = dstat.sample()
            packet = {'status': status,
                      'ip_addr': get_ip_addr()}
            res = requests.post('%s/heartbeat/%s' % (server, id),
                                data=json.dumps(packet),
                                headers={'content-type': 'application/json'})
            result = res.json()
            if result['update']:
                update(data, result['update'])
        except SystemExit:
            raise
        except:
            traceback.print_exc()
            time.sleep(backoff)
        time.sleep(tick)


def get_ip_addr():
    try:
        ifc = subprocess.check_output('ifconfig wlan0', shell=True)
    except subprocess.CalledProcessError:
        traceback.print_exc()
        return None
    pat = re.compile(r'inet addr:([^\s]+)')
    for line in ifc.split('\n'):
        m = pat.search(line)
        if m:
            return m.groups()[0]


def main():
    global DATA_DIR
    p = optparse.OptionParser(usage='%prog [options]')
    p.add_option('--id', help='Print device ID and exit. The ID may be blank.',
                 action='store_true')
    p.add_option('-d', '--daemon', help='Run as daemon.',
                 action='store_true')
    p.add_option('-p', '--pidfile', help='PID file path. Default: %default',
                 default='/var/run/heartbeat.pid')
    p.add_option('-l', '--log', help='Custom log file. Default: %default',
                 default='/var/log/heartbeat.log')
    p.add_option('-s', '--server', help='Server. Default: %default',
                 default='http://10.0.1.15:5000')
    p.add_option('-t', '--tick', help='Seconds to sleep in the main loop',
                 type=int, default=10)
    p.add_option('--data_dir', action='store', default='/etc/heartbeat',
                 help='Custom data dir. This must be writable. '
                      'Default: %default')
    (options, args) = p.parse_args()
    DATA_DIR = options.data_dir

    if options.id:
        data = Data()
        print data.get_id() or ''
        return

    kw = dict(server=options.server, tick=options.tick)
    if options.daemon:
        daemonize(loop, kw=kw, pidfile=options.pidfile, log=options.log)
    else:
        loop(**kw)


if __name__ == '__main__':
    main()
