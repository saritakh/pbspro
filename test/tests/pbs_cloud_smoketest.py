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

#CLOUD = 'test-cloud-'
CLOUD = 'x19'

@tags('smoke')
class CloudSmokeTest(PBSTestSuite):

    """
    This test suite contains a few smoke tests of PBS

    """

    def test_submit_cloud_job(self):
        """
        Test to submit a job
        """

        a = {'log_events': 2047}
        self.server.manager(MGR_CMD_SET, SERVER, a, expect=True)

        self.scheduler.add_resource('node_location',apply=True)
        a = {'resources_default.node_location': 'local'}
        self.server.manager(MGR_CMD_SET, QUEUE, a, id='workq')

        j1 = Job(TEST_USER)
        j2 = Job('centos',
                 attrs={'queue': 'cloudq3',
                        'Resource_List.select': '1:ncpus=1'})
        j2.set_sleep_time(1000)


        j3 = Job('centos',
                 attrs={'queue': 'cloudq3',
                        'Resource_List.select': '1:ncpus=1'})

        #jid1 = self.server.submit(j1)
        jid2 = self.server.submit(j2)
        jid3 = self.server.submit(j3)

        #self.server.expect(JOB, {'job_state': 'R'}, id=jid1)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid2)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid3,
                           max_attempts=60,interval=10)

        self.server.expect(JOB, {'exec_vnode': (MATCH,CLOUD)}, id=jid3)
