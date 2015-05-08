from setuptools import setup
from git_version import get_git_version
from distutils.command.sdist import sdist
import os
from distutils import dir_util

class my_build_py(sdist):


    #had to overwrite the distribution creation as splunk depends on the folder name of the application
    #therefore the archive contains a folder only named after the application name, omitting the version string
    #e.g. elasticsearchapp instead of elasticsearchapp-1.1.1
    #THIS WILL BREAK STANDARD PYTHON BEHAVIOUR
    #DO NOT INSTALL THESE SOURCE DISTS ON ANYTHING BUT SPLUNK!
    def make_distribution(self):
        """Create the source distribution(s).  First, we create the release
        tree with 'make_release_tree()'; then, we create all required
        archive files (according to 'self.formats') from the release tree.
        Finally, we clean up by blowing away the release tree (unless
        'self.keep_temp' is true).  The list of archive files created is
        stored so it can be retrieved later by 'get_archive_files()'.
        """
        # Don't warn about missing meta-data here -- should be (and is!)
        # done elsewhere.

        #CHANGE
        base_dir = self.distribution.get_name()
        full_name = self.distribution.get_fullname()
        #CHANGEEND

        base_name = os.path.join(self.dist_dir, full_name)

        self.make_release_tree(base_dir, self.filelist.files)
        archive_files = []              # remember names of files we create
        # tar archive must be created last to avoid overwrite and remove
        if 'tar' in self.formats:
            self.formats.append(self.formats.pop(self.formats.index('tar')))

        for fmt in self.formats:
            file = self.make_archive(base_name, fmt, base_dir=base_dir,
                                     owner=self.owner, group=self.group)
            archive_files.append(file)
            self.distribution.dist_files.append(('sdist', '', file))

        self.archive_files = archive_files

        if not self.keep_temp:
            dir_util.remove_tree(base_dir, dry_run=self.dry_run)

    def run(self):
        # honor the --dry-run flag
        if not self.dry_run:
            curpath = os.path.dirname(os.path.realpath(__file__))
            for root, dirs, files in os.walk(os.path.join(curpath,'default')):
                for file in files:
                    if file.endswith(".conftemplate"):
                        fpath = os.path.join(root, file)
                        fileName, fileExtension = os.path.splitext(fpath)
                        with open(fpath, 'r') as template:
                            with open(fileName + '.conf', 'w') as conffile:
                                conffile.write(template.read().replace('$version$', get_git_version()))
        # distutils uses old-style classes, so no super()
        sdist.run(self)

setup(  cmdclass={'sdist': my_build_py},
        name="alert_manager",
        version = get_git_version(),
        description='Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify owner, status, severity) and auto-resolve features',
        url='https://github.com/simcen/alert_manager',
        author='Simon Balz, Mika Borner',
        author_email='simon@balz.me, mika.borner@gmail.com',
        packages=['bin'],
        setup_requires=['nose', 'nose-exclude', 'coverage', 'unittest2'],
        include_package_data=True
      )