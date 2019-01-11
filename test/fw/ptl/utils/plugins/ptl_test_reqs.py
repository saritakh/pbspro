# coding: utf-8

# Copyright (C) 1994-2018 Altair Engineering, Inc.
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
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Commercial License Information:
#
# For a copy of the commercial license terms and conditions,
# go to: (http://www.pbspro.com/UserArea/agreement.html)
# or contact the Altair Legal Department.
#
# Altair’s dual-license business model allows companies, individuals, and
# organizations to create proprietary derivative works of PBS Pro and
# distribute them - whether embedded or bundled with other software -
# under a commercial license agreement.
#
# Use of Altair’s trademarks, including but not limited to "PBS™",
# "PBS Professional®", and "PBS Pro™" and Altair’s logos is subject to Altair's
# trademark licensing policies.

import sys
import logging
import unittest
from nose.plugins.base import Plugin
from nose.plugins.skip import SkipTest

log = logging.getLogger('nose.plugins.PTLTestReqs')

REQKEY = '__PTL_REQS_LIST__'


def requirements(*args, **kwargs):
    """
    Decorator that adds tags to classes or functions or methods
    """
    clusterparam_def = {
        'num_servers': 0,
        'num_moms': 1,
        'num_comms': 1,
        'num_clients': 1,
        'no_mom_on_server': 'False',
        'no_comm_on_server': 'False',
        'no_comm_on_mom': 'True'
    }
    reqobj = {}
    def wrap_obj(obj):
        reqobj = getattr(obj, REQKEY, {})
        for name, value in kwargs.items():
            if name not in clusterparam_def:
                #Error handling needs to be done
                _msg = 'Invalid requirements specified'
                #skip(_msg)
                print "Invalid requirements........"
        for name, value in kwargs.iteritems():
            #setattr(obj, name, value)
            reqobj[name] = value
        for l in clusterparam_def:
            if l not in reqobj:
                reqobj[l] = clusterparam_def[l]
        setattr(obj, REQKEY, reqobj)
        return obj
    return wrap_obj


class PTLTestReqs(Plugin):

    """
    Load test cases from given parameter
    """
    name = 'PTLTestReqs'
    score = sys.maxint - 7
    enabled = True
    logger = logging.getLogger(__name__)

    def __init__(self):
        Plugin.__init__(self)
        self.reqts = {}
        self._test_marker = 'test_'

    def options(self, parser, env):
        """
        Register command line options
        """
        pass

    def set_data(self, paramfile=None, testparam=None):
        tparam = ""
        if paramfile is not None:
            _pf = open(paramfile, 'r')
            _params_from_file = _pf.readlines()
            _pf.close()
            _nparams = []
            for l in range(len(_params_from_file)):
                if _params_from_file[l].startswith('#'):
                    continue
                else:
                    _nparams.append(_params_from_file[l])
            _f = ','.join(map(lambda l: l.strip('\r\n'), _nparams))
            if testparam is not None:
                tparam = testparam + ',' + _f
            else:
                tparam = _f
        dcount = ['server', 'servers', 'mom', 'moms', 'comms', 'client']
        pccount = {
            'num_servers': 0,
            'num_moms': 1,
            'num_comms': 1,
            'num_clients': 1,
            'no_mom_on_server': 'False',
            'no_comm_on_server': 'False',
            'no_comm_on_mom': 'True'
        }
        for h in tparam.split(','):
            if '=' in h:
                k, v = h.split('=')
                if k in dcount:
                    if (k == 'server' or k == 'servers'):
                        pccount['num_servers'] = len(v.split(':'))
                    if (k == 'mom' or k == 'moms'):
                        pccount['num_moms'] = len(v.split(':'))
                    if k == 'comms':
                        pccount['num_comms'] = len(v.split(':'))
                    if k == 'clients':
                        pccount['num_clients'] = len(v.split(':'))
        self.reqts = pccount

    def configure(self, options, config):
        """
        Configure the plugin and system, based on selected options.

        attr and eval_attr may each be lists.

        self.attribs will be a list of lists of tuples. In that list, each
        list is a group of attributes, all of which must match for the rule to
        match.
        """
        self.tags_to_check = []
        self.config = config
        self.enabled = True

    def wantClass(self, cls):
        """
        Accept the class if its subclass of TestCase and has at-least one
        test case
        """
        if not issubclass(cls, unittest.TestCase):
            return False
        has_test = False
        for t in dir(cls):
            if t.startswith(self._test_marker):
                has_test = True
                break
        if not has_test:
            return False

    def wantFunction(self, function):
        """
        Accept the function if its tags match.
        """
        return False

    def is_test_cluster_matching(self, reqt=None, clust=None):
        """
        Validates test requirements against test cluster information
        returns True on match or False otherwise
        """
        rv = True
        mn = ['num_servers', 'num_moms', 'num_comms', 'num_clients']
        if (reqt is not None and clust is not None):
            for k in mn:
                if clust[k] < reqt[k]:
                    rv = False
        return rv

    def wantMethod(self, method):
        """
        Accept the method if its tags match.
        """
        try:
            cls = method.im_class
        except AttributeError:
            return False
        if not method.__name__.startswith(self._test_marker):
            return False
        rcc = getattr(method, REQKEY, {})
        print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
        print rcc
        print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
        print self.reqts
        print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
        rv = self.is_test_cluster_matching(rcc, self.reqts)
        if rv is False:
            print "^^^^^^^^^^^^^^^^^^^^^ENTERED FALSE CONDITION"
            #if isclass(err[0]) and issubclass(err[0], SkipTest):
            #    status = 'SKIP'
            #    status_data = 'Reason = %s' % (err[1])
            #method.__unittest_skip__ = True
            #method.__unittest_skip_why__ = "Cluster not matching!!!!"
        return True
