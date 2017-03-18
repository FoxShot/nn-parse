#!/usr/bin/env python3

from lxml import html
import requests
import re
import math
import urllib
from os.path import expanduser
home = expanduser("~")	#multi os support
import os
import configparser
import youtube_dl

class login(requests.Session):
	def __init__(self):
		requests.Session.__init__(self)
		config = configparser.SafeConfigParser()
		configfile = open(home + '/.config/nn-parse/config','r')
		config.readfp(configfile)
		username = config.get("user", "username")
		password = config.get("user", "password")
		payload = {
			"username": username,
			"password": password
		}
		login_url = "http://naurunappula.com/login.php?ref=%2F"
		result = self.post(
			login_url,
			data = payload,
			headers = dict(referer=login_url)
		)
		tree = html.fromstring(result.content)		
		self.user_id = tree.xpath('//a[@class="userphoto"]/@href')[0]
		result = self.get("https://naurunappula.com"+self.user_id)
		tree = html.fromstring(result.content)
		self.group_ids = list()
		self.group_names = list()
		for kanava in tree.xpath('//div[@class="grouplist"]/ul/li'):
			link = kanava.xpath('a/@href')[0]
			self.group_ids.append(re.search('\d+', link).group(0))
			self.group_names.append(kanava.xpath('a/text()')[0])
			
	def hae(self, url):
		return self.get(
			url,
			headers = dict(referer = url)
		)

mie = login()
		
class YTelement(youtube_dl.YoutubeDL):
	def __init__(self, url):
		options = {
			'format': '-f bestvideo[height<=480]+bestaudio/best[height<=480]',
			'simulate': 'true'
			}
		youtube_dl.YoutubeDL.__init__(self, options)
		with self:
			result = self.extract_info(
				'http:' + url,
				download=False # We just want to extract the info
			)
		if 'entries' in result:
			# Can be a playlist or a list of videos
			formats = result['entries'][0]['formats']
		else:
			# Just a video
			formats = result['formats']
		
		self.video = result['url']

class NNement(list):
	def __init__(self, page=1):
		self.url = 'http://naurunappula.com/videot'
		result = mie.hae(self.url+'/?p='+str(page))
#		result = requests.get(self.url)
		tree = html.fromstring(result.content)
		for element in tree.xpath('//table[@class="padd gridlist"]/tr/td/a'):
			self.append(VideoElement(element))
			
class Kommentti:
	def __init__(self, element):
		self.user = element.xpath('td[@class="author"]//b/text()')[0]
		self.user_data = " ".join(element.xpath('td[@class="author"]/div[@class="usergroup"]//text()')).strip()
		self.content = element.xpath('td[@class="content"]/div/text()')
		self.text = " ".join(self.content)

class VideoElement:
	def __init__(self, gridlist):
		self.title = gridlist.xpath('@title')[0]
		if self.title == "":
			self.name = "<Ei nimikettä>"
		else:
			self.name = gridlist.xpath('text()')[0]
		self.link = "https://naurunappula.com" + gridlist.xpath('@href')[0]
#		self.link_id = re.search('\d+', self.link).group(0)
		self.image = gridlist.xpath('img/@src')[0]
	
	def hae_video(self):
		result = mie.get(self.link)
		tree = html.fromstring(result.content)
		linkdata = tree.xpath('//div[@id="view_container"]/div[@id="linkdatacontainer"]/div[@id="linkdata"]')[0]

		self.link_id = tree.xpath('//input[@name="link_id"]/@value')[0]
		self.rating = linkdata.xpath('h1/span[@id="ratevalue"]/text()')
		if len(self.rating)!=0:
			self.rating = self.rating[0].strip()
		else:
			self.rating = "<et ole kirjautunut>"
		self.katsottu = linkdata.xpath('div[@id="linktoolstable"]//p/b/text()')[0]
		self.user = linkdata.xpath('div[@id="linktoolstable"]//a/b/text()')
		if len(self.user)!=0:
			self.user = self.user[0]
			i=2
		else:
			self.user = "anon"
			i=1 #jos anon niin yksi rivi puuttuu alusta
		self.date = linkdata.xpath('div[@id="linktoolstable"]//div[@id="linkinfo"]/p/text()')[i].strip()
		self.date = re.search('\d+[.]\d+[.]\d+', self.date).group(0) #haetaan vain päivänmäärä

		embedded = tree.xpath('//div[@id="viewbody_container"]/div[@id="viewbody"]/div[@id="viewembedded"]')[0]
		youtube = embedded.xpath('iframe/@src')
		flv = embedded.xpath('script/text()')

		if len(flv) != 0:
			self.url = re.search('https:.+[.]flv', flv[0]).group(0) #HUOM! jos logattuna niin https, muuten http
		else:
			ydl = YTelement(youtube[0])
			self.url = ydl.video
	
	def hae_sessio(self, sessio):
		tree = html.fromstring(sessio.content)
		self.title = tree.xpath('//div[@id="view_container"]/div[@id="linkdatacontainer"]/div[@id="linkdata"]/h1/span[@id="linktitle"]/text()')
		if len(self.title)!=0:
			self.title = self.title[0]
		else:
			self.title = "<Ei nimikettä>"
		self.link = sessio.url
		self.hae_video()
		self.hae_kommentit()
	
	def hae_rating(self):
		result = mie.hae(self.link)
		tree = html.fromstring(result.content)
		linkdata = tree.xpath('//div[@id="view_container"]/div[@id="linkdatacontainer"]/div[@id="linkdata"]')[0]
		self.rating = linkdata.xpath('h1/span[@id="ratevalue"]/text()')[0].strip()
		
	def hae_kommentit(self):
		result = mie.get(self.link)
		tree = html.fromstring(result.content)
		self.comments = list()
		for kommentti in tree.xpath('//div[@id="list_comments"]/table/tr')[::2]:
			self.comments.append(Kommentti(kommentti))
		
	def rate_video(self, rating):
		payload={
			'service_id':'1',
			'target_id':self.link_id,
			'points':rating
			}
		mie.post("https://naurunappula.com/rate.php", payload)
		
	def add_channel(self, kanava):
		payload={
			'link_id':self.link_id,
			'group_id':kanava
			}
		mie.post("https://naurunappula.com/favadd.php", payload)


