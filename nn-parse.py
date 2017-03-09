 #!python3

from lxml import html
import requests
import re
import math
import urllib
import vlc
from os.path import expanduser
home = expanduser("~")	#multi os support
from gi.repository import Gtk,Gdk,GObject
from gi.repository.GdkPixbuf import Pixbuf
import os
import configparser
#import mpv
#from mpv import MPV
import gi
gi.require_version('Gtk', '3.0')
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
	
	def hae(self, url):
		return self.get(
			url,
			headers = dict(referer = url)
		)

mie = login()

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
		
class DataBox(Gtk.VBox):
	def __init__(self, olio):	
		Gtk.VBox.__init__(self)
		
		label = Gtk.Label(olio.title)
		self.add(label)

		rate_box = Gtk.Box()
		rate_box.set_homogeneous(True)
		self.rating = Gtk.Label(olio.rating)
		rate_box.add(self.rating)
		for rating in ('+2','+1','-1'):
			painike = Gtk.Button()
			painike.Mnemonic = rating
			painike.add(Gtk.Label(rating))
			painike.connect('clicked', self.on_button_clicked)
			rate_box.add(painike)
		self.add(rate_box)

		self.data = olio

		label = Gtk.Label("<" + olio.user + "> " + olio.date +" Katsottu: " + olio.katsottu + " kertaa")
		self.add(label)
	
	def on_button_clicked(self, widget):
		self.data.rate_video(widget.Mnemonic)
		self.data.hae_rating()
		self.rating.set_label(self.data.rating)
		
class Seekbar(Gtk.HScale):
	def __init__(self, VLCWidget):
		Gtk.HScale.__init__(self)
		self.player = VLCWidget
		self.connect("change-value", self.set_time)
		self.set_range(0,1)
		self.set_digits(5)
		self.set_draw_value(False)
		GObject.timeout_add(200, self.timeout)
		self.connect("destroy", self.close)
		self.timer_on = True
		
	def close():
		self.timer_on = False

	def timeout(self):
		self.set_value(self.player.get_position())
		return self.timer_on
		
	def set_length(self):
		print(self.player.get_length())
		self.set_range(0,1)
		
	def set_time(self, widget, scroll, value):
		if scroll == Gtk.ScrollType.JUMP:
			self.player.set_position(value)

		
class VLCWindow(Gtk.Window):
	def __init__(self, olio):
		Gtk.Window.__init__(self, title="VLC")
		
		self.vbox = Gtk.VBox()
		self.add(self.vbox)

		toolbar = Gtk.Toolbar()
		for icon, direction in (
			((Gtk.STOCK_GO_BACK), ('n')),
			((Gtk.STOCK_GO_FORWARD), ('p')),
#			((Gtk.STOCK_REFRESH), (''))
			):
			b = Gtk.ToolButton(icon)
			b.Mnemonic = direction
			b.connect("clicked", self.change_video)
			toolbar.insert(b, -1)
		self.vbox.add(toolbar)
		
		self.draw_area = VLCWidget()
		self.draw_area.connect("realize",self._realized)
		self.vbox.add(self.draw_area)

		olio.hae_video()
		self.data = olio

		self.draw_area.player.set_mrl(olio.url)
		
		haku = Seekbar(self.draw_area.player)
		self.vbox.add(haku)

		self.tiedot = DataBox(olio)
		self.vbox.add(self.tiedot)
		self.connect("destroy", self.close)
		self.connect("key_press_event", self.key_pressed)
		
	def _realized(self, widget):
		win_id = widget.get_window().get_xid()
		self.draw_area.player.set_xwindow(win_id)
		self.draw_area.player.play()

	def close(self, widget):
		self.draw_area.seis()
		
	def key_pressed(self, widget, event):
		key_method = {
			Gdk.KEY_Left: "back",
			Gdk.KEY_Right: "next",
			}
		method_name = key_method.get(event.keyval)
		method = getattr(self, method_name)
		method()
		
	def back(self):
		self.change_video("n")
		
	def next(self):
		self.change_video("p")
		
	def toolbar_direction(self, widget):
		self.change_video(widget.Mnemonic)

	def change_video(self, direction):
#		url = "https://naurunappula.com/go.php"
#		payload = {
#			'link_id': self.data.link_id,
#			'c': '2',
#			'dir': widget.Mnemonic
#		}
#		result = mie.put(
#			url,
#			data = payload,
#			headers = dict(referer=url)
#		)
#		print(result.text)
		sessio = mie.get("https://naurunappula.com/go.php?link_id="+self.data.link_id+"&c=2&dir="+direction)
		self.data.hae_sessio(sessio)
		self.draw_area.player.stop()
		self.draw_area.player.set_mrl(self.data.url)
		self.draw_area.player.play()
		self.vbox.remove(self.tiedot)
		self.tiedot = DataBox(self.data)
		self.vbox.add(self.tiedot)
		self.queue_draw()
		self.show_all()
		
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

class NNement(list):
	def __init__(self, page=1):
		self.url = 'http://naurunappula.com/videot'
		result = mie.hae(self.url+'/?p='+str(page))
#		result = requests.get(self.url)
		tree = html.fromstring(result.content)
		for element in tree.xpath('//table[@class="padd gridlist"]/tr/td/a'):
			self.append(VideoElement(element))

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
			self.rating = self.rating[0]
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
	
	def hae_rating(self):
		result = mie.hae(self.link)
		tree = html.fromstring(result.content)
		linkdata = tree.xpath('//div[@id="view_container"]/div[@id="linkdatacontainer"]/div[@id="linkdata"]')[0]
		self.rating = linkdata.xpath('h1/span[@id="ratevalue"]/text()')[0]	
			
	def rate_video(self, rating):
		payload={
			'service_id':'1',
			'target_id':self.link_id,
			'points':rating
			}
			
		mie.post("https://naurunappula.com/rate.php", payload)

class Nappi(Gtk.Button):
	def __init__(self, olio):
		Gtk.Button.__init__(self)
		self.Mnemonic = olio
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

class Ristikko(Gtk.Grid):
	def __init__(self, page=1):
		Gtk.Grid.__init__(self)
		NN = NNement(page)

		i=0
		for vid in NN:
			laatikko = Nappi(vid)
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
		
		for icon, direction in (
			((Gtk.STOCK_GO_BACK), (-1)),
			((Gtk.STOCK_GO_FORWARD), (1)),
			((Gtk.STOCK_REFRESH), (0))
			):
			b = Gtk.ToolButton(icon)
			b.Mnemonic = direction
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
