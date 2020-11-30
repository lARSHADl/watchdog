from __future__ import unicode_literals

import pytest
from watchdog.utils import platform

if not platform.is_linux():  # noqa
    pytest.skip("GNU/Linux only.", allow_module_level=True)

import contextlib
import ctypes
import errno
import logging
import os
from functools import partial

from watchdog.events import DirCreatedEvent, DirDeletedEvent, DirModifiedEvent
from watchdog.observers.api import ObservedWatch
from watchdog.observers.inotify import InotifyFullEmitter, InotifyEmitter
from watchdog.observers.inotify_c import Inotify

from . import Queue
from .shell import mkdtemp, rm


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def setup_function(function):
    global p, event_queue
    tmpdir = os.path.realpath(mkdtemp())
    p = partial(os.path.join, tmpdir)
    event_queue = Queue()


@contextlib.contextmanager
def watching(path=None, use_full_emitter=False):
    path = p('') if path is None else path
    global emitter
    Emitter = InotifyFullEmitter if use_full_emitter else InotifyEmitter
    emitter = Emitter(event_queue, ObservedWatch(path, recursive=True))
    emitter.start()
    yield
    emitter.stop()
    emitter.join(5)


def teardown_function(function):
    rm(p(''), recursive=True)
    try:
        if emitter.is_alive():
            raise AssertionError
    except NameError:
        pass


def test_late_double_deletion(monkeypatch):
    inotify_fd = type(str("FD"), (object,), {})()  # Empty object
    inotify_fd.last = 0
    inotify_fd.wds = []

    # CREATE DELETE CREATE DELETE DELETE_SELF IGNORE DELETE_SELF IGNORE
    inotify_fd.buf = (
        # IN_CREATE|IS_DIR (wd = 1, path = subdir1)
        b"\x01\x00\x00\x00\x00\x01\x00\x40\x00\x00\x00\x00\x10\x00\x00\x00"
        b"\x73\x75\x62\x64\x69\x72\x31\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        # IN_DELETE|IS_DIR (wd = 1, path = subdir1)
        b"\x01\x00\x00\x00\x00\x02\x00\x40\x00\x00\x00\x00\x10\x00\x00\x00"
        b"\x73\x75\x62\x64\x69\x72\x31\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    ) * 2 + (
        # IN_DELETE_SELF (wd = 2)
        b"\x02\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        # IN_IGNORE (wd = 2)
        b"\x02\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        # IN_DELETE_SELF (wd = 3)
        b"\x03\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        # IN_IGNORE (wd = 3)
        b"\x03\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )

    os_read_bkp = os.read

    def fakeread(fd, length):
        if fd is inotify_fd:
            result, fd.buf = fd.buf[:length], fd.buf[length:]
            return result
        return os_read_bkp(fd, length)

    os_close_bkp = os.close

    def fakeclose(fd):
        if fd is not inotify_fd:
            os_close_bkp(fd)

    def inotify_init():
        return inotify_fd

    def inotify_add_watch(fd, path, mask):
        fd.last += 1
        logger.debug("New wd = %d" % fd.last)
        fd.wds.append(fd.last)
        return fd.last

    def inotify_rm_watch(fd, wd):
        logger.debug("Removing wd = %d" % wd)
        fd.wds.remove(wd)
        return 0

    # Mocks the API!
    from watchdog.observers import inotify_c
    monkeypatch.setattr(os, "read", fakeread)
    monkeypatch.setattr(os, "close", fakeclose)
    monkeypatch.setattr(inotify_c, "inotify_init", inotify_init)
    monkeypatch.setattr(inotify_c, "inotify_add_watch", inotify_add_watch)
    monkeypatch.setattr(inotify_c, "inotify_rm_watch", inotify_rm_watch)

    with watching(p('')):
        # Watchdog Events
        for evt_cls in [DirCreatedEvent, DirDeletedEvent] * 2:
            event = event_queue.get(timeout=5)[0]
            if not isinstance(event, evt_cls):
                raise AssertionError
            if event.src_path != p('subdir1'):
                raise AssertionError
            event = event_queue.get(timeout=5)[0]
            if not isinstance(event, DirModifiedEvent):
                raise AssertionError
            if event.src_path != p('').rstrip(os.path.sep):
                raise AssertionError

    if inotify_fd.last != 3:
        raise AssertionError
    if inotify_fd.buf != b"":
        raise AssertionError
    if inotify_fd.wds != [2, 3]:
        raise AssertionError


def test_raise_error(monkeypatch):
    func = Inotify._raise_error

    monkeypatch.setattr(ctypes, "get_errno", lambda: errno.ENOSPC)
    with pytest.raises(OSError) as exc:
        func()
    if exc.value.errno != errno.ENOSPC:
        raise AssertionError
    if "inotify watch limit reached" not in str(exc.value):
        raise AssertionError

    monkeypatch.setattr(ctypes, "get_errno", lambda: errno.EMFILE)
    with pytest.raises(OSError) as exc:
        func()
    if exc.value.errno != errno.EMFILE:
        raise AssertionError
    if "inotify instance limit reached" not in str(exc.value):
        raise AssertionError

    monkeypatch.setattr(ctypes, "get_errno", lambda: errno.ENOENT)
    with pytest.raises(OSError) as exc:
        func()
    if exc.value.errno != errno.ENOENT:
        raise AssertionError
    if "No such file or directory" not in str(exc.value):
        raise AssertionError

    monkeypatch.setattr(ctypes, "get_errno", lambda: -1)
    with pytest.raises(OSError) as exc:
        func()
    if exc.value.errno != -1:
        raise AssertionError
    if "Unknown error -1" not in str(exc.value):
        raise AssertionError


def test_non_ascii_path():
    """
    Inotify can construct an event for a path containing non-ASCII.
    """
    path = p(u"\N{SNOWMAN}")
    with watching(p('')):
        os.mkdir(path)
        event, _ = event_queue.get(timeout=5)
        if not isinstance(event.src_path, type(u"")):
            raise AssertionError
        if event.src_path != path:
            raise AssertionError
        # Just make sure it doesn't raise an exception.
        if not repr(event):
            raise AssertionError
