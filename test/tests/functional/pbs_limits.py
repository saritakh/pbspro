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

from tests.functional import *

class TestLimits(TestFunctional):
    '''
    This test suite contains a few smoke tests of PBS
    '''

    @skipOnCpuSet
    @tags('smoke')
    def test_fgc_limits(self):
        """
        Test for limits
        """
        a = {'resources_available.ncpus': 4}
        self.server.create_vnodes('lt', a, 2, self.mom)
        a = {'max_run': '[u:' + str(TEST_USER) + '=2]'}
        self.server.manager(MGR_CMD_SET, SERVER, a)
        self.server.expect(SERVER, a)
        j1 = Job(TEST_USER)
        j2 = Job(TEST_USER)
        j3 = Job(TEST_USER)
        j1id = self.server.submit(j1)
        self.server.expect(JOB, {'job_state': 'R'}, j1id)
        j2id = self.server.submit(j2)
        self.server.expect(JOB, {'job_state': 'R'}, id=j2id)
        j3id = self.server.submit(j3)
        self.server.expect(JOB, 'comment', op=SET, id=j3id)
        self.server.expect(JOB, {'job_state': 'Q'}, id=j3id)

    @skipOnCpuSet
    @tags('smoke')
    def test_limits(self):
        """
        Test for limits
        """
        a = {'resources_available.ncpus': 4}
        self.server.create_vnodes('lt', a, 2, self.mom)
        a = {'max_run_res.ncpus': '[u:' + str(TEST_USER) + '=1]'}
        self.server.manager(MGR_CMD_SET, SERVER, a, expect=True)
        for _ in range(3):
            j = Job(TEST_USER)
            self.server.submit(j)
        a = {'server_state': 'Scheduling'}
        self.server.expect(SERVER, a, op=NE)
        a = {'job_state=R': 1, 'euser=' + str(TEST_USER): 1}
        self.server.expect(JOB, a, attrop=PTL_AND)

    @tags('smoke')
    def test_project_based_limits(self):
        """
        Test for project based limits
        """
        proj = 'testproject'
        a = {'max_run': '[p:' + proj + '=1]'}
        self.server.manager(MGR_CMD_SET, SERVER, a, expect=True)
        for _ in range(5):
            j = Job(TEST_USER, attrs={ATTR_project: proj})
            self.server.submit(j)
        self.server.expect(SERVER, {'server_state': 'Scheduling'}, op=NE)
        self.server.expect(JOB, {'job_state=R': 1})

