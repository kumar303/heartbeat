import subprocess
import unittest

import mock
from nose.tools import eq_

import heartbeat


class TestDstat(unittest.TestCase):
    output = """\
----total-cpu-usage---- -dsk/total- ------memory-usage----- -net/total- ---load-avg--- ---paging-- ---system-- ---procs--- --io/total- --filesystem- proc -most-expensive- --most-expensive-
usr sys idl wai hiq siq| read  writ| used  buff  cach  free| recv  send| 1m   5m  15m |  in   out | int   csw |run blk new| read  writ|files  inodes|tota|  cpu process   |  memory process
 45   3  52   0   0   0|  31k 1532B|48.2M 14.6M  108M  267M|   0     0 |3.81 2.56 2.35|   0     0 |2461   444 |  0   0 0.6|0.84  0.17 |  767   2896 |  69|darkice       42|mpd         9492k
 56   8  36   0   0   0|   0     0 |48.4M 14.6M  108M  267M| 198B 1348B|3.81 2.56 2.35|   0     0 |2661   619 |  0   0   0|   0     0 |  768   2896 |  69|darkice       41|mpd         9492k
""".strip().split('\n')

    def setUp(self):
        self.ds = heartbeat.Dstat()

    def test_parse(self):
        data = self.ds.parse(self.output)
        import pprint
        pprint.pprint(data)

        eq_(data['average']['cpu']['usr'], '45')
        eq_(data['average']['cpu']['sys'], '3')
        eq_(data['average']['cpu']['idl'], '52')
        eq_(data['average']['cpu']['wai'], '0')
        eq_(data['average']['cpu']['siq'], '0')

        eq_(data['average']['disk']['read'], '31k')
        eq_(data['average']['disk']['writ'], '1532B')

        eq_(data['average']['mem']['used'], '48.2M')
        eq_(data['average']['mem']['buff'], '14.6M')
        eq_(data['average']['mem']['cach'], '108M')
        eq_(data['average']['mem']['free'], '267M')

        eq_(data['average']['net']['recv'], '0')
        eq_(data['average']['net']['send'], '0')

        eq_(data['average']['load']['1m'], '3.81')
        eq_(data['average']['load']['5m'], '2.56')
        eq_(data['average']['load']['15m'], '2.35')

        eq_(data['average']['page']['in'], '0')
        eq_(data['average']['page']['out'], '0')

        eq_(data['average']['sys']['int'], '2461')
        eq_(data['average']['sys']['csw'], '444')

        eq_(data['average']['proc']['run'], '0')
        eq_(data['average']['proc']['blk'], '0')
        eq_(data['average']['proc']['new'], '0.6')

        eq_(data['average']['io']['read'], '0.84')
        eq_(data['average']['io']['writ'], '0.17')

        eq_(data['average']['fs']['files'], '767')
        eq_(data['average']['fs']['inodes'], '2896')

        eq_(data['average']['proc-count']['tota'], '69')

        eq_(data['average']['top-cpu']['cpu'], 'darkice')
        eq_(data['average']['top-cpu']['process'], '42')

        eq_(data['average']['top-mem']['memory'], 'mpd')
        eq_(data['average']['top-mem']['process'], '9492k')

        eq_(data['sample']['cpu']['usr'], '56')


@mock.patch('heartbeat.subprocess.check_output')
class TestIPAddr(unittest.TestCase):

    def test_good(self, out):
        out.return_value = '''\
wlan0     Link encap:Ethernet  HWaddr e0:91:53:62:ac:0a
          inet addr:10.0.1.22  Bcast:10.0.1.255  Mask:255.255.255.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:206316 errors:0 dropped:208633 overruns:0 frame:0
          TX packets:239308 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000
          RX bytes:37438823 (35.7 MiB)  TX bytes:293610377 (280.0 MiB)
'''
        eq_(heartbeat.get_ip_addr(), '10.0.1.22')

    def test_bad(self, out):
        out.side_effect = subprocess.CalledProcessError(1, 'ifconfig',
                                                        output='Device not found')
        eq_(heartbeat.get_ip_addr(), None)
