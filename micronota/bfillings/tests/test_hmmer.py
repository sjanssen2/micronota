from tempfile import mkstemp
from os import getcwd, remove, close
from unittest import TestCase, main
from functools import partial
from skbio.util import get_data_path
from burrito.util import ApplicationError

from micronota.bfillings.hmmer import HMMscan, hmmscan_fasta


class HMMERTests(TestCase):

    def setUp(self):
        self.get_hmmer_path = partial(get_data_path,
                                      subfolder='hmmer')
        self.hmmdb_fp = self.get_hmmer_path('Pfam_B_1.hmm')
        self.positive_fps = list(map( self.get_hmmer_path,
                                      ['Pfam_B_1.fasta']))
        self.temp_fd, self.temp_fp = mkstemp()
    def tearDown(self):
        close(self.temp_fd)
        remove(self.temp_fp)

class HMMscanTest(HMMERTests):
    def test_base_command(self):
        c = HMMscan()
        print(c.BaseCommand)
        self.assertEqual(
            c.BaseCommand,
            'cd "%s/"; %s' % (getcwd(), c._command))

        params = {'--cpu': 2}
        for i in params:
            if params[i] is None:
                c.Parameters[i].on()
                cmd = 'cd "{d}/"; {cmd} {option}'.format(
                    d=getcwd(), cmd=c._command, option=i)
            else:
                c.Parameters[i].on(params[i])
                cmd = 'cd "{d}/"; {cmd} {option} {value}'.format(
                    d=getcwd(), cmd=c._command,
                    option=i, value=params[i])

            self.assertEqual(c.BaseCommand, cmd)
            c.Parameters[i].off()

    def test_scan_hmm_fasta(self):
        params = {'--noali': None,
                  '--tblout': self.temp_fp[1]}
        for f in self.positive_fps:
            res = hmmscan_fasta(self.hmmdb_fp, f, params)
            res['StdOut'].close()
            res['StdErr'].close()
            obs = res['--tblout']
            out_fp = '.'.join([f, 'tblout'])
            with open(out_fp) as exp:
                # skip comment lines as some contain running time info
                self.assertListEqual(
                    [i for i in exp.readlines() if not i.startswith('#')],
                    [j for j in obs.readlines() if not j.startswith('#')])
            obs.close()


class HMMPressTests(HMMERTests):
    def test_hmmpress_hmm_exist(self):
        with self.assertRaisesRegex(
                ApplicationError,
                r'Error: Looks like .* is already pressed'):
            hmmpress_hmm(self.hmm_fp)

    def test_compress_hmm(self):
        # .i1i file is different from run to run. skip it.
        suffices = ('i1f', 'i1m', 'i1p')
        exp = []
        for i in suffices:
            with open('.'.join([self.hmm_fp, i]), 'rb') as f:
                exp.append(f.read())

        res = hmmpress_hmm(self.hmm_fp, True)
        res['StdOut'].close()
        res['StdErr'].close()

        for i, e in zip(suffices, exp):
            with open('.'.join([self.hmm_fp, i]), 'rb') as f:
                self.assertEqual(f.read(), e)

if __name__=="__main__":
    main()
