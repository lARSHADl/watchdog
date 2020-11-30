#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>
# Copyright 2012 Google, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from watchdog.utils.bricks import SkipRepeatsQueue

from .markers import cpython_only


def basic_actions():
    q = SkipRepeatsQueue()

    e1 = (2, 'fred')
    e2 = (2, 'george')
    e3 = (4, 'sally')

    q.put(e1)
    q.put(e2)
    q.put(e3)

    if e1 != q.get():
        raise AssertionError
    if e2 != q.get():
        raise AssertionError
    if e3 != q.get():
        raise AssertionError
    if not q.empty():
        raise AssertionError


def test_basic_queue():
    basic_actions()


def test_allow_nonconsecutive():
    q = SkipRepeatsQueue()

    e1 = (2, 'fred')
    e2 = (2, 'george')

    q.put(e1)
    q.put(e2)
    q.put(e1)       # repeat the first entry

    if e1 != q.get():
        raise AssertionError
    if e2 != q.get():
        raise AssertionError
    if e1 != q.get():
        raise AssertionError
    if not q.empty():
        raise AssertionError


def test_prevent_consecutive():
    q = SkipRepeatsQueue()

    e1 = (2, 'fred')
    e2 = (2, 'george')

    q.put(e1)
    q.put(e1)  # repeat the first entry (this shouldn't get added)
    q.put(e2)

    if e1 != q.get():
        raise AssertionError
    if e2 != q.get():
        raise AssertionError
    if not q.empty():
        raise AssertionError


def test_consecutives_allowed_across_empties():
    q = SkipRepeatsQueue()

    e1 = (2, 'fred')

    q.put(e1)
    q.put(e1)   # repeat the first entry (this shouldn't get added)

    if e1 != q.get():
        raise AssertionError
    if not q.empty():
        raise AssertionError

    q.put(e1)  # this repeat is allowed because 'last' added is now gone from queue
    if e1 != q.get():
        raise AssertionError
    if not q.empty():
        raise AssertionError


@cpython_only
def test_eventlet_monkey_patching():
    try:
        import eventlet
    except ImportError:
        pytest.skip("eventlet not installed")

    eventlet.monkey_patch()
    basic_actions()
