import unittest
from unittest.mock import Mock
from raft import *
from enum import Enum


class ExampleOperations(Enum):
    """
    Example state machine commands, where the only two possible commands are
    increment or decrement a counter.
    """
    INC = 0
    DEC = 1

class LogReplication(unittest.TestCase):
    def test_request_is_appended_to_local_log(self):
        state = RaftState()
        cmd = ExampleOperations.INC
        state.replicate(cmd)

        self.assertEqual(state.log[0].command, cmd)

    def test_entry_is_appended_with_current_term(self):
        state = RaftState()
        state.currentTerm = 10
        state.replicate(ExampleOperations.INC)
        self.assertEqual(state.log[0].term, 10)

    def test_entry_index_increments_at_every_append(self):
        state = RaftState()

        for _ in range(3):
            state.replicate(ExampleOperations.INC)

        for i in range(3):
            self.assertEqual(state.log[i].index, i + 1)

    def test_entry_is_replicated_to_all_followers(self):
        peers = [Mock(), Mock()]
        state = RaftState(peers=peers)

        state.become_leader()
        state.replicate(ExampleOperations.INC)
        state.hearbeat_timer_fired()

        request = AppendEntriesRequest(
            term=0,
            prevLogIndex=0,
            prevLogTerm=0,
            entries=state.log,
            leaderCommit=0)

        for p in state.peers:
            p.request.assert_any_call(request)


    def test_process_append_entries(self):
        state = RaftState()

        entry = LogEntry(term=1, index=1, command=ExampleOperations.DEC)

        request = AppendEntriesRequest(
            term=1,
            prevLogIndex=0,
            prevLogTerm=0,
            entries=[entry],
            leaderCommit=0)

        reply = state.process(request)

        # The entry is valid, so nothing weird should happen
        self.assertTrue(reply.success)

        # The last index in the replicated log should be the most recent one
        self.assertEqual(reply.lastIndex, state.log[-1].index)

        # The log must now contain the entry
        self.assertEqual(state.log, [entry])


    def test_append_entries_is_rejected_if_more_recent_term_than_leader(self):
        """
        AppendEntries must be rejected if the leader's term is older than ours.
        See section 5.1 in the raft paper.
        """
        state = RaftState()
        state.currentTerm = 10

        entry = LogEntry(term=1, index=1, command=ExampleOperations.DEC)
        request = AppendEntriesRequest(
            term=1,
            prevLogIndex=0,
            prevLogTerm=0,
            entries=[entry],
            leaderCommit=0)

        reply = state.process(request)

        self.assertFalse(reply.success)
        self.assertEqual(state.id, reply.fromId)
        self.assertEqual(state.log, [])

    def test_entry_is_committed_if_leader_says_so(self):
        state = RaftState()
        state.log = [LogEntry(term=1, index=1, command=None)]
        state.term = 1
        request = AppendEntriesRequest(term=1, prevLogIndex=1, prevLogTerm=1, entries=[], leaderCommit=1)
        state.process(request)
        self.assertEqual(state.commitIndex, 1)

    def test_do_not_commit_entries_not_in_the_local_log(self):
        state = RaftState()
        state.log = [LogEntry(term=1, index=1, command=None)]
        state.term = 1
        request = AppendEntriesRequest(term=1, prevLogIndex=1, prevLogTerm=1, entries=[], leaderCommit=2)
        state.process(request)
        self.assertEqual(state.commitIndex, 1)

    def test_do_not_uncommit_entries(self):
        state = RaftState()
        state.log = [LogEntry(term=1, index=1, command=None)]
        state.term = 1
        state.commitIndex = 1
        request = AppendEntriesRequest(term=1, prevLogIndex=1, prevLogTerm=1, entries=[], leaderCommit=0)
        state.process(request)
        self.assertEqual(state.commitIndex, 1)

    def test_append_entries_is_rejected_if_previous_log_entry_does_not_exist(
            self):
        """
        AppendEntries request will be rejected if the previous entry indicated
        in the message cannot be found in the log.

        See section 5.3 of the raft paper
        """
        state = RaftState()
        state.log = [LogEntry(term=1, index=1, command=ExampleOperations.DEC)]
        old_log = state.log

        new_entry = LogEntry(term=1, index=3, command=ExampleOperations.INC)

        request = AppendEntriesRequest(
            term=1,
            prevLogIndex=2,
            prevLogTerm=1,
            entries=[new_entry],
            leaderCommit=0)

        reply = state.process(request)

        self.assertFalse(reply.success)
        self.assertEqual(state.id, reply.fromId)
        self.assertEqual(state.log, old_log)

    def test_entries_are_appended_to_the_log_if_previous_log_entry_exists(
            self):
        state = RaftState()
        old_entry = LogEntry(term=1, index=1, command=ExampleOperations.DEC)
        new_entry = LogEntry(term=1, index=2, command=ExampleOperations.INC)
        state.log = [old_entry]

        request = AppendEntriesRequest(
            term=1,
            prevLogIndex=1,
            prevLogTerm=1,
            entries=[new_entry],
            leaderCommit=0)

        reply = state.process(request)
        self.assertTrue(reply.success)

        expected_log = [old_entry, new_entry]
        self.assertEqual(state.log, expected_log)
        self.assertEqual(state.id, reply.fromId)

    def test_more_recent_term_wins_log_inconsistency(self):
        """
        Checks that if two entries conflict (have the same index), then the one
        with the most recent term wins.

        See section 5.3
        """
        state = RaftState()
        old_entry1 = LogEntry(term=1, index=1, command=ExampleOperations.DEC)
        old_entry2 = LogEntry(term=1, index=2, command=ExampleOperations.DEC)
        new_entry = LogEntry(term=2, index=2, command=ExampleOperations.INC)
        state.log = [old_entry1, old_entry2]

        request = AppendEntriesRequest(
            term=2,
            prevLogIndex=0,
            prevLogTerm=0,
            entries=[new_entry],
            leaderCommit=0)

        reply = state.process(request)
        self.assertTrue(reply.success)

        expected_log = [old_entry1, new_entry]
        self.assertEqual(expected_log, state.log)

    def test_duplicate_log_entries_are_ignored(self):
        state = RaftState()
        entry1 = LogEntry(term=1, index=1, command=ExampleOperations.DEC)
        entry2 = LogEntry(term=1, index=2, command=ExampleOperations.INC)

        request1 = AppendEntriesRequest(
            term=1,
            prevLogIndex=0,
            prevLogTerm=0,
            entries=[entry1],
            leaderCommit=0)

        request2 = AppendEntriesRequest(
            term=2,
            prevLogIndex=0,
            prevLogTerm=0,
            entries=[entry1, entry2],
            leaderCommit=0)

        state.process(request1)
        state.process(request2)

        self.assertEqual(state.log, [entry1, entry2])

    def test_that_the_match_index_is_initialized_correctly(self):
        """
        Checks that the match index is initialized correctly for every peer.
        """
        # TODO: There will be a need for a peer <-> ID translation somehow
        state = RaftState(peers=[Mock(), Mock(), Mock()])
        state.log = [LogEntry(term=1, index=10, command=ExampleOperations.DEC)]
        state.become_leader()

        for p in state.peers:
            self.assertEqual(state.match_index[p], 0)
            self.assertEqual(state.next_index[p], 10)

    def test_set_match_and_next_index_on_succesful_appendentry(self):
        state = RaftState(peers=[Mock(), Mock(), Mock()])
        for i in range(len(state.peers)):
            state.peers[i].id = i
        state.become_leader()

        for _ in range(3):
            state.replicate(ExampleOperations.INC)

        reply = AppendEntriesReply(success=True, fromId=0, lastIndex=2)

        state.process(reply)
        self.assertEqual(state.match_index[state.peers[0]], 2)
        self.assertEqual(state.next_index[state.peers[0]], 3)

    def test_decrement_next_index_on_failed_appendentry(self):
        state = RaftState(peers=[Mock(), Mock(), Mock()])
        for i in range(len(state.peers)):
            state.peers[i].id = i

        state.become_leader()

        for _ in range(3):
            state.replicate(ExampleOperations.INC)

        reply1 = AppendEntriesReply(success=True, fromId=0, lastIndex=1)
        reply2 = AppendEntriesReply(success=False, fromId=0, lastIndex=None)

        state.process(reply1)
        self.assertEqual(state.next_index[state.peers[0]], 2)
        state.process(reply2)
        self.assertEqual(state.next_index[state.peers[0]], 1)

    def test_non_replicated_entries_are_sent_again_on_heartbeat(self):
        state = RaftState(peers=[Mock(), Mock(), Mock()])
        for i in range(len(state.peers)):
            state.peers[i].id = i
        state.become_leader()
        state.replicate(ExampleOperations.INC)
        state.replicate(ExampleOperations.DEC)

        reply1 = AppendEntriesReply(success=True, fromId=0, lastIndex=1)
        state.process(reply1)

        state.hearbeat_timer_fired()

        msg = AppendEntriesRequest(term=0, prevLogTerm=0, prevLogIndex=1, entries=state.log[1:], leaderCommit=0)

        state.peers[0].request.assert_any_call(msg)

    def test_commit_index_is_sent(self):
        state = RaftState(peers=[Mock(), Mock(), Mock()])
        state.become_leader()
        state.commitIndex = 12
        state.replicate(None)
        state.hearbeat_timer_fired()
        msg = AppendEntriesRequest(term=0, prevLogTerm=0, prevLogIndex=0, entries=state.log, leaderCommit=12)
        state.peers[0].request.assert_any_call(msg)

    def test_update_commit_index_when_majority_answered(self):
        state = RaftState(peers=[Mock(), Mock()])
        for i in range(len(state.peers)):
            state.peers[i].id = i
        state.become_leader()
        state.replicate(ExampleOperations.INC)
        state.replicate(ExampleOperations.DEC)

        # the first message was replicated on a majority of the cluster, we can
        # now assume that it was commited
        state.process(AppendEntriesReply(success=True, fromId=0, lastIndex=1))
        state.process(AppendEntriesReply(success=True, fromId=1, lastIndex=1))

        self.assertEqual(state.commitIndex, 1)

        # Even one node is enough, as the commit is present on both the leader
        # and this replicated commit.
        state.process(AppendEntriesReply(success=True, fromId=0, lastIndex=2))
        self.assertEqual(state.commitIndex, 2)

    def test_entries_from_previous_terms_are_not_commited_by_counting_replicas(self):
        state = RaftState(peers=[Mock(), Mock()])
        for i in range(len(state.peers)):
            state.peers[i].id = i
        state.become_leader()
        state.replicate(ExampleOperations.INC)
        state.replicate(ExampleOperations.DEC)

        state.currentTerm = 10

        # The messages were replicated on all clusters. However as they are not
        # a part of the current term, they should not be committed by this
        # leader.
        state.process(AppendEntriesReply(success=True, fromId=0, lastIndex=1))
        state.process(AppendEntriesReply(success=True, fromId=1, lastIndex=1))
        self.assertEqual(state.commitIndex, 0)
        state = RaftState()
