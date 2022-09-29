import unittest

from mock import Mock, call, ANY

from trashcli.fstab import create_fake_volume_of
from trashcli.put.trash_directories_finder import TrashDirectoriesFinder
from trashcli.put.file_trasher import FileTrasher, TrashFileIn
from trashcli.put.trash_result import TrashResult
from datetime import datetime
import os

from trashcli.put.path_maker import PathMakerType


class TestHomeFallback(unittest.TestCase):
    def setUp(self):
        self.reporter = Mock()
        mount_points = ['/', 'sandbox/other_partition']
        self.fs = Mock()
        volumes = create_fake_volume_of(mount_points)
        trash_directories_finder = TrashDirectoriesFinder(volumes)
        self.logger = Mock()
        realpath = lambda x: x
        parent_path = os.path.dirname
        self.trash_file_in = TrashFileIn(self.fs,
                                         realpath,
                                         volumes,
                                         datetime.now,
                                         parent_path,
                                         self.logger,
                                         self.reporter)
        self.file_trasher = FileTrasher(self.fs,
                                        volumes,
                                        realpath,
                                        datetime.now,
                                        trash_directories_finder,
                                        parent_path,
                                        self.logger,
                                        self.reporter,
                                        self.trash_file_in)
        self.possible_trash_directories = Mock()
        self.possible_trash_directories.trash_directories_for.return_value = \
            [('.Trash/123', '', PathMakerType.relative_paths, 'top_trash_dir_rules'),
             ('.Trash-123', '', PathMakerType.relative_paths, 'all_is_ok_rules')]
        # self.possible_trash_directories = None

    def test_use_of_top_trash_dir_when_sticky(self):
        self.fs.mock_add_spec(['isdir', 'islink', 'has_sticky_bit',
                               'move', 'atomic_write',
                               'remove_file', 'ensure_dir'])
        self.fs.isdir.return_value = True
        self.fs.islink.return_value = False
        self.fs.has_sticky_bit.return_value = True

        result = TrashResult(False)
        self.file_trasher.trash_file('sandbox/foo',
                                     None,
                                     None,
                                     result,
                                     {},
                                     123,
                                     self.possible_trash_directories,
                                     'trash-put',
                                     99)

        assert self.fs.mock_calls == [
            call.isdir('.Trash'),
            call.islink('.Trash'),
            call.has_sticky_bit('.Trash'),
            call.ensure_dir('.Trash/123', 448),
            call.ensure_dir('.Trash/123/files', 448),
            call.ensure_dir('.Trash/123/info', 448),
            call.atomic_write('.Trash/123/info/foo.trashinfo', ANY),
            call.move('sandbox/foo', '.Trash/123/files/foo')
        ]

    def test_bug_will_use_top_trashdir_even_with_not_sticky(self):
        self.fs.mock_add_spec(['isdir', 'islink', 'has_sticky_bit',
                               'move', 'atomic_write',
                               'remove_file', 'ensure_dir'])
        self.fs.isdir.return_value = True
        self.fs.islink.return_value = False
        self.fs.has_sticky_bit.return_value = False

        result = TrashResult(False)
        self.file_trasher.trash_file('sandbox/foo',
                                     None,
                                     None,
                                     result,
                                     {},
                                     123,
                                     self.possible_trash_directories,
                                     'trash-put',
                                     99)

        assert self.fs.mock_calls == [
            call.isdir('.Trash'),
            call.islink('.Trash'),
            call.has_sticky_bit('.Trash'),
            call.ensure_dir('.Trash-123', 448),
            call.ensure_dir('.Trash-123/files', 448),
            call.ensure_dir('.Trash-123/info', 448),
            call.atomic_write('.Trash-123/info/foo.trashinfo', ANY),
            call.move('sandbox/foo', '.Trash-123/files/foo')
        ]
