# -*- coding: utf-8 -*-
"""
destroyer.py

A class that performs a destroy query on all data writers.
"""
import logging

import gevent
import gevent.pool

from diyapi_web_server.exceptions import (
    AlreadyInProgress,
    DestroyFailedError,
)

from diyapi_web_server.local_database_util import most_recent_timestamp_for_key

class Destroyer(object):
    """Performs a destroy query on all data writers."""
    def __init__(
        self, 
        node_local_connection,
        data_writers,
        collection_id, 
        key,
        timestamp        
    ):
        self.log = logging.getLogger('Destroyer')
        self.log.info('collection_id=%d, key=%r' % (collection_id, key, ))
        self._node_local_connection = node_local_connection
        self.data_writers = data_writers
        self.collection_id = collection_id
        self.key = key
        self.timestamp = timestamp
        self._pending = gevent.pool.Group()
        self._done = []

    def _join(self, timeout):
        self._pending.join(timeout, True)
        # make sure _done_link gets run first by cooperating
        gevent.sleep(0)
        if not self._pending:
            return
        raise DestroyFailedError()

    def _done_link(self, task):
        if isinstance(task.value, gevent.GreenletExit):
            return
        self._done.append(task)

    def _spawn(self, segment_num, data_writer, run, *args):
        method_name = run.__name__
        task = self._pending.spawn(run, *args)
        task.rawlink(self._done_link)
        task.segment_num = segment_num
        task.data_writer = data_writer
        task.method_name = method_name
        return task

    def destroy(self, timeout=None):
        if self._pending:
            raise AlreadyInProgress()

        # TODO: find a non-blocking way to do this
        file_info = most_recent_timestamp_for_key(
            self._node_local_connection , self.collection_id, self.key
        )

        file_size = (0 if file_info is None else file_info.file_size)

        for i, data_writer in enumerate(self.data_writers):
            segment_num = i + 1
            self._spawn(
                segment_num,
                data_writer,
                data_writer.destroy_key,
                self.collection_id,
                self.key,
                self.timestamp,
                segment_num
            )
        self._join(timeout)
        self._done = []

        return file_size
