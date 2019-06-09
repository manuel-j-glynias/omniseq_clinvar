#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 06:07:58 2019

@author: mglynias
"""

from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

import urllib.parse
import logging
import sys

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


app = Flask(__name__)
logger.debug('calling MongoClient')
client = MongoClient('localhost', 27017)
    
try:
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
except ConnectionFailure:
    logger.debug("Server not available, exiting")
    sys.exit()
 
db = client.omniseq
mycol = db["clinvar"]

@app.route('/')
def index():
    myDict = {'explain':'Server Works!'}
    return jsonify(myDict)
  

@app.route("/omniseq_api/v1/by_pdot/", methods=['GET'])
def handle_pdot():
    logger.debug("handle_pdot")
    myDict = {'explain':'Error!'}
    gene = request.args.get('gene', None) # use default value repalce 'None'
    logger.debug(gene)
    pdot = request.args.get('pDot', None)
    logger.debug(pdot)
    if (gene!=None and pdot!=None):
        myquery = { 'gene':gene, 'pDot':pdot}
        mydoc = mycol.find_one(myquery)
        if (mydoc != None):
            myDict = {'gene': mydoc['gene'], 'cDot': mydoc['cDot'], 'pDot': mydoc['pDot'],
                      'significance': mydoc['significance'], 'explain': mydoc['explain'],
                      'shouldReport':mydoc['shouldReport']}

    return jsonify(myDict)
 

@app.route("/omniseq_api/v1/by_cdot/", methods=['GET'])
def handle_cdot():
    myDict = {'explain':'Error!'}
    gene = request.args.get('gene', None) # use default value repalce 'None'
    cdot = urllib.parse.unquote(request.args.get('cDot', None))
    if (gene!=None and cdot!=None):
        myquery = { 'gene':gene, 'cDot':cdot}
        mydoc = mycol.find_one(myquery)
        if (mydoc != None):
            myDict = {'gene': mydoc['gene'], 'cDot': mydoc['cDot'], 'pDot': mydoc['pDot'],
                      'significance': mydoc['significance'], 'explain': mydoc['explain'],
                      'shouldReport':mydoc['shouldReport']}

    return jsonify(myDict)


@app.route("/omniseq_api/v1/shouldReport/", methods=['GET'])
def handle_shouldReport():
    myDict = {'explain':'Error!'}
    gene = request.args.get('gene', None) # use default value repalce 'None'
    pdot = request.args.get('pDot', None)
    if (gene!=None and pdot!=None):
        myquery = { 'gene':gene, 'pDot':pdot}
        mydoc = mycol.find_one(myquery)
        if (mydoc != None):
            myDict = {'shouldReport':mydoc['shouldReport']}

    return jsonify(myDict)

