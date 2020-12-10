import os
from unittest import TestCase

import yaml

from docstr_coverage.configFile import readConfigFile


class TestConfigFile(TestCase):
    def setUp(self) -> None:
        self.fakeOption = {"verbose": '1', 'exclude': "*/tests", 'skip_magic': False, 'skip_file_doc': False,
                           'skip_init': False,
                           'skip_class_def': False, 'skip_private': False, 'follow_links': False, 'fail_under': 100.0,
                           'badge': None, 'percentage_only': False, 'skip_magic_old': False, 'skip_file_doc_old': False,
                           'skipinit': False, 'skipclassdef': False, 'followlinks': False, 'failunder': None}
        self.fakeConfigFile = {"paths": ["tests", "docstr_coverage"], "verbose": '2', 'skip_magic': True, 'skip_file_doc': True,
                               'skip_init': True,
                               'skip_class_def': True, 'skip_private': True, 'follow_links': True, 'fail_under': 90,
                               'percentage_only': True}
        self.fakeConfigFile2 = {"paths": "docstr_coverage", "verbose": '2', 'skip_magic': True,
                               'skip_file_doc': True,
                               'skip_init': True,
                               'skip_class_def': True, 'skip_private': True, 'follow_links': True, 'fail_under': 90,
                               'percentage_only': True}

    def testReadConfigFileNoFile(self):
        """
        Test readConfigFile when .docstr.yaml is missing
        """
        path, kwargs = readConfigFile(("mypath",), self.fakeOption)
        self.assertEqual(path, ("mypath",))
        self.assertEqual(kwargs, self.fakeOption)

    def testReadConfigFile(self):
        """
        Test ReadConfigFile with fake .docstr.yaml with multiple paths
        """
        # fake .docstr.yaml
        with open('.docstr.yaml', 'w') as outfile:
            yaml.dump(self.fakeConfigFile, outfile, default_flow_style=False)

        path, kwargs = readConfigFile(("",), self.fakeOption)
        outfile.close()
        # remove fake file
        os.remove('.docstr.yaml')
        self.assertEqual(path, tuple(["tests", "docstr_coverage"]))
        self.assertEqual(kwargs.keys(), self.fakeOption.keys())
        self.assertEqual(kwargs["verbose"], self.fakeConfigFile["verbose"])
        self.assertEqual(kwargs["exclude"], self.fakeOption["exclude"])

    def testReadConfigFileWithStringPath(self):
        """
        Test ReadConfigFile with fake .docstr.yaml with only one path
        """
        # fake .docstr.yaml
        with open('.docstr.yaml', 'w') as outfile:
            yaml.dump(self.fakeConfigFile2, outfile, default_flow_style=False)

        path, kwargs = readConfigFile(("",), self.fakeOption)
        outfile.close()
        # remove fake file
        os.remove('.docstr.yaml')
        self.assertEqual(path, ('docstr_coverage',))
        self.assertEqual(kwargs.keys(), self.fakeOption.keys())
        self.assertEqual(kwargs["verbose"], self.fakeConfigFile["verbose"])
        self.assertEqual(kwargs["exclude"], self.fakeOption["exclude"])
