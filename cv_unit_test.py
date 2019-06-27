#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 26 11:09:32 2019

@author: mglynias
"""

import unittest
import clinvar
#import pprint


class Test_read_gene_categories(unittest.TestCase):

    def test_read(self):
        gene_categories_dict = clinvar.read_gene_categories('gene_categories.csv')
#        pprint.pprint(gene_categories_dict)
        self.assertEqual(len(gene_categories_dict), 134, "Should be 144")

    def test_read_oncogene(self):
        gene_categories_dict = clinvar.read_gene_categories('gene_categories.csv')
        self.assertEqual(gene_categories_dict['BRAF'], 'Oncogene', "BRAF should be an oncogene")

    def test_read_tumor_supressor(self):
        gene_categories_dict = clinvar.read_gene_categories('gene_categories.csv')
        self.assertEqual(gene_categories_dict['BRCA1'], 'Tumor Suppressor Gene', "BRCA1 should be an Tumor Suppressor Gene")
    
    def test_build_gene_category_db(self):
        client = clinvar.get_mongo_client()
        client.drop_database('omniseq')
        db = client.omniseq
        clinvar.build_gene_categories_db(db)


   

if __name__ == '__main__':
    unittest.main()