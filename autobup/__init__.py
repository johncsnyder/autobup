import sys
import os
import glob
import argparse
import re
import logging
# import logging.handlers
import subprocess
from subprocess import Popen, PIPE
from fsevents import Stream
from fsevents import Observer


class Repo:

    def __init__(self, path):
        self.path           = path
        assert os.path.isdir(path), 'repo must be a directory'
        self.repo_name      = os.path.basename(path)  # default, should had option in config file
        self.logger         = logging.getLogger(self.repo_name)
        self.stream         = Stream(self.callback, path, file_events=True)
        self.bupignore_path = os.path.join(self.path, '.bupignore')

        # inital index / save
        self.update_bupignore()
        self.index()
        self.save()

    def update_bupignore(self):
        self.logger.info('updating .bupignore')
        self.bupignore = os.path.exists(self.bupignore_path)
        self.logger.info('.bupignore %s' % ('exists' if self.bupignore else 'does not exist'))
        if self.bupignore:
            with open(self.bupignore_path, 'r') as f:
                patterns = set(path.strip() for path in f)
            
            pattern = '|'.join(('(%s)' % p.replace('*', r'[^\/]+') for p in patterns))
            # self.logger.info("ignored = %s" % pattern)
            self.ignored = re.compile(pattern)

    def index(self, path='.'):
        cmd = 'bup index -vv {ignore} "{path}"'.format(
            ignore = '--exclude-from .bupignore' if self.bupignore else '',
            path   = path
        )

        self.logger.info('Indexing `%s`' % path)
        # self.logger.debug('    %s' % cmd)
        self.run_command(cmd)

    def save(self):
        cmd = 'bup save -vv --strip -n "%s" .' % self.repo_name

        self.logger.info("Saving")
        # self.logger.debug('    %s' % cmd)
        self.run_command(cmd)

    def run_command(self, cmd):
        subprocess.Popen(cmd, shell=True, cwd=self.path).communicate()

    def callback(self, evt):
        # check if .bupignore was modified
        if evt.name == self.bupignore_path:
            # if .bupignore changes, could affect all paths in the repo, so re-index and save
            self.update_bupignore()
            self.index()
            self.save()
            return

        # check if file should be ignored
        if self.bupignore:
            name = os.path.relpath(evt.name, start=self.path)

            if self.ignored.match(name):
                self.logger.info('Ignoring %s\n' % evt.name)
                return
        
        # was the file deleted?
        deleted = not os.path.exists(evt.name)

        self.logger.info(('File modified: %s' if not deleted else 'File deleted: %s') % evt.name)
        
        evt_dir = os.path.dirname(evt.name)
        self.index(path=evt_dir if deleted else '.')

        # save repo
        self.save()

        print()


def main():
    description='autobup does auto bup using fsevents.'
    parser = argparse.ArgumentParser(prog='autobup', description=description)
    parser.add_argument('-c', '--config', type=str, default='~/.autobup', help='config file [default=~/.autobup]')
    # parser.add_argument('-l', '--log', type=str, default='/usr/local/var/log/autobup.log', help="log file")
    args = parser.parse_args()

    CONFIG_PATH = os.path.expanduser(args.config)
    assert os.path.isfile(CONFIG_PATH), 'could not open config file'

    logging.basicConfig(
        level  = logging.DEBUG,
        format = '%(asctime)s    %(name)s    %(message)s'
    )
    # LOG_FILENAME = args.log

    # get backup directories
    with open(CONFIG_PATH, 'r') as f:
        paths = [path.strip() for path in f]

    # Set up a specific logger with our desired output level
    # logger = logging.getLogger('autobup')
    # logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    # handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000, backupCount=1)
    # logger.addHandler(handler)

    observer = Observer()

    for path in paths:
        repo = Repo(os.path.expanduser(path))
        observer.schedule(repo.stream)

    observer.run()