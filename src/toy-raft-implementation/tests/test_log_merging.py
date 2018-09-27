import unittest
from raft import *

class LogMerging(unittest.TestCase):
    def test_merge_empty_log(self):
        log = []
        new_entries = [LogEntry(term=0, index=1, command=42)]
        merged_log = merge_log(log, new_entries)
        self.assertEqual(merged_log, new_entries)

    def test_merge_non_overlapping_logs(self):
        log = [LogEntry(term=0, index=1, command=42)]
        new_entries = [LogEntry(term=0, index=2, command=42)]
        merged_log = merge_log(log, new_entries)
        self.assertEqual(merged_log, log + new_entries)

    def test_merge_log_where_some_of_the_new_entries_are_already_in_the_log(self):
        log = [LogEntry(term=0, index=1, command=42)]
        new_entry = LogEntry(term=0, index=2, command=42)
        new_entries = log + [new_entry]
        merged_log = merge_log(log, new_entries)

        self.assertEqual(log + [new_entry], merged_log)
