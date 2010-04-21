# -*- coding: utf-8 -*-
"""
sql_authenticator.py

Authenticates requests
"""
import time
import hmac
import hashlib


class SqlAuthenticator(object):
    def __init__(self, connection):
        self.connection = connection

    def _string_to_sign(self, req):
        return '\n'.join((
            req.method,
            req.headers['x-diyapi-timestamp'],
        ))

    def _get_key(self, key_id):
        cur = self.connection.cursor()
        cur.execute('select key from diy_key where key_id=%s',
                    [key_id])
        row = cur.fetchone()
        if row:
            return row[0]

    def authenticate(self, req):
        try:
            auth_type, auth_string = req.authorization
        except TypeError:
            return False
        if auth_type != 'DIYAPI':
            return False
        try:
            key_id, signature = auth_string.split(':', 1)
        except TypeError:
            return False
        key = self._get_key(key_id)
        if not key:
            return False
        try:
            string_to_sign = self._string_to_sign(req)
        except KeyError:
            return False
        try:
            timestamp = int(req.headers['x-diyapi-timestamp'])
        except (TypeError, ValueError):
            return False
        if abs(time.time() - timestamp) > 600:
            return False
        expected = hmac.new(key, string_to_sign, hashlib.sha256).hexdigest()
        if signature != expected:
            return False
        req.remote_user = int(key_id)
        return True
