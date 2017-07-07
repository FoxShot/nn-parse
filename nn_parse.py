#!/usr/bin/env python3

from lxml import html
import requests
import re
from os.path import expanduser
home = expanduser("~")	#multi os support
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
			
mie = login()

class User:
	def __init__(self, user_id):
		self.id = user_id
#		self.name = 
#		self.avatar
		
	def peek(self):
		payload = {
#			'href':'/u/'+self.id,
			'type':'user',
			'target':'70329'
		}
#		result = mie.post("https://narunappula.com/peek.php", data=payload)
#		result = requests.post(
#			'http://naurunappula.com/peek.php',
#			data='type=user&target=26515',
#			headers={'content-type': 'text/plain'}
#			)
		result = requests.get('http://naurunappula.com/peek.php', params=payload)
#		user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'
#		headers = {'User-Agent': user_agent}
#		result = mie.get("https://naurunappula.com/peek.php?type=username&target=/u/70329/", headers=headers)
#		result = requests.get("http://naununappula.com/")
		print(result.headers['content-length'])
#		print(BytesIO(result.content).readlines())
#		for line in result.iter_lines(decode_unicode=True):
#			print("yks")
		
	def add_friend(self):
		self.set_friend('add')
		
	def remove_friend(self):
		self.set_friend('delete')
		
	def set_friend(self, operation):
		payload = {
			operation: self.id
		}
		mie.post("https://naurunappula.com/f.php", payload)
		
class Comment_user(User):
	def __init__(self, comment_box):
		user_id = comment_box.xpath('td[@class="author"]/div[@class="username"]/a/@href')[0]
		User.__init__(self, user_id)
		avatar_url = comment_box.xpath('td[@class="author_photo"]//img/@src')[0]
		self.avatar = avatar_url
		self.name = comment_box.xpath('td[@class="author"]//b/text()')[0]
		self.comment_data = " ".join(comment_box.xpath('td[@class="author"]/div[@class="usergroup"]//text()')).strip()
		
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
		self.video = result['url']

class Grid(list):
	media_url = None
	
	def __init__(self, page=1):
		result = mie.get(self.media_url+'/?p='+str(page))
		tree = html.fromstring(result.content)
		for element in tree.xpath('//table[@class="padd gridlist"]/tr/td/a'):
			self.append(VideoElement(element))

class VideoGrid(Grid):
	media_url = 'https://naurunappula.com/videot'
	
	def __init__(self, page=1):
		Grid.__init__(self, page)
		
class ImageGrid(Grid):
	media_url = 'https://naurunappula.com/kuvat'
	
	def __init__(self, page=1):
		Grid.__init__(self, page)
		
class GroupGrid(list):
	def __init__(self, media_url ,page=1):
		result = mie.get(media_url+'/?page_id='+str(page))
		tree = html.fromstring(result.content)
		for element in tree.xpath('//table[@class="padd gridlist groupmedias"]/tr/td/a'):
			self.append(VideoElement(element))		
			
class Kommentti:
	def __init__(self, element):
		self.user = Comment_user(element)
		self.content = element.xpath('td[@class="content"]/div/text()')
		self.quote = " ".join(element.xpath('td[@class="content"]//div[@class="quote_msg"]/text()')).strip()
		self.quote_user = " ".join(element.xpath('td[@class="content"]//div[@class="quote_msg"]/a/text()')).strip()
		self.text = self.quote_user + " " + self.quote + " ".join(self.content)
		
class Kommentti_sent:
	def __init__(self, data, kommentti):
		self.comment_media = "".join(data.xpath('a//text()')).strip()
		self.comment_date = data.xpath('span/text()')
		self.comment_id = re.search("\d+","".join(kommentti.xpath('@id'))).group(0)
		self.content = " ".join(kommentti.xpath('text()')).strip()
#		payload={
#			'action':'get_message',
#			'msg_id':self.comment_id
#			}
#		message = mie.post("https://naurunappula.com/comment.php", payload)

	def hae_tiedot(self):
		payload={
			'from_viewmode':'1',
			'service_id':'1',
			'target_id':self.comment_media,
			'page_id':'-1',	#näytä kaikki
			'action':'fetch'
			}
		result = mie.post("https://naurunappula.com/comment.php", payload)
		tree = html.fromstring(result.text)
		self.comment_rating = "".join(tree.xpath('//span[@id="crate_' + self.comment_id + '"]/text()')).strip()

class User_comments(list):
	def __init__(self):
		result = mie.get("https://naurunappula.com" + mie.user_id + "?c=1000")
		tree = html.fromstring(result.content)
		elements = tree.xpath('//div[@class="sent_comments"]/div')
		for data, kommentti in zip(elements[0::2], elements[1::2]):
			self.append(Kommentti_sent(data, kommentti))
			
class Media:
	cathegory=None
	
	def __init__(self, media_id):
		self.id = media_id
		self.link = "https://naurunappula.com/" + self.id
		
	def hae_rating(self):
		result = mie.get(self.link)
		tree = html.fromstring(result.content)
		linkdata = tree.xpath('//div[@id="view_container"]/div[@id="linkdatacontainer"]/div[@id="linkdata"]')[0]
		rating = linkdata.xpath('h1/span[@id="ratevalue"]/text()')[0].strip()
		return rating
		
	def hae_kommentit(self):
		payload={
			'from_viewmode':'1',
			'service_id':'1',
			'target_id':self.id,
			'page_id':'-1',	#näytä kaikki
			'action':'fetch'
			}
		result = mie.post("https://naurunappula.com/comment.php", payload)
		tree = html.fromstring(result.text)
		comments = list()
		for kommentti in tree.xpath('//div[@id="list_comments"]/table/tr')[::2]:
			comments.append(Kommentti(kommentti))
		return comments

	def hae_kanavat(self):
		result = mie.get(self.link)
		tree = html.fromstring(result.content)
		channels = tree.xpath('//div[@id="linkinfo"]/p/a[starts-with(@href, "/g/")]/text()')
		return channels

	def hae_tagit(self):
		result = mie.get(self.link)
		tree = html.fromstring(result.content)
		tags = tree.xpath('//div[@id="linkinfo"]/p/a[starts-with(@href, "/s/")]/text()')
		return tags

	def rate(self, rating):
		payload={
			'service_id':'1',
			'target_id':self.id,
			'points':rating
			}
		mie.post("https://naurunappula.com/rate.php", payload)

	def add_channel(self, kanava):
		payload={
			'link_id':self.id,
			'group_id':kanava
			}
		mie.post("https://naurunappula.com/favadd.php", payload)

	def add_tag(self, tag):
		payload={
			'link_id':self.id,
			'inlinetagsuggestion':1,
			'suggest_tag':tag
			}
		mie.post("https://naurunappula.com/editor.php", payload)

	def add_comment(self, comment):
		payload={
			'action':'send_comment',
			'service_id':'1',
			'target_id':self.id,
			'comment':comment
			}
		mie.post("https://naurunappula.com/comment.php", payload)

	def change_media(self, direction):
		url = "https://naurunappula.com/go.php"
		payload = {
			'link_id':self.id,
			'c':self.cathegory,
			'dir':direction
		}
		return mie.get(url, params=payload)

class VideoElement(Media):
	def __init__(self, gridlist):
		self.title = gridlist.xpath('@title')[0]
		if self.title == "":
			self.name = "<Ei nimikettä>"
		else:
			self.name = gridlist.xpath('text()')[0]
		self.link = "https://naurunappula.com" + gridlist.xpath('@href')[0]
		media_id = re.search('\/(\d+)\/', self.link).group(1)
		thumbnail_url = gridlist.xpath('img/@src')[0]
		self.thumbnail = thumbnail_url
		Media.__init__(self, media_id)

class MediaPage(Media):
	embedded_pattern = None
	test = [ 'script/text()',
		'video/source/@src',
		'iframe/@src'
		]
	
	def __init__(self,session):
		self.html_tree = html.fromstring(session.content)
		media_id = self.html_tree.xpath('//input[@name="link_id"]/@value')[0]

		Media.__init__(self, media_id)

		linkdata = self.html_tree.xpath('//div[@id="view_container"]/div[@id="linkdatacontainer"]/div[@id="linkdata"]')[0]

		self.title = linkdata.xpath('h1/span[@id="linktitle"]/text()')
		if len(self.title)!=0:
			self.title = self.title[0]
		else:
			self.title = "<Ei nimikettä>"
		self.link = session.url

		self.rating = linkdata.xpath('h1/span[@id="ratevalue"]/text()') #hae_rating
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
		self.tags = linkdata.xpath('//div[@id="linkinfo"]/p/a[starts-with(@href, "/s/")]/text()')
		self.channels = linkdata.xpath('//div[@id="linkinfo"]/p/a[starts-with(@href, "/g/")]/text()')
		self.comments = self.hae_kommentit()
		
#		img = embedded.xpath('script/text()')
#		webm = embedded.xpath('video/source/@src')
#		youtube = embedded.xpath('iframe/@src')
#		flv = embedded.xpath('script/text()')

#		if len(img) != 0:
#			self.url = "https://babylon.naurunappula.com" + re.search('\/screen\/.+[.jpg|.png]', img[0]).group(0)
#			print("img")	
#		elif len(webm) != 0:
#			self.url = webm[0]
#			print("webm")
#		elif len(flv) != 0:
#			self.url = re.search('https:.+[.]flv', flv[0]).group(0) #HUOM! jos logattuna niin https, muuten http
#			print("flv")
#		else:
#			ydl = YTelement(youtube[0])
#			self.url = ydl.video
#			print("ydl")

		self.url = self.tunnista_tyyppi() #käytetään alaluokan metodia jos on
	
	def tunnista_tyyppi(self):
		embedded = self.html_tree.xpath(self.embedded_pattern)[0]
		for index, format_pattern in enumerate(self.test):
			format_element = embedded.xpath(format_pattern)
			if len(format_element) != 0:
				return self.toiminta(index, format_element)
		return None
	
	def toiminta(self, index, element):
		if index!=0:
			return element
		else:
			return None
						
	def hae_rating(self):
		self.rating = super().hae_rating()
		return self.rating

	def hae_kommentit(self):
		self.kommentit = super().hae_kommentit()
		return self.kommentit

	def hae_kanavat(self):
		self.channels = super().hae_kanavat()
		return self.channels	
	
class VideoPage(MediaPage):
	cathegory = '2'
	embedded_pattern = '//div[@id="viewbody_container"]/div[@id="viewbody"]/div[@id="viewembedded"]'
	test = [ 'iframe/@src',
		'video/source/@src'
		]

	def __init__(self, session):
		MediaPage.__init__(self, session)

	def toiminta(self, index, element):
		if index == 0:
			ydl = YTelement(element[0])
			return ydl.video
		elif index == 1:
			return re.search('https:.+[.]flv', element[0]).group(0) #HUOM! jos logattuna niin https, muuten http
		else:
			return None
		
class ImagePage(MediaPage):
	cathegory = '1'
	embedded_pattern = '//div[@id="viewbody_container"]/div[@id="viewbody"]//div[@id="viewembedded"]'
	test = [ 'script/text()',
		'video/source/@src'
		]
	
	def __init__(self, session):
		MediaPage.__init__(self, session)

	def toiminta(self, index, element):
		if index == 0:
			return "https://babylon.naurunappula.com" + re.search('\/screen\/.+[.jpg|.png|.gif]', element[0]).group(0)
		elif index == 1:
			return element[0]
		else:
			return None
