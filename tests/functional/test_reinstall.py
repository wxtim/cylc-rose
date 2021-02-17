# THIS FILE IS PART OF THE ROSE-CYLC PLUGIN FOR THE CYLC SUITE ENGINE.
# Copyright (C) NIWA & British Crown (Met Office) & Contributors.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Functional tests for top-level function record_cylc_install_options.

n.b. The tests in this module _must_ be run in order.
"""

from pathlib import Path
import subprocess
import pytest
import os
import shutil

from uuid import uuid4


from cylc.flow.platforms import get_platform


@pytest.fixture(scope='module')
def monkeymodule():
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope='module')
def workflow_src(tmp_path_factory):
    orig_srcdir = Path(__file__).parent / '10_reinstall_basic'
    srcdir = (tmp_path_factory.getbasetemp() / 'srcdir')
    shutil.copytree(orig_srcdir, srcdir)
    yield srcdir
    shutil.rmtree(srcdir)


@pytest.fixture(scope='module')
def workflow_install_dir():
    install_dirname = f'cylc-rose-test.{str(uuid4())[:10]}'
    install_dirpath = Path(
        os.path.expandvars(get_platform()['run directory'])
    ) / install_dirname
    yield install_dirpath
    shutil.rmtree(install_dirpath)


@pytest.fixture(scope='module')
def cylc_install(monkeymodule, workflow_install_dir, workflow_src):
    srcdir = workflow_src
    monkeymodule.setenv('ROSE_SUITE_OPT_CONF_KEYS', 'b')
    result = subprocess.run(
        [
            'cylc', 'install', '--directory',
            str(srcdir), '--flow-name', str(workflow_install_dir.name),
            '-O', 'c', '--no-run-name'
        ],
        capture_output=True,
        env=os.environ
    )
    yield {'result': result, 'install_dir': workflow_install_dir}
    os.environ.pop('ROSE_SUITE_OPT_CONF_KEYS')


@pytest.fixture(scope='module')
def cylc_reinstall(workflow_install_dir, workflow_src):
    result = subprocess.run(
        [
            'cylc', 'reinstall', str(workflow_install_dir.name),
            '-O', 'd'
        ],
        capture_output=True,
        env=os.environ
    )
    return {'result': result, 'install_dir': workflow_install_dir}


@pytest.fixture(scope='module')
def cylc_reinstall_with_modified_src(workflow_install_dir, workflow_src):
    (workflow_src / 'rose-suite.conf').write_text("opts=z\n")
    result = subprocess.run(
        [
            'cylc', 'reinstall', str(workflow_install_dir.name),
            '-O', 'd'
        ],
        capture_output=True,
        env=os.environ
    )
    return {'result': result, 'install_dir': workflow_install_dir}


def test_install_ok(cylc_install):
    assert cylc_install['result'].returncode == 0


@pytest.mark.parametrize(
    'file_, content',
    [
        ('rose-suite.conf', (
            '# Config Options \'b c (cylc-install)\' from CLI appended to '
            'options already in `rose-suite.conf`.\n'
            'opts=a b c (cylc-install)\n'
        )),
        ('opt/rose-suite-cylc-install.conf',(
            '# This file records CLI Options.\n\n'
            '!opts=b c\n'
        ))
    ]
)
def test_installed_file_content(cylc_install, file_, content):
    assert (cylc_install['install_dir'] / file_).read_text() == content


def test_reinstall_ok(cylc_reinstall):
    assert cylc_reinstall['result'].returncode == 0


@pytest.mark.parametrize(
    'file_, content',
    [
        ('rose-suite.conf', (
            '# Config Options \'b c (cylc-install)\' from CLI appended to '
            'options already in `rose-suite.conf`.\n'
            'opts=a b c d (cylc-install)\n'
        )),
        ('opt/rose-suite-cylc-install.conf',(
            '# This file records CLI Options.\n\n'
            '!opts=b c d\n'
        ))
    ]
)
def test_reinstalled_file_content(cylc_reinstall, file_, content):
    assert (cylc_reinstall['install_dir'] / file_).read_text() == content


def test_reinstalled_from_changed_source_ok(cylc_reinstall_with_modified_src):
    assert cylc_reinstall_with_modified_src['result'].returncode == 0


@pytest.mark.parametrize(
    'file_, content',
    [
        ('rose-suite.conf', (
            '# Config Options \'b c (cylc-install)\' from CLI appended to '
            'options already in `rose-suite.conf`.\n'
            'NOTE: opt a has been removed.\n'
            'NOTE: opts b c d have been remembered.\n'
            'opts=a b c d (cylc-install)\n'
        )),
    ]
)
def test_reinstalled_from_changed_source_file_content(
    cylc_reinstall_with_modified_src, file_, content
):
    assert (
        cylc_reinstall_with_modified_src['install_dir'] / file_
    ).read_text() == content
