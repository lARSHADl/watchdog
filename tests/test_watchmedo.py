# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

# Skip if import PyYAML failed. PyYAML missing possible because
# watchdog installed without watchmedo. See Installation section
# in README.rst
yaml = pytest.importorskip('yaml')  # noqa

import os

from watchdog import watchmedo
from yaml.constructor import ConstructorError
from yaml.scanner import ScannerError


def test_load_config_valid(tmpdir):
    """Verifies the load of a valid yaml file"""

    yaml_file = os.path.join(tmpdir, 'config_file.yaml')
    with open(yaml_file, 'w') as f:
        f.write('one: value\ntwo:\n- value1\n- value2\n')

    config = watchmedo.load_config(yaml_file)
    if not isinstance(config, dict):
        raise AssertionError
    if 'one' not in config:
        raise AssertionError
    if 'two' not in config:
        raise AssertionError
    if not isinstance(config['two'], list):
        raise AssertionError
    if config['one'] != 'value':
        raise AssertionError
    if config['two'] != ['value1', 'value2']:
        raise AssertionError


def test_load_config_invalid(tmpdir):
    """Verifies if safe load avoid the execution
    of untrusted code inside yaml files"""

    critical_dir = os.path.join(tmpdir, 'critical')
    yaml_file = os.path.join(tmpdir, 'tricks_file.yaml')
    with open(yaml_file, 'w') as f:
        content = (
            'one: value\n'
            'run: !!python/object/apply:os.system ["mkdir {}"]\n'
        ).format(critical_dir)
        f.write(content)

    # PyYAML get_single_data() raises different exceptions for Linux and Windows
    with pytest.raises((ConstructorError, ScannerError)):
        watchmedo.load_config(yaml_file)

    if os.path.exists(critical_dir):
        raise AssertionError
