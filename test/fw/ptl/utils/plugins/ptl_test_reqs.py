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
    Decorator to provide the cluster information required for a particular
    testcase or testsuite.
    """
    default_requirements = {
        'num_servers': 0,
        'num_moms': 1,
        'num_comms': 1,
        'num_clients': 1,
        'no_mom_on_server': 'False',
        'no_comm_on_server': 'False',
        'no_comm_on_mom': 'True'
    }
    reqobj = default_requirements
    def wrap_obj(obj):
        getreq = getattr(obj, REQKEY, {})
        if getreq:
            reqobj.update(getreq)
        for name, value in kwargs.iteritems():
            reqobj.update(kwargs)
        setattr(obj, REQKEY, reqobj)
        return obj
    return wrap_obj


class PTLTestReqs(Plugin):

    """
    Load test cases from given parameter
    """
    name = 'PTLTestReqs'
    score = sys.maxint - 3
    logger = logging.getLogger(__name__)

    def __init__(self):
        Plugin.__init__(self)
        self._test_marker = 'test_'
        self.requirements = {}
        self.prmcounts = { 
            'num_servers': 0,
            'num_moms': 1,
            'num_comms': 1,
            'num_clients': 1,
            'no_mom_on_server': 'False',
            'no_comm_on_server': 'False',
            'no_comm_on_mom': 'True'
        }

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
        paramkeys = ['server', 'servers', 'mom', 'moms', 'comms', 'client']
        tparam_dic = {}
        tparam_dic.update(self.prmcounts)
        for h in tparam.split(','):
            if '=' in h:
                k, v = h.split('=')
                if k in paramkeys:
                    if (k == 'server' or k == 'servers'):
                        tparam_dic['num_servers'] = len(v.split(':'))
                    if (k == 'mom' or k == 'moms'):
                        tparam_dic['num_moms'] = len(v.split(':'))
                    if k == 'comms':
                        tparam_dic['num_comms'] = len(v.split(':'))
                    if k == 'clients':
                        tparam_dic['num_clients'] = len(v.split(':'))
        self.prmcounts.update(tparam_dic)

    def configure(self, options, config):
        """
        Configure the plugin and system, based on selected options.

        attr and eval_attr may each be lists.

        self.attribs will be a list of lists of tuples. In that list, each
        list is a group of attributes, all of which must match for the rule to
        match.
        """
        self.config = config
        #self.requirements = getattr(method, REQKEY, {})
        #if self.requirements:
        #    self.enabled = True
        self.enabled = True

    def are_requirements_matching(self):
        """
        Validates test requirements against test cluster information
        returns True on match or False otherwise
        """
        keylist = ['num_servers', 'num_moms', 'num_comms', 'num_clients']
        if (len(self.prmcounts) and len(self.requirements)):
            for kl in keylist:
                if self.prmcounts[kl] < self.requirements[kl]:
                    return False

    def prepareTestCase(self, method):
        """
        Accept the method if its tags match.
        """
        try:
            cls = method.im_class
        except AttributeError:
            return False
        if not method.__name__.startswith(self._test_marker):
            return False
        self.requirements = getattr(method, REQKEY, {})
        #rv = self.are_requirements_matching(requirements)
        rv = self.are_requirements_matching()
        print 'here1'
        if rv is False:
            print "^^^^^^^^^^^^^^^^^^^^^ENTERED FALSE CONDITION"
            setattr(method, '__unittest_skip__', True)
            setattr(method, '__unittest_skip_why__', 'REQSKIPPED')
        return method
