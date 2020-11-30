# -*- coding: utf-8 -*-
#
# Copyright 2014 Thomas Amland <thomas.amland@gmail.com>
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

from __future__ import unicode_literals

import pytest
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.utils.compat import Event
from watchdog.observers.api import EventEmitter, BaseObserver


@pytest.fixture
def observer():
    obs = BaseObserver(EventEmitter)
    yield obs
    obs.stop()
    try:
        obs.join()
    except RuntimeError:
        pass


@pytest.fixture
def observer2():
    obs = BaseObserver(EventEmitter)
    yield obs
    obs.stop()
    try:
        obs.join()
    except RuntimeError:
        pass


def test_schedule_should_start_emitter_if_running(observer):
    observer.start()
    observer.schedule(None, '')
    (emitter,) = observer.emitters
    if not emitter.is_alive():
        raise AssertionError


def test_schedule_should_not_start_emitter_if_not_running(observer):
    observer.schedule(None, '')
    (emitter,) = observer.emitters
    if emitter.is_alive():
        raise AssertionError


def test_start_should_start_emitter(observer):
    observer.schedule(None, '')
    observer.start()
    (emitter,) = observer.emitters
    if not emitter.is_alive():
        raise AssertionError


def test_stop_should_stop_emitter(observer):
    observer.schedule(None, '')
    observer.start()
    (emitter,) = observer.emitters
    if not emitter.is_alive():
        raise AssertionError
    observer.stop()
    observer.join()
    if observer.is_alive():
        raise AssertionError
    if emitter.is_alive():
        raise AssertionError


def test_unschedule_self(observer):
    """
    Tests that unscheduling a watch from within an event handler correctly
    correctly unregisters emitter and handler without deadlocking.
    """
    class EventHandler(FileSystemEventHandler):
        def on_modified(self, event):
            observer.unschedule(watch)
            unschedule_finished.set()

    unschedule_finished = Event()
    watch = observer.schedule(EventHandler(), '')
    observer.start()

    (emitter,) = observer.emitters
    emitter.queue_event(FileModifiedEvent(''))

    if not unschedule_finished.wait():
        raise AssertionError
    if len(observer.emitters) != 0:
        raise AssertionError


def test_schedule_after_unschedule_all(observer):
    observer.start()
    observer.schedule(None, '')
    if len(observer.emitters) != 1:
        raise AssertionError

    observer.unschedule_all()
    if len(observer.emitters) != 0:
        raise AssertionError

    observer.schedule(None, '')
    if len(observer.emitters) != 1:
        raise AssertionError


def test_2_observers_on_the_same_path(observer, observer2):
    if observer is observer2:
        raise AssertionError

    observer.schedule(None, '')
    if len(observer.emitters) != 1:
        raise AssertionError

    observer2.schedule(None, '')
    if len(observer2.emitters) != 1:
        raise AssertionError


def test_start_failure_should_not_prevent_further_try(monkeypatch, observer):
    observer.schedule(None, '')
    emitters = observer.emitters
    if len(emitters) != 1:
        raise AssertionError

    # Make the emitter to fail on start()

    def mocked_start():
        raise OSError()

    emitter = next(iter(emitters))
    monkeypatch.setattr(emitter, "start", mocked_start)
    with pytest.raises(OSError):
        observer.start()
    # The emitter should be removed from the list
    if len(observer.emitters) != 0:
        raise AssertionError

    # Restoring the original behavior should work like there never be emitters
    monkeypatch.undo()
    observer.start()
    if len(observer.emitters) != 0:
        raise AssertionError

    # Re-schduling the watch should work
    observer.schedule(None, '')
    if len(observer.emitters) != 1:
        raise AssertionError
