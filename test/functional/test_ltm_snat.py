# Copyright 2015-2106 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from requests.exceptions import HTTPError

from f5.bigip.ltm.snat import RequireOneOf

TESTDESCRIPTION = 'TESTDESCRIPTION'


def delete_snat(bigip, name, partition):
    s = bigip.ltm.snatcollection.snat
    try:
        s.load(name=name, partition=partition)
    except HTTPError as err:
        if err.response.status_code != 404:
            raise
        return
    s.delete()


def setup_create_test(request, bigip, name, partition):
    def teardown():
        delete_snat(bigip, name, partition)
    request.addfinalizer(teardown)
    snat1 = bigip.ltm.snatcollection.snat
    return snat1


def setup_basic_test(request, bigip, name, partition, orig='1.1.1.1'):
    def teardown():
        delete_snat(bigip, name, partition)

    snat1 = bigip.ltm.snatcollection.snat
    snat_collection1 = bigip.ltm.snatcollection
    snat1.create(name=name, partition=partition, origins=orig, automap=True)
    request.addfinalizer(teardown)
    return snat1, snat_collection1


class TestSNAT(object):
    def test_create_no_args(self, request, bigip):
        snat1 = setup_create_test(request, bigip, 'TESTNAME', 'Common')
        with pytest.raises(RequireOneOf):
            snat1.create()

    def test_create(self, request, bigip):
        snat1 = setup_create_test(request, bigip, 'snat1', 'Common')
        snat1.create(name='snat1', partition='Common', origins='1.1.1.1',
                     automap=True)
        assert snat1.name == 'snat1'
        assert snat1.partition == 'Common'
        assert snat1.generation and isinstance(snat1.generation, int)
        assert snat1.kind == 'tm:ltm:snat:snatstate'
        assert snat1.selfLink.startswith(
            'https://localhost/mgmt/tm/ltm/snat/~Common~snat1')

    def test_update_and_refresh(self, request, bigip):
        snat1, sc1 = setup_basic_test(request, bigip, 'snat1', 'Common')
        snat1.description = TESTDESCRIPTION
        snat1.update()
        assert snat1.description == TESTDESCRIPTION
        snat1.description = "NEWDESCRIPTION"
        snat1.refresh()
        assert snat1.description == TESTDESCRIPTION
        snat1.description = "NEWDESCRIPTION"
        snat1.update()
        assert snat1.description == "NEWDESCRIPTION"

    def test_load_and_delete(self, request, bigip):
        snat1, sc1 = setup_basic_test(request, bigip, 'snat1', 'Common')
        snat2 = sc1.snat
        snat2.load(name='snat1', partition='Common')
        snat1.delete()
        assert snat1.__dict__ == {'deleted': True}
