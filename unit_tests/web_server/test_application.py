# -*- coding: utf-8 -*-
"""
test_application.py

test diyapi_web_server/application.py
"""
import os
import unittest
import uuid
import random
import time
import zlib
import hashlib

from webtest import TestApp

from unit_tests.util import random_string, generate_key
from unit_tests.web_server import util
from diyapi_web_server.zfec_segmenter import ZfecSegmenter
from diyapi_web_server.amqp_exchange_manager import AMQPExchangeManager
from messages.archive_key_start_reply import ArchiveKeyStartReply
from messages.archive_key_next_reply import ArchiveKeyNextReply
from messages.archive_key_final_reply import ArchiveKeyFinalReply
from messages.database_listmatch_reply import DatabaseListMatchReply
from messages.retrieve_key_start_reply import RetrieveKeyStartReply
from messages.retrieve_key_next_reply import RetrieveKeyNextReply
from messages.retrieve_key_final_reply import RetrieveKeyFinalReply
from messages.destroy_key_reply import DestroyKeyReply

from diyapi_web_server import application
from diyapi_web_server.application import Application


EXCHANGES = os.environ['DIY_NODE_EXCHANGES'].split()


class TestApplication(unittest.TestCase):
    """test diyapi_web_server/application.py"""
    def setUp(self):
        self.exchange_manager = AMQPExchangeManager(EXCHANGES)
        self.authenticator = util.FakeAuthenticator(0)
        self.amqp_handler = util.FakeAMQPHandler()
        self.accounter = util.FakeAccounter()
        self.app = TestApp(Application(
            self.amqp_handler,
            self.exchange_manager,
            self.authenticator,
            self.accounter
        ))
        self._key_generator = generate_key()
        self._real_uuid1 = uuid.uuid1
        uuid.uuid1 = util.fake_uuid_gen().next
        self._real_sample = random.sample
        random.sample = util.fake_sample
        self._real_timeout = application.EXCHANGE_TIMEOUT
        application.EXCHANGE_TIMEOUT = 0
        self._real_time = time.time
        time.time = util.fake_time

    def tearDown(self):
        uuid.uuid1 = self._real_uuid1
        random.sample = self._real_sample
        time.time = self._real_time
        application.EXCHANGE_TIMEOUT = self._real_timeout

    def test_unauthorized(self):
        self.app.app.authenticator = util.FakeAuthenticator(None)
        self.app.get(
            '/data/some-key',
            dict(action='listmatch'),
            status=401
        )

    def test_archive_small(self):
        timestamp = time.time()
        for i in xrange(len(self.exchange_manager)):
            request_id = uuid.UUID(int=i).hex
            self.amqp_handler.replies_to_send[request_id].put(
                ArchiveKeyFinalReply(
                    request_id,
                    ArchiveKeyFinalReply.successful,
                    0
                )
            )
        avatar_id = self.authenticator.remote_user
        content = random_string(64 * 1024)
        key = self._key_generator.next()
        resp = self.app.post('/data/' + key, content)
        self.assertEqual(resp.body, 'OK')
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            len(content)
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_archive_small_with_overwrite(self):
        timestamp = time.time()
        old_size_per_slice = 12345
        old_size_total = 0
        for i in xrange(len(self.exchange_manager)):
            request_id = uuid.UUID(int=i).hex
            self.amqp_handler.replies_to_send[request_id].put(
                ArchiveKeyFinalReply(
                    request_id,
                    ArchiveKeyFinalReply.successful,
                    old_size_per_slice
                )
            )
            old_size_total += old_size_per_slice
        avatar_id = self.authenticator.remote_user
        content = random_string(64 * 1024)
        key = self._key_generator.next()
        resp = self.app.post('/data/' + key, content)
        self.assertEqual(resp.body, 'OK')
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            len(content)
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            old_size_total
        )

    def test_archive_small_with_handoff(self):
        timestamp = time.time()
        self.exchange_manager.mark_down(0)
        for i in xrange(len(self.exchange_manager)):
            request_id = uuid.UUID(int=i).hex
            message = ArchiveKeyFinalReply(
                request_id,
                ArchiveKeyFinalReply.successful,
                0
            )
            if self.exchange_manager.is_down(i):
                for exchange in self.exchange_manager.handoff_exchanges(i):
                    self.amqp_handler.replies_to_send_by_exchange[(
                        request_id, exchange
                    )].put(message)
            else:
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, self.exchange_manager[i]
                )].put(message)
        self.exchange_manager.mark_up(0)
        avatar_id = self.authenticator.remote_user
        content = random_string(64 * 1024)
        key = self._key_generator.next()
        resp = self.app.post('/data/' + key, content)
        self.assertEqual(resp.body, 'OK')
        self.assertTrue(self.exchange_manager.is_down(0))
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            len(content)
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_archive_small_with_handoff_failure(self):
        timestamp = time.time()
        self.exchange_manager.mark_down(0)
        for i in xrange(len(self.exchange_manager)):
            request_id = uuid.UUID(int=i).hex
            message = ArchiveKeyFinalReply(
                request_id,
                ArchiveKeyFinalReply.successful,
                0
            )
            if self.exchange_manager.is_down(i):
                for j, exchange in enumerate(
                    self.exchange_manager.handoff_exchanges(i)):
                        if j != 0:
                            self.amqp_handler.replies_to_send_by_exchange[(
                                request_id, exchange
                            )].put(message)
            else:
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, self.exchange_manager[i]
                )].put(message)
        self.exchange_manager.mark_up(0)
        avatar_id = self.authenticator.remote_user
        content = random_string(64 * 1024)
        key = self._key_generator.next()
        resp = self.app.post('/data/' + key, content, status=504)
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_archive_large(self):
        timestamp = time.time()
        avatar_id = self.authenticator.remote_user
        content_length = 1024 * 1024 * 3
        for i in xrange(len(self.exchange_manager)):
            request_id = uuid.UUID(int=i).hex
            self.amqp_handler.replies_to_send[request_id].put(
                ArchiveKeyStartReply(
                    request_id,
                    ArchiveKeyStartReply.successful,
                    0
                )
            )
            self.amqp_handler.replies_to_send[request_id].put(
                ArchiveKeyNextReply(
                    request_id,
                    ArchiveKeyNextReply.successful,
                    0
                )
            )
            self.amqp_handler.replies_to_send[request_id].put(
                ArchiveKeyFinalReply(
                    request_id,
                    ArchiveKeyFinalReply.successful,
                    0
                )
            )
        key = self._key_generator.next()
        with open('/dev/urandom', 'rb') as f:
            resp = self.app.request(
                '/data/' + key,
                method='POST',
                headers={
                    'content-length': str(content_length),
                },
                body_file=f,
            )
        self.assertEqual(resp.body, 'OK')
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            content_length
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_archive_large_with_handoff(self):
        timestamp = time.time()
        avatar_id = self.authenticator.remote_user
        content_length = 1024 * 1024 * 3
        self.exchange_manager.mark_down(0)
        for i in xrange(len(self.exchange_manager)):
            request_id = uuid.UUID(int=i).hex
            for message in [
                ArchiveKeyStartReply(
                    request_id,
                    ArchiveKeyStartReply.successful,
                    0
                ),
                ArchiveKeyNextReply(
                    request_id,
                    ArchiveKeyNextReply.successful,
                    0
                ),
                ArchiveKeyFinalReply(
                    request_id,
                    ArchiveKeyFinalReply.successful,
                    0
                ),
            ]:
                if self.exchange_manager.is_down(i):
                    for exchange in self.exchange_manager.handoff_exchanges(i):
                        self.amqp_handler.replies_to_send_by_exchange[(
                            request_id, exchange
                        )].put(message)
                else:
                    self.amqp_handler.replies_to_send_by_exchange[(
                        request_id, self.exchange_manager[i]
                    )].put(message)
        self.exchange_manager.mark_up(0)
        key = self._key_generator.next()
        with open('/dev/urandom', 'rb') as f:
            resp = self.app.request(
                '/data/' + key,
                method='POST',
                headers={
                    'content-length': str(content_length),
                },
                body_file=f,
            )
        self.assertEqual(resp.body, 'OK')
        self.assertTrue(self.exchange_manager.is_down(0))
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            content_length
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_archive_large_with_archive_failure(self):
        timestamp = time.time()
        avatar_id = self.authenticator.remote_user
        content_length = 1024 * 1024 * 3
        self.exchange_manager.mark_down(0)
        for i in xrange(len(self.exchange_manager)):
            request_id = uuid.UUID(int=i).hex
            for j, message in enumerate([
                ArchiveKeyStartReply(
                    request_id,
                    ArchiveKeyStartReply.successful,
                    0
                ),
                ArchiveKeyNextReply(
                    request_id,
                    ArchiveKeyNextReply.successful,
                    0
                ),
                ArchiveKeyFinalReply(
                    request_id,
                    ArchiveKeyFinalReply.successful,
                    0
                ),
            ]):
                if self.exchange_manager.is_down(i):
                    for k, exchange in enumerate(
                        self.exchange_manager.handoff_exchanges(i)):
                            if not (j >=1 and k == 0):
                                self.amqp_handler.replies_to_send_by_exchange[(
                                    request_id, exchange
                                )].put(message)
                else:
                    self.amqp_handler.replies_to_send_by_exchange[(
                        request_id, self.exchange_manager[i]
                    )].put(message)
        self.exchange_manager.mark_up(0)
        key = self._key_generator.next()
        with open('/dev/urandom', 'rb') as f:
            resp = self.app.request(
                '/data/' + key,
                method='POST',
                headers={
                    'content-length': str(content_length),
                },
                body_file=f,
                status=504
            )
        self.assertTrue(self.exchange_manager.is_down(0))
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    # TODO: test archive without content-length header

    def test_listmatch(self):
        prefix = 'a_prefix'
        key_list = ['%s-%d' % (prefix, i) for i in xrange(10)]
        request_id = uuid.UUID(int=0).hex
        self.amqp_handler.replies_to_send[request_id].put(
            DatabaseListMatchReply(
                request_id,
                DatabaseListMatchReply.successful,
                key_list=key_list
            )
        )
        resp = self.app.get('/data/%s' % (prefix,), dict(action='listmatch'))
        self.assertEqual(resp.body, repr(key_list))

    def test_retrieve_nonexistent(self):
        avatar_id = self.authenticator.remote_user
        key = self._key_generator.next()
        timestamp = time.time()

        for i in xrange(len(self.exchange_manager)):
            request_id = uuid.UUID(int=i).hex
            self.amqp_handler.replies_to_send[request_id].put(
                RetrieveKeyStartReply(
                    request_id,
                    RetrieveKeyStartReply.error_key_not_found,
                    error_message='key not found',
                )
            )

        resp = self.app.get('/data/%s' % (key,),
                            status=404)
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_retrieve_small(self):
        avatar_id = self.authenticator.remote_user
        key = self._key_generator.next()
        timestamp = time.time()
        file_size = 1024
        data_content = random_string(file_size)
        file_adler32 = zlib.adler32(data_content)
        file_md5 = hashlib.md5(data_content).digest()

        segmenter = ZfecSegmenter(
            8, # TODO: min_segments
            len(self.exchange_manager))
        segments = segmenter.encode(data_content)

        for segment_number, segment in enumerate(segments):
            segment_number += 1
            segment_adler32 = zlib.adler32(segment)
            segment_md5 = hashlib.md5(segment).digest()
            request_id = uuid.UUID(int=segment_number - 1).hex
            self.amqp_handler.replies_to_send[request_id].put(
                RetrieveKeyStartReply(
                    request_id,
                    RetrieveKeyStartReply.successful,
                    timestamp,
                    False,
                    0,  # version number
                    segment_number,
                    1,  # num slices
                    len(data_content),
                    file_size,
                    file_adler32,
                    file_md5,
                    segment_adler32,
                    segment_md5,
                    segment
                )
            )

        resp = self.app.get('/data/%s' % (key,))
        self.assertEqual(len(resp.body), file_size)
        self.assertEqual(resp.body, data_content)
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            file_size
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_retrieve_small_when_exchange_is_down(self):
        avatar_id = self.authenticator.remote_user
        key = self._key_generator.next()
        timestamp = time.time()
        file_size = 1024
        data_content = random_string(file_size)
        file_adler32 = zlib.adler32(data_content)
        file_md5 = hashlib.md5(data_content).digest()

        segmenter = ZfecSegmenter(
            8, # TODO: min_segments
            len(self.exchange_manager))
        segments = segmenter.encode(data_content)

        self.exchange_manager.mark_down(0)
        for i, segment in enumerate(segments):
            segment_adler32 = zlib.adler32(segment)
            segment_md5 = hashlib.md5(segment).digest()
            request_id = uuid.UUID(int=i).hex
            if not self.exchange_manager.is_down(i):
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, self.exchange_manager[i]
                )].put(
                    RetrieveKeyStartReply(
                        request_id,
                        RetrieveKeyStartReply.successful,
                        timestamp,
                        False,
                        0,      # version number
                        i + 1,  # segment number
                        1,      # num slices
                        len(data_content),
                        file_size,
                        file_adler32,
                        file_md5,
                        segment_adler32,
                        segment_md5,
                        segment
                    )
                )

        resp = self.app.get('/data/%s' % (key,))
        self.assertEqual(len(resp.body), file_size)
        self.assertEqual(resp.body, data_content)
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            file_size
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_retrieve_large(self):
        avatar_id = self.authenticator.remote_user
        key = self._key_generator.next()
        timestamp = time.time()
        n_slices = 3
        slice_size = 1
        file_size = slice_size * n_slices
        data_list = [random_string(slice_size)
                     for _ in xrange(n_slices)]
        data_content = ''.join(data_list)
        file_adler32 = zlib.adler32(data_content)
        file_md5 = hashlib.md5(data_content).digest()

        for sequence_number, slice in enumerate(data_list):
            segmenter = ZfecSegmenter(
                8, # TODO: min_segments
                len(self.exchange_manager))
            segments = segmenter.encode(slice)
            for segment_number, segment in enumerate(segments):
                segment_number += 1
                segment_adler32 = zlib.adler32(segment)
                segment_md5 = hashlib.md5(segment).digest()
                request_id = uuid.UUID(int=segment_number - 1).hex
                if sequence_number == 0:
                    self.amqp_handler.replies_to_send[request_id].put(
                        RetrieveKeyStartReply(
                            request_id,
                            RetrieveKeyStartReply.successful,
                            timestamp,
                            False,
                            0,  # version number
                            segment_number,
                            n_slices,
                            len(slice),
                            file_size,
                            file_adler32,
                            file_md5,
                            segment_adler32,
                            segment_md5,
                            segment
                        )
                    )
                elif sequence_number == n_slices - 1:
                    self.amqp_handler.replies_to_send[request_id].put(
                        RetrieveKeyFinalReply(
                            request_id,
                            sequence_number,
                            RetrieveKeyFinalReply.successful,
                            segment
                        )
                    )
                else:
                    self.amqp_handler.replies_to_send[request_id].put(
                        RetrieveKeyNextReply(
                            request_id,
                            sequence_number,
                            RetrieveKeyNextReply.successful,
                            segment
                        )
                    )

        resp = self.app.get('/data/%s' % (key,))
        self.assertEqual(len(resp.body), file_size)
        self.assertEqual(resp.body, data_content)
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            file_size
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )

    def test_destroy(self):
        avatar_id = self.authenticator.remote_user
        key = self._key_generator.next()
        base_size = 12345
        timestamp = time.time()
        for i, exchange in enumerate(self.exchange_manager):
            request_id = uuid.UUID(int=i).hex
            self.amqp_handler.replies_to_send[request_id].put(
                DestroyKeyReply(
                    request_id,
                    DestroyKeyReply.successful,
                    base_size + i
                )
            )

        resp = self.app.delete('/data/%s' % (key,))
        self.assertEqual(resp.body, 'OK')
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            base_size
        )

    def test_destroy_with_handoff(self):
        avatar_id = self.authenticator.remote_user
        key = self._key_generator.next()
        base_size = 12345
        timestamp = time.time()
        self.exchange_manager.mark_down(0)
        for i, exchange in enumerate(self.exchange_manager):
            request_id = uuid.UUID(int=i).hex
            message = DestroyKeyReply(
                request_id,
                DestroyKeyReply.successful,
                base_size + i
            )
            if self.exchange_manager.is_down(i):
                for exchange in self.exchange_manager.handoff_exchanges(i):
                    self.amqp_handler.replies_to_send_by_exchange[(
                        request_id, exchange
                    )].put(message)
            else:
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, self.exchange_manager[i]
                )].put(message)
        self.exchange_manager.mark_up(0)

        resp = self.app.delete('/data/%s' % (key,))
        self.assertEqual(resp.body, 'OK')
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            base_size
        )

    def test_destroy_with_handoff_failure(self):
        avatar_id = self.authenticator.remote_user
        key = self._key_generator.next()
        base_size = 12345
        timestamp = time.time()
        self.exchange_manager.mark_down(0)
        for i, exchange in enumerate(self.exchange_manager):
            request_id = uuid.UUID(int=i).hex
            message = DestroyKeyReply(
                request_id,
                DestroyKeyReply.successful,
                base_size + i
            )
            if self.exchange_manager.is_down(i):
                for j, exchange in enumerate(
                    self.exchange_manager.handoff_exchanges(i)):
                        if j != 0:
                            self.amqp_handler.replies_to_send_by_exchange[(
                                request_id, exchange
                            )].put(message)
            else:
                self.amqp_handler.replies_to_send_by_exchange[(
                    request_id, self.exchange_manager[i]
                )].put(message)
        self.exchange_manager.mark_up(0)

        resp = self.app.delete('/data/%s' % (key,), status=504)
        self.assertEqual(
            self.accounter._added[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._retrieved[avatar_id, timestamp],
            0
        )
        self.assertEqual(
            self.accounter._removed[avatar_id, timestamp],
            0
        )


if __name__ == "__main__":
    unittest.main()
