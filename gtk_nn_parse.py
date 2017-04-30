#!/usr/bin/env python3

import math
import threading
import requests
import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk,Gdk,GdkPixbuf,GObject
from os.path import isfile, getsize
from nn_parse import VideoGrid,mie,VideoPage,ImageGrid
from gtk_vlc_player import DecoratedVLCWidget

class Kuva(threading.Thread, Gtk.Box):
	__gsignals__ = {
			'downloaded':(GObject.SIGNAL_RUN_FIRST, None, ())
		}
	
	folder = None
	size = None

	def __init__(self, url):
		threading.Thread.__init__(self)
		Gtk.Box.__init__(self)
		self.set_size_request(self.size,self.size)
		self.spinner = Gtk.Spinner()
		self.spinner.start()
		self.pack_start(self.spinner, True, True, 0)
		self.url = url
		self.imgname = re.search('\d+[.]jpg', url)
		
	def run(self):
		self.local_file = open(self.folder+self.imgname, 'wb')
		response=requests.get(self.url, stream=True)
		for chunk in response.iter_content(100000):
			self.local_file.write(chunk)
		self.emit('downloaded')

	def get_file(self):
		return self.folder + self.imgname
		
	def write_file(self):
		if not isfile(self.folder+self.imgname):		
			self.start()
		elif not getsize(self.folder+self.imgname):
			self.start()
		else:
			self.emit('downloaded')
			
	def do_downloaded(self):
		image = Gtk.Image()
		imgbuffer = GdkPixbuf.Pixbuf.new_from_file(self.get_file())
		imgbuffer = imgbuffer.scale_simple(self.size,self.size,GdkPixbuf.InterpType.BILINEAR)
		image.set_from_pixbuf(imgbuffer)
		self.remove(self.spinner)
		self.pack_start(image, True, True, 0)
		self.queue_draw()
		self.show_all()
		
class Avatar(Kuva):
	folder = "./avatars/"
	size = 50
	
	def __init__(self, url):
		Kuva.__init__(self, url)
		if self.imgname == None:
			self.imgname="no-photo-mini.gif"
		else:
			self.imgname=self.imgname.group(0)
		self.write_file()

class Thumbnail(Kuva):
	folder = "./thumbnails/"
	size = 100
	
	def __init__(self, url):
		Kuva.__init__(self, url)
		if self.imgname == None:
			self.imgname="video.gif"
		else:
			self.imgname=self.imgname.group(0)
		self.write_file()

class Kanavavalikko(Gtk.ComboBoxText):
	def __init__(self):
		Gtk.ComboBoxText.__init__(self)
		for nimi in mie.group_names:
			self.append(None, nimi)
		
	def add_to(self):
		return mie.group_ids[self.get_active()]
		
class KommenttiLaatikko(Gtk.ListBoxRow):
	def __init__(self, kommentti):
		Gtk.ListBoxRow.__init__(self)
		builder = Gtk.Builder()
		builder.add_from_file("KommenttiLaatikko.glade")
		user_thumbnail = builder.get_object("user_thumbnail")
		user_thumbnail.set_from_file(Avatar(kommentti.user.avatar).get_file())
		user_name = builder.get_object("user_name")
		user_name.set_label("<"+kommentti.user.name+">")
		user_data = builder.get_object("user_data")
		user_data.set_label(kommentti.user.comment_data)
		comment = builder.get_object("comment")
		comment.get_buffer().set_text(kommentti.text)
		self.add(builder.get_object("comment_box"))

class VLCWindow(Gtk.Window):
	def __init__(self, olio):
		Gtk.Window.__init__(self, title="VLC")
		
		self.data = olio
		self.connect("key_press_event", self.key_pressed)
		self.draw_area = DecoratedVLCWidget()
		self.draw_area.set_media(olio.url)
		self.draw_area.player.play()

		builder = Gtk.Builder()
		builder.add_from_file("VideoIkkuna.glade")
		builder.connect_signals(self)
		self.add(builder.get_object("video_window"))

		self.title = builder.get_object("title")
		self.user = builder.get_object("user")
		self.date = builder.get_object("date")
		self.times_watched = builder.get_object("times_watched")
		self.rating = builder.get_object("rating")

		channel_select = builder.get_object("channel_select")
		self.valikko = Kanavavalikko()
		channel_select.add(self.valikko)

		self.channels_list = builder.get_object("channels_list")

		self.tags_list = builder.get_object("tags_list")
		self.tag_input = builder.get_object("tag_input")

		video_area = builder.get_object("video_area")
		video_area.pack_start(self.draw_area, True, True, 0)
		
#		comments_window = builder.get_object("comments_window")
#		comments_window.set_max_content_height(200) #vaatii GTK version 3.22
		self.comments_list = builder.get_object("comments")
		self.comment_input = builder.get_object("comment_input")
		
		self.fill_lists()

	def fill_lists(self):
		self.title.set_label(self.data.title)
		self.user.set_label("<" + self.data.user + "> ")
		self.date.set_label(self.data.date)
		self.times_watched.set_label("Katsottu: " + self.data.katsottu + " kertaa")
		self.rating.set_label(self.data.rating)
		self.kanavat = Gtk.VBox()
		for kanava in self.data.channels:
			self.kanavat.pack_start(Gtk.Label(kanava), False, False, 0)
		self.channels_list.add(self.kanavat) 
		self.tagit = Gtk.VBox()
		for tagi in self.data.tags:
			self.tagit.pack_start(Gtk.Label(tagi), False, False, 0)
		self.tags_list.add(self.tagit)
		self.kommentit = Gtk.ListBox()
		for kommentti in self.data.comments:
			self.kommentit.add(KommenttiLaatikko(kommentti))
		self.comments_list.add(self.kommentit)
		
	def empty_lists(self):
		self.channels_list.remove(self.kanavat)
		self.tags_list.remove(self.tagit)
		self.comments_list.remove(self.kommentit)

	def do_rating(self, widget):
		self.data.rate(widget.get_label())
		self.data.hae_rating()
		self.rating.set_label(self.data.rating)
		
	def add_comment(self, widget):
		text = self.comment_input.get_text(self.comment_input.get_start_iter(), self.comment_input.get_end_iter(), False)
		self.data.add_comment(text)
		self.data.hae_kommentit()
		self.comments_list.remove(self.kommentit)
		self.kommentit = Gtk.ListBox()
		for kommentti in self.data.comments:
			self.kommentit.pack_start(KommenttiLaatikko(kommentti), False, False, 0)
		self.comments_list.add(self.kommentit)
		self.queue_draw()
		self.show_all()		

	def add_channel(self, widget):
		kanava_id = self.valikko.add_to()
		self.data.add_channel(kanava_id)
		self.data.hae_kanavat()
		self.channels_list.remove(self.kanavat)
		self.kanavat = Gtk.VBox()
		for kanava in self.data.channels:
			self.kanavat.pack_start(Gtk.Label(kanava), False, False, 0)
		self.channels_list.add(self.kanavat) 
		self.queue_draw()
		self.show_all()
		
	def add_tag(self, widget):
		tag = self.tag_input.get_text()
		self.data.add_tag(tag)

	def key_pressed(self, widget, event):
		key_method = {
			Gdk.KEY_Left: "back",
			Gdk.KEY_Right: "next",
			}
		method_name = key_method.get(event.keyval)
		method = getattr(self, method_name)
		method()
		
	def back(self, *widget):
		self.change_video("n")
		
	def next(self, *widget):
		self.change_video("p")
		
	def change_video(self, direction):
		self.data = VideoPage(self.data.change_media(direction))
		self.draw_area.player.stop()
		self.draw_area.player.set_mrl(self.data.url)
		self.draw_area.player.play()
		self.empty_lists()
		self.fill_lists()
		self.queue_draw()
		self.show_all()

class Nappi(Gtk.Button):
	def __init__(self, olio):
		Gtk.Button.__init__(self)
		threading.Thread.__init__(self)
		self.Mnemonic = olio
		jako = Gtk.VBox()
		jako.add(Thumbnail(olio.thumbnail))
		label = Gtk.Label(olio.name)
		jako.add(label)
		self.add(jako)
		self.connect("clicked", self.on_button_clicked)
		self.set_size_request(210,150)
		
	def on_button_clicked(self, widget):
		session = mie.get(widget.Mnemonic.link)
		window = VLCWindow(VideoPage(session))
		window.show_all()
		
class Ristikko(Gtk.Grid):
	def __init__(self, page=1):
		Gtk.Grid.__init__(self)
		NN = VideoGrid(page)

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
	
	def on_button_clicked(self, widget):
		self.page += widget.Mnemonic
		self.jako.remove(self.grid)
		self.grid = Ristikko(self.page)
		self.jako.pack_start(self.grid, True, True, 0)
		self.queue_draw()
		self.show_all()

win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
