#!/usr/bin/env python
# -*- coding: utf-8 -*- 

"""
Very simple tool for backup litres.ru catalog
(c) 2017 kiltum@kiltum.tech
pep8 --ignore=W191,E501 litres-backup.py
for work:
pip install tqdm
pip install rfc6266
"""

import sys
import argparse
import requests
from tqdm import tqdm
#import xml.etree.ElementTree as ET
import lxml.etree as ET
import rfc6266
import time
import re
import demjson
import os
import shutil
from PIL import Image
import img2pdf

FORMATS = ['fb2.zip', 'html', 'html.zip', 'txt', 'txt.zip', 'rtf.zip', 'a4.pdf', 'a6.pdf', 'mobi.prc', 'epub', 'ios.epub']
URL = "http://robot.litres.ru/pages/"
URL_www = "http://www.litres.ru"
TMP_DIR = "tmp"

def main(argv):
	parser = argparse.ArgumentParser(description='litres.ru backup tool')
	parser.add_argument("-u", "--user", help="Username")
	parser.add_argument("-p", "--password", help="Password")
	parser.add_argument("-f", "--format", default="ios.epub", help="Downloading format. 'list' for available")
	parser.add_argument("-d", "--debug", action="store_true", help="Add debug output")
	parser.add_argument("-v", "--verbosedebug", action="store_true", help="You really want to see what happens?")
	args = parser.parse_args()

	if args.format == 'list':
		for f in FORMATS:
			print f
		exit(0)
	else:
		if args.format not in FORMATS:
			print "I dont know this format: " + args.format
			exit(1)

	if str(args.user) == 'None' or str(args.password) == 'None':
		print "I cant work without username and passwords"
		exit(1)

	if args.debug:
		print "Will ask for downloading " + args.format
		print "Try to login to site as " + args.user

	r = requests.post(URL + "catalit_authorise/", data={'login': args.user, 'pwd': args.password})
	if args.debug:
		print "Responce : ", r.status_code, r.reason
		print "Responce text : " + r.text

	root = ET.fromstring(r.content)

	if root.tag == "catalit-authorization-failed":
		print "Authorization failed"
		exit(1)

	sid = root.attrib['sid']
	if args.debug:
		print "Welcome, ", root.attrib['login'], "(", root.attrib['mail'], ")"
		print "Asking litres.ru for list of books (can take a some time)"
		print "sid ", sid

	r = requests.post(URL + "catalit_browser/", data={'sid': sid, 'my': "1", 'limit': "0,1000"})

	if args.verbosedebug:
		print "Responce ", r.status_code, r.reason
		print "Responce text ", r.text

	root = ET.fromstring(r.content)

	count_total = root.attrib['records']
	if args.debug:
		print "Total books: ", count_total

	if args.verbosedebug:
		print root.tag, root.attrib

	count = 1

	for child in root:
		if args.verbosedebug:
			print child.tag, child.attrib
		hub_id = child.attrib['hub_id']
		file_size = 0

		for elem in child.iter():
			if elem.tag == 'file' and elem.attrib['type'] == args.format:
				file_size = elem.attrib['size']
			if args.verbosedebug:
				print elem.tag, elem.attrib, elem.text, file_size

		r = requests.post(URL + "catalit_download_book/", data={'sid': sid, 'art': hub_id, 'type': args.format}, stream=True)

		if args.debug:
			print "Responce ", r.status_code, r.reason

		filename = rfc6266.parse_requests_response(r).filename_unsafe
		print "(", count, "/", count_total, ")", filename
		with open(filename, "wb") as handle:
			for data in tqdm(r.iter_content(), unit='b', total=int(file_size)):
				handle.write(data)
		time.sleep(1)  # do not DDoS litres.
		count = count + 1

	r = requests.get(URL_www + "/pages/my_books_fresh/", cookies={'SID': sid})
	
	items = ET.HTML(r.content).xpath("//div[contains(@class, 'art-item')]")

	for item in items:
		link = item.xpath(".//a[contains(@class, 'art-buttons__read_purchased')]")
		info = item.xpath(".//div[@data-obj]")
		if len(link) != 1 or len(info) != 1:
			continue
		link = link[0]
		info = info[0]
		if args.verbosedebug:
			print "Book link", link.attrib['href']
			print "Book info", info.attrib['data-obj']
		data_obj = dict(demjson.decode(info.attrib['data-obj']))
		book_name = data_obj['author'] + '_' + data_obj['alt']
		fid = re.search( r"file=(\d+)&", link.attrib['href']).group(1)
		while len(fid)<8:
			fid = "0" + fid
		m = re.match(r"(\d\d)(\d\d)(\d\d)(\d\d)", fid)
		r = requests.get(URL_www + "/static/pdfjs/"+m.group(1)+"/"+m.group(2)+"/"+m.group(3)+"/"+fid+".js", cookies={'SID': sid})
		m = re.search(r"=\s(\{.+\});", r.text)
		js_obj = dict(demjson.decode(m.group(1)))
		max_w_index = 0
		for i, page in enumerate(js_obj['pages']):
			if page['p'][0]['w'] > js_obj['pages'][max_w_index]['p'][0]['w']:
				max_w_index = i
		pages = js_obj['pages'][max_w_index]['p']
		rt = js_obj['pages'][max_w_index]['rt']
		os.mkdir(TMP_DIR)
		imgs = []
		for i, page in enumerate(pages):
			r = requests.get(URL_www + "/pages/read_book_online/?file="+fid+"&page="+str(i)+"&rt="+rt+"&ft="+page['ext'], cookies={'SID': sid}) 
			img = TMP_DIR+'/'+str(i)+'.'+str(page['ext'])
			with open(img, 'wb') as f:
				f.write(r.content)
			imgs.append(img)
			if i%10 == 0:
				time.sleep(1)
		with open(book_name+'.pdf', "wb") as f:
			f.write(img2pdf.convert(imgs))
		shutil.rmtree(TMP_DIR)

if __name__ == "__main__":
	main(sys.argv[1:])
