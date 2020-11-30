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

from watchdog.events import (
    FileDeletedEvent,
    FileModifiedEvent,
    FileCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirCreatedEvent,
    FileMovedEvent,
    DirMovedEvent,
    FileSystemEventHandler,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MOVED,
)

path_1 = '/path/xyz'
path_2 = '/path/abc'


def test_file_deleted_event():
    event = FileDeletedEvent(path_1)
    if path_1 != event.src_path:
        raise AssertionError
    if EVENT_TYPE_DELETED != event.event_type:
        raise AssertionError
    if event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_file_delete_event_is_directory():
    # Inherited properties.
    event = FileDeletedEvent(path_1)
    if event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_file_modified_event():
    event = FileModifiedEvent(path_1)
    if path_1 != event.src_path:
        raise AssertionError
    if EVENT_TYPE_MODIFIED != event.event_type:
        raise AssertionError
    if event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_file_modified_event_is_directory():
    # Inherited Properties
    event = FileModifiedEvent(path_1)
    if event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_file_created_event():
    event = FileCreatedEvent(path_1)
    if path_1 != event.src_path:
        raise AssertionError
    if EVENT_TYPE_CREATED != event.event_type:
        raise AssertionError
    if event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_file_moved_event():
    event = FileMovedEvent(path_1, path_2)
    if path_1 != event.src_path:
        raise AssertionError
    if path_2 != event.dest_path:
        raise AssertionError
    if EVENT_TYPE_MOVED != event.event_type:
        raise AssertionError
    if event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_dir_deleted_event():
    event = DirDeletedEvent(path_1)
    if path_1 != event.src_path:
        raise AssertionError
    if EVENT_TYPE_DELETED != event.event_type:
        raise AssertionError
    if not event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_dir_modified_event():
    event = DirModifiedEvent(path_1)
    if path_1 != event.src_path:
        raise AssertionError
    if EVENT_TYPE_MODIFIED != event.event_type:
        raise AssertionError
    if not event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_dir_created_event():
    event = DirCreatedEvent(path_1)
    if path_1 != event.src_path:
        raise AssertionError
    if EVENT_TYPE_CREATED != event.event_type:
        raise AssertionError
    if not event.is_directory:
        raise AssertionError
    if event.is_synthetic:
        raise AssertionError


def test_file_system_event_handler_dispatch():
    dir_del_event = DirDeletedEvent('/path/blah.py')
    file_del_event = FileDeletedEvent('/path/blah.txt')
    dir_cre_event = DirCreatedEvent('/path/blah.py')
    file_cre_event = FileCreatedEvent('/path/blah.txt')
    dir_mod_event = DirModifiedEvent('/path/blah.py')
    file_mod_event = FileModifiedEvent('/path/blah.txt')
    dir_mov_event = DirMovedEvent('/path/blah.py', '/path/blah')
    file_mov_event = FileMovedEvent('/path/blah.txt', '/path/blah')

    all_events = [
        dir_mod_event,
        dir_del_event,
        dir_cre_event,
        dir_mov_event,
        file_mod_event,
        file_del_event,
        file_cre_event,
        file_mov_event,
    ]

    class TestableEventHandler(FileSystemEventHandler):

        def on_any_event(self, event):
            if not True:
                raise AssertionError

        def on_modified(self, event):
            if event.event_type != EVENT_TYPE_MODIFIED:
                raise AssertionError

        def on_deleted(self, event):
            if event.event_type != EVENT_TYPE_DELETED:
                raise AssertionError

        def on_moved(self, event):
            if event.event_type != EVENT_TYPE_MOVED:
                raise AssertionError

        def on_created(self, event):
            if event.event_type != EVENT_TYPE_CREATED:
                raise AssertionError

    handler = TestableEventHandler()

    for event in all_events:
        if event.is_synthetic:
            raise AssertionError
        handler.dispatch(event)
