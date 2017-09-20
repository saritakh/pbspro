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


class TestQueues(PBSTestSuite):

    """
    This test suite contains tests related to queues

    """

    @tags('smoke')
    def test_create_execution_queue(self):
        """
        Test to create execution queue
        """
        qname = 'testq'
        try:
            self.server.manager(MGR_CMD_DELETE, QUEUE, None, qname)
        except:
            pass
        a = {'queue_type': 'Execution', 'enabled': 'True', 'started': 'True'}
        self.server.manager(MGR_CMD_CREATE, QUEUE, a, qname, expect=True)
        self.server.manager(MGR_CMD_DELETE, QUEUE, id=qname)

    @tags('smoke')
    def test_create_routing_queue(self):
        """
        Test to create routing queue
        """
        qname = 'routeq'
        try:
            self.server.manager(MGR_CMD_DELETE, QUEUE, None, qname)
        except:
            pass
        a = {'queue_type': 'Route', 'started': 'True'}
        self.server.manager(MGR_CMD_CREATE, QUEUE, a, qname, expect=True)
        self.server.manager(MGR_CMD_DELETE, QUEUE, id=qname)

    @tags('smoke')
    def test_route_queue(self):
        """
        Verify that a routing queue routes a job into the appropriate execution
        queue.
        """
        a = {'queue_type': 'Execution', 'resources_min.ncpus': 1,
             'enabled': 'True', 'started': 'False'}
        self.server.manager(MGR_CMD_CREATE, QUEUE, a, id='specialq')
        dflt_q = self.server.default_queue
        a = {'queue_type': 'route',
             'route_destinations': dflt_q + ',specialq',
             'enabled': 'True', 'started': 'True'}
        self.server.manager(MGR_CMD_CREATE, QUEUE, a, id='routeq')
        a = {'resources_min.ncpus': 4}
        self.server.manager(MGR_CMD_SET, QUEUE, a, id=dflt_q)
        j = Job(TEST_USER, attrs={ATTR_queue: 'routeq',
                                  'Resource_List.ncpus': 1})
        jid = self.server.submit(j)
        self.server.expect(JOB, {ATTR_queue: 'specialq'}, id=jid)

