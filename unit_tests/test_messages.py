# -*- coding: utf-8 -*-
"""
test_messages.py

test AMQP Messages
"""
from hashlib import md5
import logging
import time
import unittest
import uuid
from zlib import adler32

from unit_tests.util import generate_database_content

from diyapi_database_server import database_content
from messages.database_key_insert import DatabaseKeyInsert
from messages.database_key_insert_reply import DatabaseKeyInsertReply
from messages.database_key_lookup import DatabaseKeyLookup
from messages.database_key_lookup_reply import DatabaseKeyLookupReply
from messages.database_key_destroy import DatabaseKeyDestroy
from messages.database_key_destroy_reply import DatabaseKeyDestroyReply
from messages.database_listmatch import DatabaseListMatch
from messages.database_listmatch_reply import DatabaseListMatchReply
from messages.archive_key_entire import ArchiveKeyEntire
from messages.archive_key_start import ArchiveKeyStart
from messages.archive_key_start_reply import ArchiveKeyStartReply
from messages.archive_key_next import ArchiveKeyNext
from messages.archive_key_next_reply import ArchiveKeyNextReply
from messages.archive_key_final import ArchiveKeyFinal
from messages.archive_key_final_reply import ArchiveKeyFinalReply
from messages.retrieve_key_start import RetrieveKeyStart
from messages.retrieve_key_start_reply import RetrieveKeyStartReply
from messages.retrieve_key_next import RetrieveKeyNext
from messages.retrieve_key_next_reply import RetrieveKeyNextReply
from messages.retrieve_key_final import RetrieveKeyFinal
from messages.retrieve_key_final_reply import RetrieveKeyFinalReply
from messages.destroy_key import DestroyKey
from messages.destroy_key_reply import DestroyKeyReply

from unit_tests.util import random_string

class TestMessages(unittest.TestCase):
    """test AMQP Messages"""

    def test_database_key_insert(self):
        """test DatabaseKeyInsert"""
        original_content = generate_database_content()
        original_request_id = uuid.uuid1().hex
        original_avatar_id = 1001
        original_reply_exchange = "reply-exchange"
        original_reply_routing_header = "reply-header"
        original_key  = "abcdefghijk"
        message = DatabaseKeyInsert(
            original_request_id,
            original_avatar_id,
            original_reply_exchange,
            original_reply_routing_header,
            original_key, 
            original_content
        )
        marshalled_message = message.marshall()
        unmarshalled_message = DatabaseKeyInsert.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.avatar_id, original_avatar_id)
        self.assertEqual(
            unmarshalled_message.reply_routing_header, 
            original_reply_routing_header
        )
        self.assertEqual(
            unmarshalled_message.reply_exchange, original_reply_exchange
        )
        self.assertEqual(unmarshalled_message.key, original_key)
        self.assertEqual(
            unmarshalled_message.database_content, original_content
        )

    def test_database_key_insert_reply_ok(self):
        """test DatabaseKeyInsertReply"""
        original_request_id = uuid.uuid1().hex
        original_result = 0
        original_previous_size = 42
        message = DatabaseKeyInsertReply(
            original_request_id,
            original_result,
            original_previous_size
        )
        marshaled_message = message.marshall()
        unmarshalled_message = DatabaseKeyInsertReply.unmarshall(
            marshaled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)
        self.assertEqual(
            unmarshalled_message.previous_size, original_previous_size
        )

    def test_database_key_lookup(self):
        """test DatabaseKeyLookup"""
        original_request_id = uuid.uuid1().hex
        original_avatar_id = 1001
        original_reply_exchange = "reply-exchange"
        original_reply_routing_header = "reply-header"
        original_key  = "abcdefghijk"
        message = DatabaseKeyLookup(
            original_request_id,
            original_avatar_id,
            original_reply_exchange,
            original_reply_routing_header,
            original_key, 
        )
        marshalled_message = message.marshall()
        unmarshalled_message = DatabaseKeyLookup.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.avatar_id, original_avatar_id)
        self.assertEqual(
            unmarshalled_message.reply_routing_header, 
            original_reply_routing_header
        )
        self.assertEqual(
            unmarshalled_message.reply_exchange, original_reply_exchange
        )
        self.assertEqual(unmarshalled_message.key, original_key)

    def test_database_key_lookup_reply_ok(self):
        """test DatabaseKeyLookupReply"""
        original_content = generate_database_content()
        original_request_id = uuid.uuid1().hex
        original_avatar_id = 1001
        message = DatabaseKeyLookupReply(
            original_request_id,
            0,
            original_content
        )
        marshalled_message = message.marshall()
        unmarshalled_message = DatabaseKeyLookupReply.unmarshall(
            marshalled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertTrue(unmarshalled_message.key_found)
        self.assertEqual(
            unmarshalled_message.database_content, original_content
        )

    def test_database_key_destroy(self):
        """test DatabaseKeyDestroy"""
        original_request_id = uuid.uuid1().hex
        original_avatar_id = 1001
        original_reply_exchange = "reply-exchange"
        original_reply_routing_header = "reply-header"
        original_key  = "abcdefghijk"
        original_timestamp = time.time()
        message = DatabaseKeyDestroy(
            original_request_id,
            original_avatar_id,
            original_reply_exchange,
            original_reply_routing_header,
            original_key,
            original_timestamp
        )
        marshalled_message = message.marshall()
        unmarshalled_message = DatabaseKeyDestroy.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.avatar_id, original_avatar_id)
        self.assertEqual(
            unmarshalled_message.reply_routing_header, 
            original_reply_routing_header
        )
        self.assertEqual(
            unmarshalled_message.reply_exchange, original_reply_exchange
        )
        self.assertEqual(unmarshalled_message.key, original_key)
        self.assertEqual(
            unmarshalled_message.timestamp, original_timestamp
        )

    def test_database_key_destroy_reply_ok(self):
        """test DatabaseKeyDestroyReply"""
        original_request_id = uuid.uuid1().hex
        original_result = 0
        original_total_size = 42
        message = DatabaseKeyDestroyReply(
            original_request_id,
            original_result,
            original_total_size
        )
        marshaled_message = message.marshall()
        unmarshalled_message = DatabaseKeyDestroyReply.unmarshall(
            marshaled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)
        self.assertEqual(
            unmarshalled_message.total_size, original_total_size
        )

    def test_database_listmatch(self):
        """test DatabaseListMatch"""
        original_request_id = uuid.uuid1().hex
        original_avatar_id = 1001
        original_reply_exchange = "reply-exchange"
        original_reply_routing_header = "reply-header"
        original_prefix  = "abcdefghijk"
        message = DatabaseListMatch(
            original_request_id,
            original_avatar_id,
            original_reply_exchange,
            original_reply_routing_header,
            original_prefix 
        )
        marshalled_message = message.marshall()
        unmarshalled_message = DatabaseListMatch.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.avatar_id, original_avatar_id)
        self.assertEqual(
            unmarshalled_message.reply_routing_header, 
            original_reply_routing_header
        )
        self.assertEqual(
            unmarshalled_message.reply_exchange, original_reply_exchange
        )
        self.assertEqual(unmarshalled_message.prefix, original_prefix)

    def test_database_listmatch_reply_ok(self):
        """test DatabaseListMatchReply"""
        original_request_id = uuid.uuid1().hex
        original_result = 0
        original_is_complete = True
        original_key_list = [str(x) for x in range(1000)]
        message = DatabaseListMatchReply(
            original_request_id,
            original_result,
            original_is_complete,
            original_key_list
        )
        marshalled_message = message.marshall()
        unmarshalled_message = DatabaseListMatchReply.unmarshall(
            marshalled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)
        self.assertEqual(unmarshalled_message.is_complete, original_is_complete)
        self.assertEqual(unmarshalled_message.key_list, original_key_list)

    def test_archive_key_entire(self):
        """test ArchiveKeyEntire"""
        original_content = random_string(64 * 1024) 
        original_request_id = uuid.uuid1().hex
        original_avatar_id = 1001
        original_reply_exchange = "reply-exchange"
        original_reply_routing_header = "reply-header"
        original_key  = "abcdefghijk"
        original_timestamp = time.time()
        original_segment_number = 3
        original_adler32 = adler32(original_content)
        original_md5 = md5(original_content).digest()
        message = ArchiveKeyEntire(
            original_request_id,
            original_avatar_id,
            original_reply_exchange,
            original_reply_routing_header,
            original_key, 
            original_timestamp,
            original_segment_number,
            original_adler32,
            original_md5,
            original_content
        )
        marshalled_message = message.marshall()
        unmarshalled_message = ArchiveKeyEntire.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.avatar_id, original_avatar_id)
        self.assertEqual(
            unmarshalled_message.reply_exchange, original_reply_exchange
        )
        self.assertEqual(
            unmarshalled_message.reply_routing_header, original_reply_routing_header
        )
        self.assertEqual(unmarshalled_message.key, original_key)
        self.assertEqual(unmarshalled_message.timestamp, original_timestamp)
        self.assertEqual(
            unmarshalled_message.segment_number, original_segment_number
        )
        self.assertEqual(unmarshalled_message.adler32, original_adler32)
        self.assertEqual(unmarshalled_message.md5, original_md5)
        self.assertEqual(unmarshalled_message.content, original_content)

    def test_archive_key_start(self):
        """test ArchiveKeyStart"""
        original_segment_size = 64 * 1024
        original_content = random_string(original_segment_size) 
        original_request_id = uuid.uuid1().hex
        original_avatar_id = 1001
        original_reply_exchange = "reply-exchange"
        original_reply_routing_header = "reply-header"
        original_key  = "abcdefghijk"
        original_timestamp = time.time()
        original_sequence = 0
        original_segment_number = 3

        message = ArchiveKeyStart(
            original_request_id,
            original_avatar_id,
            original_reply_exchange,
            original_reply_routing_header,
            original_key, 
            original_timestamp,
            original_sequence,
            original_segment_number,
            original_segment_size,
            original_content
        )
        marshalled_message = message.marshall()
        unmarshalled_message = ArchiveKeyStart.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.avatar_id, original_avatar_id)
        self.assertEqual(
            unmarshalled_message.reply_exchange, original_reply_exchange
        )
        self.assertEqual(
            unmarshalled_message.reply_routing_header, original_reply_routing_header
        )
        self.assertEqual(unmarshalled_message.key, original_key)
        self.assertEqual(unmarshalled_message.timestamp, original_timestamp)
        self.assertEqual(unmarshalled_message.sequence, original_sequence)
        self.assertEqual(
            unmarshalled_message.segment_number, original_segment_number
        )
        self.assertEqual(
            unmarshalled_message.segment_size, original_segment_size
        )
        self.assertEqual(unmarshalled_message.data_content, original_content)

    def test_archive_key_start_reply_ok(self):
        """test ArchiveKeyStartReply"""
        original_request_id = uuid.uuid1().hex
        original_result = 0
        message = ArchiveKeyStartReply(
            original_request_id,
            original_result
        )
        marshaled_message = message.marshall()
        unmarshalled_message = ArchiveKeyStartReply.unmarshall(
            marshaled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)

    def test_archive_key_next(self):
        """test ArchiveKeyNext"""
        original_segment_size = 64 * 1024
        original_content = random_string(original_segment_size) 
        original_request_id = uuid.uuid1().hex
        original_sequence = 01

        message = ArchiveKeyNext(
            original_request_id,
            original_sequence,
            original_content
        )
        marshalled_message = message.marshall()
        unmarshalled_message = ArchiveKeyNext.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.sequence, original_sequence)
        self.assertEqual(unmarshalled_message.data_content, original_content)

    def test_archive_key_next_reply_ok(self):
        """test ArchiveKeyNextReply"""
        original_request_id = uuid.uuid1().hex
        original_result = 0
        message = ArchiveKeyNextReply(
            original_request_id,
            original_result
        )
        marshaled_message = message.marshall()
        unmarshalled_message = ArchiveKeyNextReply.unmarshall(
            marshaled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)

    def test_archive_key_final(self):
        """test ArchiveKeyFinal"""
        original_content = random_string(64 * 1024) 
        original_request_id = uuid.uuid1().hex
        original_sequence = 3
        original_total_size = 42L
        original_adler32 = -10
        original_md5 = "ffffffffffffffff"
        message = ArchiveKeyFinal(
            original_request_id,
            original_sequence,
            original_total_size,
            original_adler32,
            original_md5,
            original_content
        )
        marshalled_message = message.marshall()
        unmarshalled_message = ArchiveKeyFinal.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.sequence, original_sequence)
        self.assertEqual(unmarshalled_message.total_size, original_total_size)
        self.assertEqual(unmarshalled_message.adler32, original_adler32)
        self.assertEqual(unmarshalled_message.md5, original_md5)
        self.assertEqual(unmarshalled_message.data_content, original_content)

    def test_archive_key_final_reply_ok(self):
        """test ArchiveKeyFinalReply"""
        original_request_id = uuid.uuid1().hex
        original_result = 0
        original_previous_size = 42
        message = ArchiveKeyFinalReply(
            original_request_id,
            original_result,
            original_previous_size
        )
        marshaled_message = message.marshall()
        unmarshalled_message = ArchiveKeyFinalReply.unmarshall(
            marshaled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)
        self.assertEqual(
            unmarshalled_message.previous_size, original_previous_size
        )

    def test_retrieve_key_start(self):
        """test RetrieveKeyStart"""
        original_request_id = uuid.uuid1().hex
        original_avatar_id = 1001
        original_reply_exchange = "reply-exchange"
        original_reply_routing_header = "reply-header"
        original_key  = "abcdefghijk"
        message = RetrieveKeyStart(
            original_request_id,
            original_avatar_id,
            original_reply_exchange,
            original_reply_routing_header,
            original_key 
        )
        marshalled_message = message.marshall()
        unmarshalled_message = RetrieveKeyStart.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.avatar_id, original_avatar_id)
        self.assertEqual(
            unmarshalled_message.reply_exchange, original_reply_exchange
        )
        self.assertEqual(
            unmarshalled_message.reply_routing_header, original_reply_routing_header
        )
        self.assertEqual(unmarshalled_message.key, original_key)

    def test_retrieve_key_start_reply_ok(self):
        """test RetrieveKeyStartReply"""
        original_database_content = generate_database_content()
        original_data_content = random_string(64 * 1024) 
        original_request_id = uuid.uuid1().hex
        original_result = 0
        message = RetrieveKeyStartReply(
            original_request_id,
            original_result,
            original_database_content.timestamp,
            original_database_content.is_tombstone,
            original_database_content.segment_number,
            original_database_content.segment_count,
            original_database_content.segment_size,
            original_database_content.total_size,
            original_database_content.adler32,
            original_database_content.md5,
            original_data_content
        )
        marshaled_message = message.marshall()
        unmarshalled_message = RetrieveKeyStartReply.unmarshall(
            marshaled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)
        self.assertEqual(
            unmarshalled_message.timestamp, 
            original_database_content.timestamp
        )
        self.assertEqual(
            unmarshalled_message.is_tombstone, 
            original_database_content.is_tombstone
        )
        self.assertEqual(
            unmarshalled_message.segment_number, 
            original_database_content.segment_number
        )
        self.assertEqual(
            unmarshalled_message.segment_count, 
            original_database_content.segment_count
        )
        self.assertEqual(
            unmarshalled_message.segment_size, 
            original_database_content.segment_size
        )
        self.assertEqual(
            unmarshalled_message.total_size, 
            original_database_content.total_size
        )
        self.assertEqual(
            unmarshalled_message.adler32, 
            original_database_content.adler32
        )
        self.assertEqual(
            unmarshalled_message.md5, 
            original_database_content.md5
        )
        self.assertEqual(
            unmarshalled_message.data_content, original_data_content
        )

    def test_retrieve_key_next(self):
        """test RetrieveKeyNext"""
        original_request_id = uuid.uuid1().hex
        original_sequence  = 2
        message = RetrieveKeyNext(
            original_request_id,
            original_sequence 
        )
        marshalled_message = message.marshall()
        unmarshalled_message = RetrieveKeyNext.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.sequence, original_sequence)

    def test_retrieve_key_next_reply_ok(self):
        """test RetrieveKeyNextReply"""
        original_data_content = random_string(64 * 1024) 
        original_request_id = uuid.uuid1().hex
        original_result = 0
        message = RetrieveKeyNextReply(
            original_request_id,
            original_result,
            original_data_content
        )
        marshaled_message = message.marshall()
        unmarshalled_message = RetrieveKeyNextReply.unmarshall(
            marshaled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)
        self.assertEqual(
            unmarshalled_message.data_content, original_data_content
        )

    def test_retrieve_key_final(self):
        """test RetrieveKeyFinal"""
        original_request_id = uuid.uuid1().hex
        original_sequence  = 2
        message = RetrieveKeyFinal(
            original_request_id,
            original_sequence 
        )
        marshalled_message = message.marshall()
        unmarshalled_message = RetrieveKeyFinal.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.sequence, original_sequence)

    def test_retrieve_key_final_reply_ok(self):
        """test RetrieveKeyFinalReply"""
        original_data_content = random_string(64 * 1024) 
        original_request_id = uuid.uuid1().hex
        original_result = 0
        message = RetrieveKeyFinalReply(
            original_request_id,
            original_result,
            original_data_content
        )
        marshaled_message = message.marshall()
        unmarshalled_message = RetrieveKeyFinalReply.unmarshall(
            marshaled_message
        )
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)
        self.assertEqual(
            unmarshalled_message.data_content, original_data_content
        )

    def test_destroy_key(self):
        """test DestroyKey"""
        original_request_id = uuid.uuid1().hex
        original_avatar_id  = 1001
        original_reply_exchange = "reply-exchange"
        original_reply_routing_header = "reply-header"
        original_key = "test.key"
        original_timestamp = time.time()
        message = DestroyKey(
            original_request_id,
            original_avatar_id,
            original_reply_exchange,
            original_reply_routing_header,
            original_key,
            original_timestamp
        )
        marshalled_message = message.marshall()
        unmarshalled_message = DestroyKey.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.avatar_id, original_avatar_id)
        self.assertEqual(
            unmarshalled_message.reply_exchange, original_reply_exchange
        )
        self.assertEqual(
            unmarshalled_message.reply_routing_header, 
            original_reply_routing_header
        )
        self.assertEqual(unmarshalled_message.key, original_key)
        self.assertEqual(unmarshalled_message.timestamp, original_timestamp)

    def test_destroy_key_reply_ok(self):
        """test DestroyKeyReply"""
        original_request_id = uuid.uuid1().hex
        original_result = 0
        original_total_size = 43L
        message = DestroyKeyReply(
            original_request_id,
            original_result,
            original_total_size
        )
        marshalled_message = message.marshall()
        unmarshalled_message = DestroyKeyReply.unmarshall(marshalled_message)
        self.assertEqual(unmarshalled_message.request_id, original_request_id)
        self.assertEqual(unmarshalled_message.result, original_result)
        self.assertEqual(unmarshalled_message.total_size, original_total_size)

if __name__ == "__main__":
    unittest.main()
