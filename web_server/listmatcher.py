# -*- coding: utf-8 -*-
"""
listmatcher.py

A class that performs a listmatch query.
"""
import gevent

class Listmatcher(object):
    """Performs a listmatch query."""
    def __init__(self, node_local_connection):
        self._node_local_connection = node_local_connection

    def listmatch(self, collection_id, prefix, timeout=None):
        result = self._node_local_connection.fetch_all_rows(
            """
            select key from nimbusio_node.segment
            where collection_id = %s
            and file_tombstone = false
            and handoff_node_id is null
            and key like %s
            """.strip(),
            [collection_id, "%s%%" % prefix, ]
        )
        return [key for (key, ) in result]
