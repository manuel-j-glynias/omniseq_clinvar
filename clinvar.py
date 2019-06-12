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

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
    benign = getCount(sigDict,'benign') + getCount(sigDict,'likely benign')
    uncertain = getCount(sigDict,'uncertain significance')
    return pathogenic, benign,  uncertain
    
    
def get_shouldReport(sigDict):
    shouldReport = False
    pathogenic, benign,  uncertain = getAllCounts(sigDict)
    if (pathogenic + uncertain >= benign):
        shouldReport = True
    return shouldReport
 
def get_isPathogenic(sigDict):
    isPathogenic = False
    pathogenic, benign,  uncertain = getAllCounts(sigDict)
    if (pathogenic  >= benign + uncertain):
        isPathogenic = True
    return isPathogenic
 
def get_isBenign(sigDict):
    isBenign = False
    pathogenic, benign,  uncertain = getAllCounts(sigDict)
    if (benign  >= pathogenic + uncertain):
        isBenign = True
    return isBenign
    

def getOneVariant(variationArchive):
    post_data = {
    'gene': '',
    'cDot': '',
    'pDot': '',
    'significance':'',
    'explain':'',
    'shouldReport': False,
    'isPathogenic': False,
    'isBenign': False
   }
    variantName = ''
    sigs = {}
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
    
    post_data['shouldReport'] = get_shouldReport(sigs)
    post_data['isPathogenic'] = get_isPathogenic(sigs)
    post_data['isBenign'] = get_isBenign(sigs)
       
    return post_data

 
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
       
        
def main():
    client = MongoClient('localhost', 27017)
    
    try:
    # inexpensive way to determine if mongo is up, if not then exit
        client.admin.command('ismaster')
    except ConnectionFailure:
        logger.critical("Server not available, exiting")
        sys.exit()
  
    filename = 'ClinVarVariationRelease_00-latest.xml'
    client.drop_database('omniseq')
    db = client.omniseq
    collection = db.create_collection("clinvar")
    parse_xml_file(filename,collection)
    os.remove(filename) 


main()
