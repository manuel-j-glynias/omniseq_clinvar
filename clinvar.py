#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 16:47:53 2019

@author: mglynias
"""
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from ftplib import FTP
import gzip
import os
import logging
import sys

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# =============================================================================
# def convertPDot(pDot):
#     print(pDot)
#     aaConvert = {'Ala':'A', 'Cyc':'C', 'Asp':'D', 'Glu':'E', 'Phe':'F','Gly':'G','His':'H','Ile':'I',
#                  'Lys':'K', 'Leu':'L','Met':'M', 'Asn':'N', 'Pro':'P', 'Gln':'Q', 'Arg':'R',
#                  'Ser':'S', 'Thr':'T', 'Val':'V', 'Trp':'W', 'Tyr':'Y', 'Ter':'X'}
#     p = pDot[3:-1]
#     fs = False
#     if (p.endswith('fs')):
#         fs = True
#         p = p[:-2]
#     firstAA = aaConvert[p[:3]]
#     lastAA = aaConvert[p[-3:]]
#     res = p[3:-3]
#     p = firstAA + res + lastAA
#     if (fs):
#         p += " fs"
#     return p
#     
# =============================================================================


def clinvar_fetcher(filename):
    ftp = FTP('ftp.ncbi.nlm.nih.gov')
    ftp.login() 
    ftp.cwd('pub/clinvar/xml/clinvar_variation') 
    localfile = open(filename, 'wb')
    ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
    ftp.quit()
    localfile.close()

def uncompress_clinvar(filename,outfilename):
    inF = gzip.open(filename, 'rb')
    outF = open(outfilename, 'wb')
    outF.write( inF.read() )
    inF.close()
    outF.close()


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
    
    
def get_shouldReport(sigDict):
    reported = False
    pathogenic = getCount(sigDict,'Pathogenic') + getCount(sigDict,'Likely pathogenic') + getCount(sigDict,'drug response')
    benign = getCount(sigDict,'Benign') + getCount(sigDict,'Likely benign')
    uncertain = getCount(sigDict,'Uncertain significance')
    if (pathogenic + uncertain >= benign):
        reported = True
    return reported
    

def getOneVariant(variationArchive):
    post_data = {
    'gene': '',
    'cDot': '',
    'pDot': '',
    'significance':'',
    'explain':'',
    'shouldReport': False
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
                       significance = gc.text
                       sigs[significance] = sigs.get(significance, 0) + 1
    post_data['cDot'] = get_cDot(variantName)
            
    post_data['significance'], post_data['explain'] = getSignificanceTuple(sigs)
    
    post_data['shouldReport'] = get_shouldReport(sigs)
    
#    print(post_data['gene'],post_data['cDot'],post_data['pDot'],post_data['significance'],post_data['explain'],post_data['shouldReport'])  
    
    
    return post_data

 
def parse_xml_file(path,collection):
    counter = 0
    for event, elem in ET.iterparse(path):
        if event == 'end':
            if elem.tag == 'VariationArchive':
                post_data = getOneVariant(elem)
                _ = collection.insert_one(post_data)
                counter += 1
                if (counter % 1000 ==0):
                    message = str(counter) + post_data['gene'], post_data['cDot']
                    logger.debug(message)
#                print('One post: {0}'.format(result.inserted_id))
                elem.clear() # discard the element
       
        
def main():
    logger.debug('calling MongoClient')
    client = MongoClient('localhost', 27017)
    
    try:
    # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
    except ConnectionFailure:
        logger.debug("Server not available, exiting")
        sys.exit()
  
    filename = 'ClinVarVariationRelease_00-latest.xml'
    gz = filename + '.gz'
    logger.debug('calling clinvar_fetcher')
    clinvar_fetcher(gz)
    logger.debug('calling uncompress_clinvar')
    uncompress_clinvar(gz,filename)
    os.remove(gz) 
    client.drop_database('omniseq')
    db = client.omniseq
    collection = db.create_collection("clinvar")
    parse_xml_file(filename,collection)
    os.remove(filename) 


main()
