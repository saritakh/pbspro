
from ptl.utils.pbs_testsuite import *

CLOUD = 'test-cloud-'
#CLOUD = 'x19'

@tags('smoke')
class CloudJobsTest(PBSTestSuite):

    """
    This test suite contains a few smoke tests of PBS

    """

    @timeout(1000)
    def test_submit_cloud_job(self):
        """
        Test to submit a job for cloud burst
        """
        #Workaround for increasing server log level
        a = {'log_events': 2047}
        self.server.manager(MGR_CMD_SET, SERVER, a, expect=True)

        #Workaround for adding node_location to sched_config resources line
        self.scheduler.add_resource('node_location',apply=True)

        #Workaround for adding workq default node_location=local
        a = {'resources_default.node_location': 'local'}
        self.server.manager(MGR_CMD_SET, QUEUE, a, id='workq')

        #Get list of Nodes that have ncpus > 0
        a = {'state':'free'}
        free_nodes = self.server.filter(NODE, a)
        nodes = free_nodes.values()[0]
        self.logger.info('skh - nodes are ' + str(nodes))

        #For every local node submit a workq job
        for n in nodes:
            j = Job('centos',
                    attrs={'Resource_List.select':'1:node_location=local',
                           'Resource_List.place': 'exclhost'})
            j.set_sleep_time(1000)
            jid = self.server.submit(j)
            self.server.expect(JOB, {'job_state': 'R'}, id=jid)

        #Submit a cloud job to cloudq3
        j3 = Job('centos',
                 attrs={'queue': 'cloudq3',
                        'Resource_List.select': '1:ncpus=1'})
        j3.set_sleep_time(100)
        jid3 = self.server.submit(j3)

        #Expect running state of cloud job
        self.server.expect(JOB, {'job_state': 'R'}, id=jid3,
                            max_attempts=60,interval=10)

        #Ensure exec_vnode of cloud job is a cloud node
        self.server.expect(JOB, {'exec_vnode': (MATCH,CLOUD)}, id=jid3)

        #Get list of Nodes that have ncpus > 0
        a = {'resources_available.ncpus': (GT, 0)}
        free_nodes = self.server.filter(NODE, a)
        nodes = free_nodes.values()[0]
        self.logger.info('skh - nodes after burst are ' + str(nodes))

        #Wait for cloud job to finish
        self.server.log_match(
            jid3 + ";Exit_status", max_attempts=30, interval=50)

        #Get list of Nodes that have ncpus > 0
        a = {'resources_available.ncpus': (GT, 0)}
        free_nodes = self.server.filter(NODE, a)
        nodes = free_nodes.values()[0]
        self.logger.info('skh - nodes after cloud job are ' + str(nodes))

        #Wait time for cloud node to unburst
        time.sleep(300)

        #Get list of Nodes that have ncpus > 0
        a = {'resources_available.ncpus': (GT, 0)}
        free_nodes = self.server.filter(NODE, a)
        nodes = free_nodes.values()[0]
        self.logger.info('skh - nodes after unburst are ' + str(nodes))

        if CLOUD not in str(nodes):
            self.logger.info('skh - cloud nodes unburst done')

