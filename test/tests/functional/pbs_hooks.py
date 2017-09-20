# coding: utf-8

# Copyright (C) 1994-2017 Altair Engineering, Inc.
# For more information, contact Altair at www.altair.com.
#
# This file is part of the PBS Professional ("PBS Pro") software.
#
# Open Source License Information:
#
# PBS Pro is free software. You can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# PBS Pro is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Commercial License Information:
#
# The PBS Pro software is licensed under the terms of the GNU Affero General
# Public License agreement ("AGPL"), except where a separate commercial license
# agreement for PBS Pro version 14 or later has been executed in writing with
# Altair.
#
# Altair’s dual-license business model allows companies, individuals, and
# organizations to create proprietary derivative works of PBS Pro and
# distribute them - whether embedded or bundled with other software - under
# a commercial license agreement.
#
# Use of Altair’s trademarks, including but not limited to "PBS™",
# "PBS Professional®", and "PBS Pro™" and Altair’s logos is subject to Altair's
# trademark licensing policies.

from ptl.utils.pbs_testsuite import *


class SmokeTest(PBSTestSuite):

    """
    This test suite contains a few smoke tests of PBS

    """

    @tags('smoke')
    def test_server_hook(self):
        """
        Create a hook, import a hook content that rejects all jobs, verify
        that a job is rejected by the hook.
        """
        hook_name = "testhook"
        hook_body = "import pbs\npbs.event().reject('my custom message')\n"
        a = {'event': 'queuejob', 'enabled': 'True'}
        self.server.create_import_hook(hook_name, a, hook_body)
        self.server.manager(MGR_CMD_SET, SERVER, {'log_events': 2047},
                            expect=True)
        j = Job(TEST_USER)
        try:
            self.server.submit(j)
        except PbsSubmitError:
            pass
        self.server.log_match("my custom message")

    @tags('smoke')
    def test_mom_hook(self):
        """
        Create a hook, import a hook content that rejects all jobs, verify
        that a job is rejected by the hook.
        """
        hook_name = "momhook"
        hook_body = "import pbs\npbs.event().reject('my custom message')\n"
        a = {'event': 'execjob_begin', 'enabled': 'True'}
        self.server.create_import_hook(hook_name, a, hook_body)
        # Asynchronous copy of hook content, we wait for the copy to occur
        self.server.log_match(".*successfully sent hook file.*" +
                              hook_name + ".PY" + ".*", regexp=True,
                              max_attempts=100, interval=5)
        j = Job(TEST_USER)
        jid = self.server.submit(j)
        self.server.expect(JOB, {ATTR_state: 'H'}, id=jid)
        self.mom.log_match("my custom message", max_attempts=10,
                           starttime=self.server.ctime)
