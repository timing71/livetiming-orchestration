###############################################################################
#  Based on code subject to the following:
#
#  Copyright (C) Tavendo GmbH and/or collaborators. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  1. Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#
###############################################################################

from autobahn.twisted.wamp import ApplicationSession
from autobahn.wamp.exception import ApplicationError
from twisted.internet.defer import inlineCallbacks

import os


LIVETIMING_SHARED_SECRET = os.environ.get('LIVETIMING_SHARED_SECRET', None)

if LIVETIMING_SHARED_SECRET is None:
    raise Exception("LIVETIMING_SHARED_SECRET not set, zombie invasion inevitable")


USERS = {
    'directory': {
        'secret': LIVETIMING_SHARED_SECRET,
        'role': u"services"
    },
    'services': {
        'secret': LIVETIMING_SHARED_SECRET,
        'role': u"services"
    },
}


class AuthenticatorSession(ApplicationSession):

    @inlineCallbacks
    def onJoin(self, details):
        def authenticate(realm, authid, details):
            self.log.info("WAMP-CRA dynamic authenticator invoked: realm='{}', authid='{}'".format(realm, authid))

            if authid in USERS:
                # return a dictionary with authentication information ...
                return USERS[authid]
            else:
                raise ApplicationError(u'com.example.no_such_user', 'could not authenticate session - no such user {}'.format(authid))

        try:
            yield self.register(authenticate, u'livetiming.authenticate')
            self.log.info("WAMP-CRA dynamic authenticator registered!")
        except Exception as e:
            self.log.error("Failed to register dynamic authenticator: {0}".format(e))
