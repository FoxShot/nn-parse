#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk,Gdk,GObject
from gi.repository.GdkPixbuf import Pixbuf
import vlc
from nn_parse import *
from gtk_vlc_player import *

class Kanavavalikko(Gtk.ComboBoxText):
	def __init__(self, olio):
		Gtk.ComboBox.__init__(self)
		for nimi in mie.group_names:
			self.append(None, nimi)
		self.connect("changed", self.add_to)
		self.olio = olio
		
	def add_to(self, widget):
		gid = mie.group_ids[self.get_active()]
		self.olio.add_channel(gid)

class KommenttiLaatikko(Gtk.ListBoxRow):
	def __init__(self, kommentti):
		Gtk.ListBoxRow.__init__(self)
		builder = Gtk.Builder()
		builder.add_from_file("KommenttiLaatikko.glade")
		user_name = builder.get_object("user_name")
		user_name.set_label("<"+kommentti.user+">")
		user_data = builder.get_object("user_data")
		user_data.set_label(kommentti.user_data)
		comment = builder.get_object("comment")
		comment.get_buffer().set_text(kommentti.text)
		self.add(builder.get_object("comment_box"))

class DataBox(Gtk.VBox):
	def __init__(self, olio):	
		Gtk.VBox.__init__(self)
		
		builder = Gtk.Builder()
		builder.add_from_file("DataLaatikko.glade")
		builder.connect_signals(self)
		title = builder.get_object("title")
		title.set_label(olio.title)
		send_data = builder.get_object("send_data")
		send_data.set_label("<" + olio.user + "> " + olio.date +" Katsottu: " + olio.katsottu + " kertaa")
		self.rating = builder.get_object("rating")
		self.rating.set_label(olio.rating)
#		self = builder.get_object("data_box")
		self.add(builder.get_object("data_box"))
		
		kommentit = Gtk.ListBox()
		for kommentti in olio.comments:
			kommentit.add(KommenttiLaatikko(kommentti))
		self.add(kommentit)

		self.data = olio

	def on_button_clicked(self, widget):
		self.data.rate_video(widget.get_label())
		self.data.hae_rating()
		self.rating.set_label(self.data.rating)
		
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
		self.vbox.pack_start(toolbar, False, False, 0)
		
		self.draw_area = DecoratedVLCWidget()
		self.vbox.add(self.draw_area)

		olio.hae_video()
		olio.hae_kommentit()
		self.data = olio

		self.draw_area.player.set_mrl(olio.url)
		
		self.tiedot = DataBox(olio)
		self.vbox.pack_end(self.tiedot, False, False, 0)
		self.connect("key_press_event", self.key_pressed)
		
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
#			'dir': direction
#		}
#		result = mie.post(
#			url,
#			data = payload,
#			headers = dict(referer=url)
#		)
#		print(result.content)
		sessio = mie.get("https://naurunappula.com/go.php?link_id="+self.data.link_id+"&c=2&dir="+direction)
		self.data.hae_sessio(sessio)
		self.draw_area.player.stop()
		self.draw_area.player.set_mrl(self.data.url)
		self.draw_area.player.play()
		self.vbox.remove(self.tiedot)
		self.tiedot = DataBox(self.data)
		self.vbox.pack_end(self.tiedot, False, False, 0)
		self.queue_draw()
		self.show_all()

class Thumbnail(Gtk.Image):
	def __init__(self, url):
		Gtk.Image.__init__(self)
		
		imgname=re.search('\d+[.]jpg', url)

		if imgname == None:
			imgname="video.gif"
		else:
			imgname=imgname.group(0)
									
		if not os.path.isfile("./icons/"+imgname):				
			response=urllib.request.urlopen(url)
			with open("./icons/"+imgname, 'wb') as img:
				img.write(response.read())

		pb = Pixbuf.new_from_file("./icons/"+imgname)
		self.set_from_pixbuf(pb)

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
