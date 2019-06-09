#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  9 18:34:20 2019

@author: mglynias
"""

from ftplib import FTP
import logging
import sys

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



def clinvar_fetcher(filename):
    try:
        ftp = FTP('ftp.ncbi.nlm.nih.gov')
        ftp.login() 
        ftp.cwd('pub/clinvar/xml/clinvar_variation') 
        localfile = open(filename, 'wb')
        ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
        ftp.quit()
        localfile.close()
    except:  
        message = "Unexpected error:" + sys.exc_info()[0]
        logger.debug(message)


def main():
    filename = 'ClinVarVariationRelease_00-latest.xml.gz'
    logger.debug('calling clinvar_fetcher')
    clinvar_fetcher(filename)
    logger.debug('calling uncompress_clinvar')
