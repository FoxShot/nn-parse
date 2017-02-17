 #!python3

from lxml import html
import requests
import re
import math
import urllib
import vlc
from os.path import expanduser
home = expanduser("~")	#multi os support
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf
import os
import configparser
#import mpv
#from mpv import MPV
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
#import subprocess
import youtube_dl


class VLCWidget(Gtk.DrawingArea):
	"""Simple VLC widget.

	Its player can be controlled through the 'player' attribute, which
	is a vlc.MediaPlayer() instance.
	"""
	def __init__(self, *p):
		Gtk.DrawingArea.__init__(self)
#		self.instance = vlc.Instance('--verbose 2'.split())
		self.instance = vlc.Instance('--no-xlib')
		self.player = self.instance.media_player_new()
		self.set_size_request(640, 480)
#		self.connect("destroy", lambda b: self.player.stop())

	def seis(self):
		getattr(self.player, "stop")()
		self.player.stop()
		self.instance.release()
	
class VLCWindow(Gtk.Window):
	def __init__(self, video_url):
		Gtk.Window.__init__(self, title="VLC")
		self.draw_area = VLCWidget()
		self.draw_area.connect("realize",self._realized)
		
		self.vbox = Gtk.VBox()
		self.add(self.vbox)
		self.vbox.pack_start(self.draw_area, True, True, 0)

#		result = requests.get(video_url)
		mie = login()
		result = mie.hae(video_url)
		tree = html.fromstring(result.content)
		linkdata = tree.xpath('//div[@id="view_container"]/div[@id="linkdatacontainer"]/div[@id="linkdata"]')[0]
		rating = linkdata.xpath('h1/span[@id="ratevalue"]/text()')
		if len(rating)!=0:
			rating = rating[0]
		else:
			rating = "<et ole kirjautunut>"
		nimike = linkdata.xpath('h1/span[@id="linktitle"]/text()')[0]
		katsottu = linkdata.xpath('div[@id="linktoolstable"]//p/b/text()')[0]

		label = Gtk.Label(nimike + " " + rating)
		self.vbox.add(label)

		label = Gtk.Label("Katsottu: " + katsottu + " kertaa")
		self.vbox.add(label)

		self.connect("destroy", self.close)
		
	def _realized(self, widget):
		win_id = widget.get_window().get_xid()
		self.draw_area.player.set_xwindow(win_id)

	def close(self, widget):
		self.draw_area.seis()

	def display(self, video_url):
		result = requests.get(video_url)
		tree = html.fromstring(result.content)
		embedded = tree.xpath('//div[@id="viewbody_container"]/div[@id="viewbody"]/div[@id="viewembedded"]')[0]
		youtube = embedded.xpath('iframe/@src')
		flv = embedded.xpath('script/text()')

		if len(flv) != 0:
			url = re.search('https:.+[.]flv', flv[0]).group(0) #HUOM! jos logattuna niin https, muuten http
		else:
			ydl = YTelement(youtube[0])
			url = ydl.video

		self.draw_area.player.set_mrl(url)
		self.draw_area.player.play()

		
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

class Thumbnail(Gtk.Image):
	def __init__(self, url):
		Gtk.Image.__init__(self)

		youtube="https://sgooby.naurunappula.com/images/icons/youtube.gif" #https ja sgooby?
		video="https://sgooby.naurunappula.com/images/icons/video.gif" #https ja sgooby?
		if url == youtube:
			imgname="youtube.gif"
		elif url == video:
			imgname="video.gif"
		else:
			imgname=re.search('\d+[.]jpg', url).group(0)
									
		if not os.path.isfile("./icons/"+imgname):				
			response=urllib.request.urlopen(url)
			with open("./icons/"+imgname, 'wb') as img:
				img.write(response.read())

		pb = Pixbuf.new_from_file("./icons/"+imgname)
		self.set_from_pixbuf(pb)

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
	
	def hae(self, url):
		return self.get(
			url,
			headers = dict(referer = url)
		)

class NNement(list):
	def __init__(self, page=1):
		self.url = 'http://naurunappula.com/videot'
		mie = login()
		result = mie.hae(self.url+'/?p='+str(page))
#		result = requests.get(self.url)
		tree = html.fromstring(result.content)
		for element in tree.xpath('//table[@class="padd gridlist"]/tr/td/a'):
			self.append(sadf(element))

class sadf:
	def __init__(self, NNement):
		self.title = NNement.xpath('@title')[0]
		if self.title == "":
			self.name = "<Ei nimikettä>"
		else:
			self.name = NNement.xpath('text()')[0]
		self.link = NNement.xpath('@href')[0]
		self.image = NNement.xpath('img/@src')[0]

class nappi(Gtk.Button):
	def __init__(self, olio):
		Gtk.Button.__init__(self)
		self.Mnemonic = "https://naurunappula.com" + olio.link #https?
		jako = Gtk.VBox()
		kuva = Thumbnail(olio.image)
		jako.add(kuva)
		label = Gtk.Label(olio.name)
		jako.add(label)
		self.add(jako)
		self.connect("clicked", self.on_button_clicked)

	def on_button_clicked(self, widget):
		window = VLCWindow(widget.Mnemonic)
		window.show_all()
		window.display(widget.Mnemonic)

class Ristikko(Gtk.Grid):
	def __init__(self, page=1):
		Gtk.Grid.__init__(self)
		NN = NNement(page)

		i=0
		for vid in NN:
			laatikko = nappi(vid)
			self.attach(laatikko,(i%5)+1,math.floor(i/5)+1,1,1)
			i+=1

class MyWindow(Gtk.Window):
	def __init__(self):
		Gtk.Window.__init__(self, title="nn-parse")

		self.jako = Gtk.VBox()
		self.add(self.jako)
		
		self.page=1
		
		toolbar = Gtk.Toolbar()
		self.jako.pack_start(toolbar, True, True, 0)
		
		b = Gtk.ToolButton(Gtk.STOCK_GO_BACK)
		b.Mnemonic = -1
		b.connect("clicked", self.on_button_clicked)
		toolbar.insert(b, -1)
		
		b = Gtk.ToolButton(Gtk.STOCK_GO_FORWARD)
		b.Mnemonic = 1
		b.connect("clicked", self.on_button_clicked)
		toolbar.insert(b, -1)
		
		b = Gtk.ToolButton(Gtk.STOCK_REFRESH)
		b.Mnemonic = 0
		b.connect("clicked", self.on_button_clicked)
		toolbar.insert(b, -1)

		self.grid = Ristikko()
		self.jako.pack_start(self.grid, True, True, 0)
	
#		self.player = mpv.MPV(ytdl=True)

	def on_button_clicked(self, widget):
		self.page += widget.Mnemonic
		self.jako.remove(self.grid)
		self.grid = Ristikko(self.page)
		self.jako.pack_start(self.grid, True, True, 0)
		self.queue_draw()
		self.show_all()		#tämä oli tärkeä
	

win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
