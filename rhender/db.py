import os
from subprocess import check_output as sh

from orator import DatabaseManager, Model

from rhender import config
from rhender.cd import cd
from rhender.shell import shell

DATABASES = {
    'sqlite': {
        'driver': 'sqlite',
        'database': 'rhender.db',
    }
}

db = DatabaseManager(DATABASES)
Model.set_connection_resolver(db)


class Project(Model):

    def head_hash(self):
        head_hash = shell('git rev-parse HEAD')
        return head_hash.strip()

    def pull(self):
        if not os.path.isdir(self.local_path):
            shell('git clone %s %s' % (self.repository_url, self.local_path))
        else:
            with cd(self.local_path):
                shell('git pull origin master')

    def commit(self):
        with cd(self.local_path):
            shell('git commit -A -m "Make change to file"')

    @property
    def local_path(self):
        return '%s/%s' % (config.DATA_DIR, self.id)

    def list_files(self):
        with cd(self.local_path):
            output = shell('git ls-tree -r --name-only master')
        paths = [
            path.strip()
            for path in str(output, 'utf-8').split('\n')
            if path.strip()
        ]
        return paths
