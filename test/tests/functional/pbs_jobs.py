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


class JobsTest(PBSTestSuite):

    """
    This test suite contains a few smoke tests of PBS

    """
    @tags('smoke')
    def test_submit_job(self):
        """
        Test to submit a job
        """
        j = Job(TEST_USER)
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid)

    @skipOnCpuSet
    @tags('smoke')
    def test_submit_job_array(self):
        """
        Test to submit a job array
        """
        a = {'resources_available.ncpus': 8}
        self.server.manager(MGR_CMD_SET, NODE, a, self.mom.shortname)
        j = Job(TEST_USER)
        j.set_attributes({ATTR_J: '1-3:1'})
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'B'}, jid)
        self.server.expect(JOB, {'job_state=R': 3}, count=True,
                           id=jid, extend='t')

    @tags('smoke')
    def test_select(self):
        """
        Test to qselect
        """
        j = Job(TEST_USER)
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'R'}, jid)
        jobs = self.server.select()
        self.assertNotEqual(jobs, None)

    @tags('smoke')
    def test_alter(self):
        """
        Test to alter job
        """
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'},
                            expect=True)
        j = Job(TEST_USER)
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'Q'}, id=jid)
        self.server.alterjob(jid, {'comment': 'job comment altered'})
        self.server.expect(JOB, {'comment': 'job comment altered'}, id=jid)

    @skipOnCray
    @tags('smoke')
    def test_sigjob(self):
        """
        Test to signal job
        """
        j = Job(TEST_USER)
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'R', 'substate': 42},
                           attrop=PTL_AND, id=jid)
        self.server.sigjob(jid, 'suspend')
        self.server.expect(JOB, {'job_state': 'S'}, id=jid)
        self.server.sigjob(jid, 'resume')
        self.server.expect(JOB, {'job_state': 'R'}, id=jid)

    @tags('smoke')
    def test_hold_release(self):
        """
        Test to hold and release a job
        """
        j = Job(TEST_USER)
        jid = self.server.submit(j)
        a = {'job_state': 'R', 'substate': '42'}
        self.server.expect(JOB, a, jid, attrop=PTL_AND)
        self.server.holdjob(jid, USER_HOLD)
        self.server.expect(JOB, {'Hold_Types': 'u'}, jid)
        self.server.rlsjob(jid, USER_HOLD)
        self.server.expect(JOB, {'Hold_Types': 'n'}, jid)

    @skipOnCpuSet
    @tags('smoke')
    def test_finished_jobs(self):
        """
        Test for finished jobs
        """
        a = {'resources_available.ncpus': '4'}
        self.server.manager(MGR_CMD_SET, NODE, a, self.mom.shortname,
                            expect=True)
        a = {'job_history_enable': 'True'}
        self.server.manager(MGR_CMD_SET, SERVER, a, expect=True)
        a = {'Resource_List.walltime': '10', ATTR_k: 'oe'}
        j = Job(TEST_USER, attrs=a)
        j.set_sleep_time(5)
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'F'}, extend='x', offset=5,
                           interval=1, id=jid)

    @tags('smoke')
    def test_shrink_to_fit(self):
        """
        Smoke test shrink to fit by setting a dedicated time to start in an
        hour and submit a job that can run for as low as 59 mn and as long as
        4 hours. Expect the job's walltime to be greater or equal than the
        minimum set.
        """
        a = {'resources_available.ncpus': 1}
        self.server.manager(MGR_CMD_SET, NODE, a, self.mom.shortname)
        now = time.time()
        self.scheduler.add_dedicated_time(start=now + 3600, end=now + 7200)
        j = Job(TEST_USER)
        a = {'Resource_List.max_walltime': '04:00:00',
             'Resource_List.min_walltime': '00:58:00'}
        j.set_attributes(a)
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid)
        attr = {'Resource_List.walltime':
                (GE, a['Resource_List.min_walltime'])}
        self.server.expect(JOB, attr, id=jid)

    @tags('smoke')
    def test_submit_job_with_script(self):
        """
        Test to submit job with job script
        """
        j = Job(TEST_USER, attrs={ATTR_N: 'test'})
        j.create_script('sleep 120\n', hostname=self.server.client)
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid)

    @tags('smoke')
    def test_movejob(self):
        """
        Verify that a job can be moved to another queue than the one it was
        originally submitted to
        """
        a = {'queue_type': 'Execution', 'enabled': 'True', 'started': 'True'}
        self.server.manager(MGR_CMD_CREATE, QUEUE, a, id='solverq')
        a = {'scheduling': 'False'}
        self.server.manager(MGR_CMD_SET, SERVER, a)
        j = Job(TEST_USER)
        jid = self.server.submit(j)
        self.server.movejob(jid, 'solverq')
        a = {'scheduling': 'True'}
        self.server.manager(MGR_CMD_SET, SERVER, a)
        self.server.expect(JOB, {ATTR_queue: 'solverq', 'job_state': 'R'},
                           attrop=PTL_AND)

    @tags('smoke')
    def test_printjob(self):
        """
        Verify that printjob can be executed
        """
        j = Job(TEST_USER)
        jid = self.server.submit(j)
        a = {'job_state': 'R', 'substate': 42}
        self.server.expect(JOB, a, id=jid)
        printjob = os.path.join(self.mom.pbs_conf['PBS_EXEC'], 'bin',
                                'printjob')
        jbfile = os.path.join(self.mom.pbs_conf['PBS_HOME'], 'mom_priv',
                              'jobs', jid + '.JB')
        ret = self.du.run_cmd(self.mom.hostname, cmd=[printjob, jbfile],
                              sudo=True)
        self.assertEqual(ret['rc'], 0)

    @checkModule("pexpect")
    @tags('smoke')
    def test_interactive_job(self):
        """
        Submit an interactive job
        """
        cmd = 'sleep 10'
        j = Job(TEST_USER, attrs={ATTR_inter: ''})
        j.interactive_script = [('hostname', '.*'),
                                (cmd, '.*')]
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'R'}, id=jid)
        self.server.delete(jid)
        self.server.expect(JOB, 'queue', op=UNSET, id=jid)
