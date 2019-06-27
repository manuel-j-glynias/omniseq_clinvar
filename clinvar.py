#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 16:47:53 2019

@author: mglynias
"""
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
import logging
import sys
import csv
import pprint

#oncogene:  if majority vote is benign, suppress
#Tumor Suppressor:  if majority vote is pathogenic+uncertain


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_csv_dict_list(variables_file): 
    reader = csv.DictReader(open(variables_file, 'r'))
    dict_list = []
    for line in reader:
        dict_list.append(line)
    return dict_list
 
def get_csv_dict_list_dictionary(csv_dict_list,key1,key2, acceptable_categories):
    dd = {}
    for d in csv_dict_list:
        if d[key2] in acceptable_categories:
            dd[d[key1]] = d[key2]
    return dd   


def read_gene_categories(path):
    csv_dict_list = get_csv_dict_list(path)
    gene_dict = get_csv_dict_list_dictionary(csv_dict_list,'gene','category',['Oncogene','Tumor Suppressor Gene'])
    return gene_dict
    
def get_cDot(variantName):
  if (len(variantName)>0 and ':' in variantName):
      vn = variantName.split(':')[1]
      if (' ' in vn):
          variantName = vn.split()[0]
      else:
          variantName = vn
  return variantName
    

def getSignificanceTuple(sigDict):
    maxVal = 0
    maxName = ''
    explain = ''
    for significance in sigDict:
        if (len(explain) > 0):
            explain += "/"
        explain += significance + "(" + str(sigDict[significance]) +  ")"
        if (sigDict[significance] > maxVal):
            maxVal = sigDict[significance]
            maxName = significance
    return maxName,explain

def getCount(sigDict,key):
    count = 0
    if key in sigDict:
        count = sigDict[key]
    return count
    

def getAllCounts(sigDict):
    pathogenic = getCount(sigDict,'pathogenic') + getCount(sigDict,'likely pathogenic') + getCount(sigDict,'drug response')
    benign = getCount(sigDict,'benign') + getCount(sigDict,'likely benign') + getCount('no known pathogenicity')
    uncertain = getCount(sigDict,'uncertain significance')
    return pathogenic, benign,  uncertain
    
 #oncogene:  if majority vote is benign, suppress  if its null, report
#Tumor Suppressor:  if majority vote is pathogenic+uncertain
   
 
def is_majority_vote_not_benign(sigDict):
    shouldReport = False
    pathogenic, benign,  uncertain = getAllCounts(sigDict)
    if (pathogenic + uncertain) >= benign:    # i.e. if majority vote is pathogenic+uncertain, then report; so report any non-benign variant in p53
        shouldReport = True
    return shouldReport
     

def getOneVariant(variationArchive):
    post_data = {
    'variant_id': '',
    'gene': '',
    'cDot': '',
    'pDot': '',
    'significance':'',
    'explain':'',
    'is_majority_vote_not_benign': False,
   }
    variantName = ''
    sigs = {}
    for simpleAllele in variationArchive.iter('SimpleAllele'):
        if 'VariationID' in simpleAllele.attrib:
            post_data['variant_id'] = simpleAllele.attrib['VariationID']
    for gene in variationArchive.iter('Gene'):
       post_data['gene'] = gene.attrib['Symbol']
    for name in variationArchive.iter('Name'):
        if (len(variantName) == 0):
            variantName = name.text
    for proteinChange in variationArchive.iter('ProteinChange'):
        post_data['pDot'] = proteinChange.text
    for clinicalAssertion in variationArchive.iter('ClinicalAssertion'):
       for child in clinicalAssertion:
           if (child.tag=='Interpretation'):
               for gc in child:
                   if (gc.tag=='Description'):
                       significance = gc.text.lower()
                       sigs[significance] = sigs.get(significance, 0) + 1
    post_data['cDot'] = get_cDot(variantName)
            
    post_data['significance'], post_data['explain'] = getSignificanceTuple(sigs)
    
    post_data['is_majority_vote_not_benign'] = is_majority_vote_not_benign(sigs)
       
    return post_data

#for testing
def parse_xml_file_no_db(path):
    counter = 0
    for event, elem in ET.iterparse(path):
        if event == 'end':
            if elem.tag == 'VariationArchive':
                post_data = getOneVariant(elem)
                print(post_data)
                counter += 1
                if (counter > 10):
                    break
                elem.clear() # discard the element
 
    

def parse_xml_file(path,collection):
    counter = 0
    for event, elem in ET.iterparse(path):
        if event == 'end':
            if elem.tag == 'VariationArchive':
                post_data = getOneVariant(elem)
                _ = collection.insert_one(post_data)
                counter += 1
                if (counter % 10000 ==0):
                    message = str(counter) + ' ' + post_data['gene'] + ' ' + post_data['cDot'] + ' ' + post_data['pDot']
                    logger.debug(message)
                elem.clear() # discard the element

def get_mongo_client():
    client = MongoClient('localhost', 27017)
    
    try:
    # inexpensive way to determine if mongo is up, if not then exit
        client.admin.command('ismaster')
    except ConnectionFailure:
        logger.critical("Server not available, exiting")
        sys.exit()
    return client

def build_clinvar_db(db):
    filename = 'ClinVarVariationRelease_00-latest.xml'
    collection = db.create_collection("clinvar")
    parse_xml_file(filename,collection)
    os.remove(filename) 
       
def build_gene_categories_db(db):
    filename = 'gene_categories.csv'
    collection = db.create_collection("gene_categories")
    gene_categories_dict = read_gene_categories(filename)
    for gene_category in gene_categories_dict:
        post_data = { 'gene': gene_category,  'category' : gene_categories_dict[gene_category] }
        _ = collection.insert_one(post_data)
         

def main():
    client = get_mongo_client()
    client.drop_database('omniseq')
    db = client.omniseq
    build_gene_categories_db(db)
    build_clinvar_db(db)
 
    

if __name__ == '__main__':
    main()
