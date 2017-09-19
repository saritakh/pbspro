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


@tags('sched')
class TestFairshare(TestFunctional):

    """
    Test the pbs_sched fairshare functionality.  
    """

    @skipOnCpuSet
    @tags('smoke')
    def test_fairshare(self):
        """
        Test for fairshare
        """
        a = {'fair_share': 'true ALL',
             'fairshare_usage_res': 'ncpus*walltime',
             'unknown_shares': 10}
        self.scheduler.set_sched_config(a)
        a = {'resources_available.ncpus': 4}
        self.server.create_vnodes('vnode', a, 4, self.mom)
        a = {'Resource_List.select': '1:ncpus=4'}
        for _ in range(10):
            j = Job(TEST_USER1, a)
            self.server.submit(j)
        a = {'job_state=R': 4}
        self.server.expect(JOB, a)
        self.logger.info('testinfo: waiting for walltime accumulation')
        running_jobs = self.server.filter(JOB, {'job_state': 'R'})
        if running_jobs.values():
            for _j in running_jobs.values()[0]:
                a = {'resources_used.walltime': (NE, '00:00:00')}
                self.server.expect(JOB, a, id=_j, interval=1, max_attempts=30)
        j = Job(TEST_USER2)
        jid = self.server.submit(j)
        self.server.expect(JOB, {'job_state': 'Q'}, id=jid, offset=5)
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        a = {'server_state': 'Scheduling'}
        self.server.expect(SERVER, a, op=NE)
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        cycle = self.scheduler.cycles(start=self.server.ctime, lastN=10)
        if len(cycle) > 0:
            i = len(cycle) - 1
            while len(cycle[i].political_order) == 0:
                i -= 1
            cycle = cycle[i]
            firstconsidered = cycle.political_order[0]
            lastsubmitted = jid.split('.')[0]
            msg = 'testinfo: first job considered [' + str(firstconsidered) + \
                  '] == last submitted [' + str(lastsubmitted) + ']'
            self.logger.info(msg)
            self.assertEqual(firstconsidered, lastsubmitted)

    def setup_fs(self):

        self.scheduler.set_sched_config({'log_filter': '0'})

        self.scheduler.add_to_resource_group('grp1', 100, 'root', 60)
        self.scheduler.add_to_resource_group('grp2', 200, 'root', 40)
        self.scheduler.add_to_resource_group('pbsuser1', 101, 'grp1', 40)
        self.scheduler.add_to_resource_group('pbsuser2', 102, 'grp1', 20)
        self.scheduler.add_to_resource_group('pbsuser3', 201, 'grp2', 30)
        self.scheduler.add_to_resource_group('pbsuser4', 202, 'grp2', 10)
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduler_iteration': 7})
        a = {'fair_share': 'True', 'fairshare_decay_time': '24:00:00',
             'fairshare_decay_factor': 0.5}
        self.scheduler.set_sched_config(a)

    @skipOnCpuSet
    @tags('smoke')
    def test_fairshare_enhanced(self):
        """
        Test the basic fairshare behavior with custom resources for math module
        """

        rv = self.server.add_resource('foo1', 'float', 'nh')
        self.assertTrue(rv)

        self.setup_fs()

        a = {'fairshare_usage_res':
             'ceil(fabs(-ncpus*(foo1/100.00)*sqrt(100)))'}
        self.scheduler.set_sched_config(a)

        a = {'resources_available.ncpus': 1, 'resources_available.foo1': 5000}
        self.server.manager(MGR_CMD_SET, NODE, a, self.mom.shortname)

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        time.sleep(1)
        a = {'Resource_List.select': '1:ncpus=1:foo1=20',
             'Resource_List.walltime': 4}
        J1 = Job(TEST_USER2, attrs=a)
        a = {'Resource_List.select': '1:ncpus=1:foo1=20',
             'Resource_List.walltime': 4}
        J2 = Job(TEST_USER3, attrs=a)
        a = {'Resource_List.select': '1:ncpus=1:foo1=20',
             'Resource_List.walltime': 4}
        J3 = Job(TEST_USER1, attrs=a)
        j1id = self.server.submit(J1)
        j2id = self.server.submit(J2)
        j3id = self.server.submit(J3)
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        rv = self.server.expect(SERVER, {'server_state': 'Scheduling'}, op=NE)

        self.logger.info("Checking the job state of " + j3id)
        self.server.expect(
            JOB, {'job_state': 'R'}, id=j3id, max_attempts=30, interval=2)
        self.server.expect(
            JOB, {'job_state': 'Q'}, id=j2id, max_attempts=30, interval=2)
        self.server.expect(
            JOB, {'job_state': 'Q'}, id=j1id, max_attempts=30, interval=2)

        msg = "Checking the job state of " + j2id + ", runs after "
        msg += j3id + " completes"
        self.logger.info(msg)
        self.server.expect(
            JOB, {'job_state': 'R'}, id=j2id, max_attempts=30, interval=2)
        self.server.expect(
            JOB, {'job_state': 'Q'}, id=j1id, max_attempts=30, interval=2)

        msg = "Checking the job state of " + j1id + ", runs after "
        msg += j2id + " completes"
        self.logger.info(msg)
        self.server.expect(
            JOB, {'job_state': 'R'}, id=j1id, max_attempts=30, interval=2)

        self.server.log_match(
            j1id + ";Exit_status", max_attempts=30, interval=2)

        time.sleep(1)

        fs1 = self.scheduler.query_fairshare(name=str(TEST_USER1))
        self.logger.info('Checking ' + str(fs1.usage) + " == 3")
        self.assertEqual(fs1.usage, 3)

        fs2 = self.scheduler.query_fairshare(name=str(TEST_USER2))
        self.logger.info('Checking ' + str(fs2.usage) + " == 3")
        self.assertEqual(fs2.usage, 3)

        fs3 = self.scheduler.query_fairshare(name=str(TEST_USER3))
        self.logger.info('Checking ' + str(fs3.usage) + " == 3")
        self.assertEqual(fs3.usage, 3)

        fs4 = self.scheduler.query_fairshare(name=str(TEST_USER4))
        self.logger.info('Checking ' + str(fs4.usage) + " == 1")
        self.assertEqual(fs4.usage, 1)

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        time.sleep(1)
        a = {'Resource_List.select': '1:ncpus=1:foo1=20',
             'Resource_List.walltime': 4}
        J1 = Job(TEST_USER4, attrs=a)
        a = {'Resource_List.select': '1:ncpus=1:foo1=20',
             'Resource_List.walltime': 4}
        J2 = Job(TEST_USER2, attrs=a)
        a = {'Resource_List.select': '1:ncpus=1:foo1=20',
             'Resource_List.walltime': 4}
        J3 = Job(TEST_USER1, attrs=a)
        j1id = self.server.submit(J1)
        j2id = self.server.submit(J2)
        j3id = self.server.submit(J3)
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        rv = self.server.expect(SERVER, {'server_state': 'Scheduling'}, op=NE)

        self.logger.info("Checking the job state of " + j1id)
        self.server.expect(
            JOB, {'job_state': 'R'}, id=j1id, max_attempts=30, interval=2)
        self.server.expect(
            JOB, {'job_state': 'Q'}, id=j2id, max_attempts=30, interval=2)
        self.server.expect(
            JOB, {'job_state': 'Q'}, id=j3id, max_attempts=30, interval=2)

        msg = "Checking the job state of " + j3id + ", runs after "
        msg += j1id + " completes"
        self.logger.info(msg)
        self.server.expect(
            JOB, {'job_state': 'R'}, id=j3id, max_attempts=30, interval=2)
        self.server.expect(
            JOB, {'job_state': 'Q'}, id=j2id, max_attempts=30, interval=2)

        msg = "Checking the job state of " + j2id + ", runs after "
        msg += j1id + " completes"
        self.logger.info(msg)
        self.server.expect(
            JOB, {'job_state': 'R'}, id=j2id, max_attempts=30, interval=2)

        self.server.log_match(
            j2id + ";Exit_status", max_attempts=30, interval=2)

        time.sleep(1)

        fs1 = self.scheduler.query_fairshare(name=str(TEST_USER1))
        self.logger.info('Checking ' + str(fs1.usage) + " == 5")
        self.assertEqual(fs1.usage, 5)

        fs2 = self.scheduler.query_fairshare(name=str(TEST_USER2))
        self.logger.info('Checking ' + str(fs2.usage) + " == 5")
        self.assertEqual(fs2.usage, 5)

        fs3 = self.scheduler.query_fairshare(name=str(TEST_USER3))
        self.logger.info('Checking ' + str(fs3.usage) + " == 3")
        self.assertEqual(fs3.usage, 3)

        fs4 = self.scheduler.query_fairshare(name=str(TEST_USER4))
        self.logger.info('Checking ' + str(fs4.usage) + " == 3")
        self.assertEqual(fs4.usage, 3)

    def set_up_resource_group(self):
        """
        Set up the resource_group file for test suite
        """
        self.scheduler.add_to_resource_group('group1', 10, 'root', 40)
        self.scheduler.add_to_resource_group('group2', 20, 'root', 60)
        self.scheduler.add_to_resource_group(TEST_USER, 11, 'group1', 50)
        self.scheduler.add_to_resource_group(TEST_USER1, 12, 'group1', 50)
        self.scheduler.add_to_resource_group(TEST_USER2, 21, 'group2', 60)
        self.scheduler.add_to_resource_group(TEST_USER3, 22, 'group2', 40)
        self.scheduler.set_fairshare_usage(TEST_USER, 100)
        self.scheduler.set_fairshare_usage(TEST_USER1, 100)
        self.scheduler.set_fairshare_usage(TEST_USER3, 1000)

    def test_formula_keyword(self):
        """
        Test to see if 'fairshare_tree_usage' and 'fairshare_perc' are allowed
        to be set in the job_sort_formula
        """

        # manager() will throw a PbsManagerError exception if this fails
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'job_sort_formula': 'fairshare_tree_usage'})

        self.server.manager(MGR_CMD_SET, SERVER,
                            {'job_sort_formula': 'fairshare_perc'})

        formula = '"pow(2,-(fairshare_tree_usage/fairshare_perc))"'
        self.server.manager(MGR_CMD_SET, SERVER, {'job_sort_formula': formula})

        formula = 'fairshare_factor'
        self.server.manager(MGR_CMD_SET, SERVER, {'job_sort_formula': formula})

        formula = 'fair_share_factor'
        try:
            self.server.manager(
                MGR_CMD_SET, SERVER, {'job_sort_formula': formula})
        except PbsManagerError as e:
            self.assertTrue("Formula contains invalid keyword" in e.msg[0])

    def test_fairshare_formula(self):
        """
        Test fairshare in the formula.  Make sure the fairshare_tree_usage
        is correct
        """

        self.set_up_resource_group()
        self.scheduler.set_sched_config({'log_filter': 2048})

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'job_sort_formula': 'fairshare_tree_usage'})
        J1 = Job(TEST_USER)
        jid1 = self.server.submit(J1)
        J2 = Job(TEST_USER1)
        jid2 = self.server.submit(J2)
        J3 = Job(TEST_USER2)
        jid3 = self.server.submit(J3)
        J4 = Job(TEST_USER3)
        jid4 = self.server.submit(J4)
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        msg = ';Formula Evaluation = '
        self.scheduler.log_match(str(jid1) + msg + '0.1253', max_attempts=2)
        self.scheduler.log_match(str(jid2) + msg + '0.1253', max_attempts=2)
        self.scheduler.log_match(str(jid3) + msg + '0.5004', max_attempts=2)
        self.scheduler.log_match(str(jid4) + msg + '0.8330', max_attempts=2)

    def test_fairshare_formula2(self):
        """
        Test fairshare in the formula.  Make sure the fairshare_perc
        is correct
        """

        self.set_up_resource_group()
        self.scheduler.set_sched_config({'log_filter': 2048})

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        self.server.manager(MGR_CMD_SET, SERVER,
                            {'job_sort_formula': 'fairshare_perc'})
        J1 = Job(TEST_USER)
        jid1 = self.server.submit(J1)
        J2 = Job(TEST_USER1)
        jid2 = self.server.submit(J2)
        J3 = Job(TEST_USER2)
        jid3 = self.server.submit(J3)
        J4 = Job(TEST_USER3)
        jid4 = self.server.submit(J4)
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        msg = ';Formula Evaluation = '
        self.scheduler.log_match(str(jid1) + msg + '0.2', max_attempts=2)
        self.scheduler.log_match(str(jid2) + msg + '0.2', max_attempts=2)
        self.scheduler.log_match(str(jid3) + msg + '0.36', max_attempts=2)
        self.scheduler.log_match(str(jid4) + msg + '0.24', max_attempts=2)

    def test_fairshare_formula3(self):
        """
        Test fairshare in the formula.  Make sure entities with small usage
        are negatively affected by their high usage siblings.  Make sure that
        jobs run in the correct order.  Use fairshare_tree_usage in a
        pow() formula
        """

        self.set_up_resource_group()
        self.scheduler.set_sched_config({'log_filter': 2048})

        formula = '"pow(2,-(fairshare_tree_usage/fairshare_perc))"'

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        self.server.manager(MGR_CMD_SET, SERVER, {'job_sort_formula': formula})
        J1 = Job(TEST_USER2)
        jid1 = self.server.submit(J1)
        J2 = Job(TEST_USER3)
        jid2 = self.server.submit(J2)
        J3 = Job(TEST_USER)
        jid3 = self.server.submit(J3)
        J4 = Job(TEST_USER1)
        jid4 = self.server.submit(J4)
        t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        msg = ';Formula Evaluation = '
        self.scheduler.log_match(str(jid1) + msg + '0.3816', max_attempts=2)
        self.scheduler.log_match(str(jid2) + msg + '0.0902', max_attempts=2)
        self.scheduler.log_match(str(jid3) + msg + '0.6477', max_attempts=2)
        self.scheduler.log_match(str(jid4) + msg + '0.6477', max_attempts=2)
        self.scheduler.log_match('Leaving Scheduling Cycle', starttime=t)

        c = self.scheduler.cycles(lastN=1)[0]
        job_order = [jid3, jid4, jid1, jid2]
        for i in range(len(job_order)):
            self.assertEqual(job_order[i].split('.')[0], c.political_order[i])

    def test_fairshare_formula4(self):
        """
        Test fairshare in the formula.  Make sure entities with small usage
        are negatively affected by their high usage siblings.  Make sure that
        jobs run in the correct order.  Use keyword fairshare_factor
        """

        self.set_up_resource_group()
        self.scheduler.set_sched_config({'log_filter': 2048})

        formula = 'fairshare_factor'

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        self.server.manager(MGR_CMD_SET, SERVER, {'job_sort_formula': formula})

        J1 = Job(TEST_USER2)
        jid1 = self.server.submit(J1)
        J2 = Job(TEST_USER3)
        jid2 = self.server.submit(J2)
        J3 = Job(TEST_USER)
        jid3 = self.server.submit(J3)
        J4 = Job(TEST_USER1)
        jid4 = self.server.submit(J4)
        t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        msg = ';Formula Evaluation = '
        self.scheduler.log_match(str(jid1) + msg + '0.3816', max_attempts=2)
        self.scheduler.log_match(str(jid2) + msg + '0.0902', max_attempts=2)
        self.scheduler.log_match(str(jid3) + msg + '0.6477', max_attempts=2)
        self.scheduler.log_match(str(jid4) + msg + '0.6477', max_attempts=2)
        self.scheduler.log_match('Leaving Scheduling Cycle', starttime=t)

        c = self.scheduler.cycles(lastN=1)[0]
        job_order = [jid3, jid4, jid1, jid2]
        for i in range(len(job_order)):
            self.assertEqual(job_order[i].split('.')[0], c.political_order[i])

    def test_fairshare_formula5(self):
        """
        Test fairshare in the formula with fair_share set to true in scheduler.
        Make sure formula takes precedence over fairshare usage. Output will be
        same as in test_fairshare_formula4.
        """

        self.set_up_resource_group()
        a = {'log_filter': 2048, 'fair_share': "True All"}
        self.scheduler.set_sched_config(a)

        formula = 'fairshare_factor'

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        self.server.manager(MGR_CMD_SET, SERVER, {'job_sort_formula': formula})

        J1 = Job(TEST_USER2, {'Resource_List.cput': 10})
        jid1 = self.server.submit(J1)
        J2 = Job(TEST_USER3, {'Resource_List.cput': 20})
        jid2 = self.server.submit(J2)
        J3 = Job(TEST_USER, {'Resource_List.cput': 30})
        jid3 = self.server.submit(J3)
        J4 = Job(TEST_USER1, {'Resource_List.cput': 40})
        jid4 = self.server.submit(J4)
        t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        msg = ';Formula Evaluation = '
        self.scheduler.log_match(str(jid1) + msg + '0.3816', max_attempts=2)
        self.scheduler.log_match(str(jid2) + msg + '0.0902', max_attempts=2)
        self.scheduler.log_match(str(jid3) + msg + '0.6477', max_attempts=2)
        self.scheduler.log_match(str(jid4) + msg + '0.6477', max_attempts=2)
        self.scheduler.log_match('Leaving Scheduling Cycle', starttime=t)

        c = self.scheduler.cycles(start=t, lastN=1)[0]
        job_order = [jid3, jid4, jid1, jid2]
        for i in range(len(job_order)):
            self.assertEqual(job_order[i].split('.')[0], c.political_order[i])

    def test_fairshare_formula6(self):
        """
        Test fairshare in the formula.  Make sure entities with small usage
        are negatively affected by their high usage siblings.  Make sure that
        jobs run in the correct order.  Use keyword fairshare_factor
        with ncpus/walltime
        """

        self.set_up_resource_group()
        self.scheduler.set_sched_config({'log_filter': 2048})

        formula = '\"fairshare_factor + (walltime/ncpus)\"'

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        self.server.manager(MGR_CMD_SET, SERVER, {'job_sort_formula': formula})

        J1 = Job(TEST_USER2, {'Resource_List.ncpus': 1,
                              'Resource_List.walltime': "00:01:00"})
        jid1 = self.server.submit(J1)
        J2 = Job(TEST_USER3, {'Resource_List.ncpus': 2,
                              'Resource_List.walltime': "00:01:00"})
        jid2 = self.server.submit(J2)
        J3 = Job(TEST_USER, {'Resource_List.ncpus': 3,
                             'Resource_List.walltime': "00:02:00"})
        jid3 = self.server.submit(J3)
        J4 = Job(TEST_USER1, {'Resource_List.ncpus': 4,
                              'Resource_List.walltime': "00:02:00"})
        jid4 = self.server.submit(J4)
        t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})
        msg = ';Formula Evaluation = '
        self.scheduler.log_match(str(jid1) + msg + '60.3816', max_attempts=2)
        self.scheduler.log_match(str(jid2) + msg + '30.0902', max_attempts=2)
        self.scheduler.log_match(str(jid3) + msg + '40.6477', max_attempts=2)
        self.scheduler.log_match(str(jid4) + msg + '30.6477', max_attempts=2)
        self.scheduler.log_match('Leaving Scheduling Cycle', starttime=t)

        c = self.scheduler.cycles(start=t, lastN=1)[0]
        job_order = [jid1, jid3, jid4, jid2]
        for i in range(len(job_order)):
            self.assertEqual(job_order[i].split('.')[0], c.political_order[i])

    def test_pbsfs(self):
        """
        Test to see if running pbsfs affects the scheduler's view of the
        fairshare usage.  This is done by calling the Scheduler()'s
        revert_to_defaults().  This will call pbsfs -e to remove all usage.
        """

        self.scheduler.add_to_resource_group(TEST_USER, 11, 'root', 10)
        self.scheduler.add_to_resource_group(TEST_USER1, 12, 'root', 10)
        self.scheduler.set_sched_config({'fair_share': 'True'})

        self.scheduler.set_fairshare_usage(TEST_USER, 100)

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        J1 = Job(TEST_USER)
        jid1 = self.server.submit(J1)
        J2 = Job(TEST_USER1)
        jid2 = self.server.submit(J2)

        t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})

        self.scheduler.log_match('Leaving Scheduling Cycle', starttime=t,
                                 max_attempts=10)

        c = self.scheduler.cycles(lastN=1)[0]
        job_order = [jid2, jid1]
        for i in range(len(job_order)):
            self.assertEqual(job_order[i].split('.')[0], c.political_order[i])

        self.server.deljob(id=jid1, wait=True)
        self.server.deljob(id=jid2, wait=True)
        self.scheduler.revert_to_defaults()

        # Set TEST_USER1 to 50.  If revert_to_defaults() has affected the
        # scheduler's view of the fairshare usage, it's the only entity with
        # usage.  It's job will run second.  If revert_to_defaults() did
        # nothing, 50 is less than 100, so TEST_USER1's job will run first
        self.scheduler.add_to_resource_group(TEST_USER, 11, 'root', 10)
        self.scheduler.add_to_resource_group(TEST_USER1, 12, 'root', 10)
        self.scheduler.set_sched_config({'fair_share': 'True'})

        self.scheduler.set_fairshare_usage(TEST_USER1, 50)

        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'False'})
        J3 = Job(TEST_USER)
        jid3 = self.server.submit(J3)
        J4 = Job(TEST_USER1)
        jid4 = self.server.submit(J4)

        t = int(time.time())
        self.server.manager(MGR_CMD_SET, SERVER, {'scheduling': 'True'})

        self.scheduler.log_match('Leaving Scheduling Cycle', starttime=t,
                                 max_attempts=10)

        c = self.scheduler.cycles(lastN=1)[0]
        job_order = [jid3, jid4]
        for i in range(len(job_order)):
            self.assertEqual(job_order[i].split('.')[0], c.political_order[i])
