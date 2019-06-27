#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 11:09:32 2019

@author: mglynias
"""

import unittest
import clinvar
#import pprint


class Test_read_parse_xml_file_no_db(unittest.TestCase):

    def test_read(self):
        filename = 'ClinVarVariationRelease_00-latest.xml'
        clinvar.parse_xml_file_no_db(filename)


   

if __name__ == '__main__':
    unittest.main()