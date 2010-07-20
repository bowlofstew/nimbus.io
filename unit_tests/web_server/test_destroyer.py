# -*- coding: utf-8 -*-
"""
test_destroyer.py

test diyapi_web_server/destroyer.py
"""
import os
import unittest
import uuid
import logging

from unit_tests.util import generate_key
from unit_tests.web_server import util

from diyapi_web_server.amqp_data_writer import AMQPDataWriter
from diyapi_web_server.exceptions import DestroyFailedError

from messages.destroy_key import DestroyKey
from messages.destroy_key_reply import DestroyKeyReply

from diyapi_web_server.destroyer import Destroyer


EXCHANGES = os.environ['DIY_NODE_EXCHANGES'].split()


class TestDestroyer(unittest.TestCase):
    """test diyapi_web_server/destroyer.py"""
    def setUp(self):
        self.amqp_handler = util.FakeAMQPHandler()
        self.data_writers = [AMQPDataWriter(self.amqp_handler, exchange)
                             for exchange in EXCHANGES]
        self._key_generator = generate_key()
        self._real_uuid1 = uuid.uuid1
        uuid.uuid1 = util.fake_uuid_gen().next
        self.log = logging.getLogger('TestDestroyer')

    def tearDown(self):
        uuid.uuid1 = self._real_uuid1

    def _make_messages(self, avatar_id, timestamp, key):
        base_size = 12345
        messages = []
        messages_to_append = []
        for i, data_writer in enumerate(self.data_writers):
            request_id = uuid.UUID(int=i).hex
            message = DestroyKey(
                request_id,
                avatar_id,
                self.amqp_handler.exchange,
                self.amqp_handler.queue_name,
                timestamp,
                key,
                i + 1,   # segment_number
                0        # version number
            )
            reply = DestroyKeyReply(
                request_id,
                DestroyKeyReply.successful,
                base_size + i
            )
            messages.append((message, data_writer.exchange))
            if data_writer.is_down:
                for handoff_data_writer in self.data_writers[1:3]:
                    self.amqp_handler.replies_to_send_by_exchange[(
                        request_id, handoff_data_writer.exchange
                    )].put(reply)
                    messages_to_append.append((
                        message, handoff_data_writer.exchange))
            else:
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, data_writer.exchange
                )].put(reply)
        messages.extend(messages_to_append)
        return base_size, messages

    def test_destroy(self):
        self.log.debug('test_destroy')
        avatar_id = 1001
        key = self._key_generator.next()
        timestamp = util.fake_time()
        base_size, messages = self._make_messages(avatar_id, timestamp, key)

        destroyer = Destroyer(self.data_writers)
        size_deleted = destroyer.destroy(avatar_id, key, timestamp, 0)

        self.assertEqual(size_deleted, base_size)

        expected = [
            (message.marshall(), exchange)
            for message, exchange in messages
        ]
        actual = [
            (message.marshall(), exchange)
            for message, exchange in self.amqp_handler.messages
        ]
        self.assertEqual(
            actual, expected, 
            'destroyer did not send expected messages %s %s' % (
                len(expected), len(actual),
            )
        )

    def test_destroy_with_failure(self):
        self.log.debug('test_destroy_with_failure')
        avatar_id = 1001
        key = self._key_generator.next()
        timestamp = util.fake_time()
        self.data_writers[0].mark_down()
        base_size, messages = self._make_messages(avatar_id, timestamp, key)
        self.data_writers[0].mark_up()

        destroyer = Destroyer(self.data_writers)
        self.assertRaises(
            DestroyFailedError,
            destroyer.destroy, avatar_id, key, timestamp, 0
        )

if __name__ == "__main__":
    from diyapi_tools.standard_logging import initialize_logging
    _log_path = "/var/log/pandora/test_web_server.log"
    initialize_logging(_log_path)
    unittest.main()