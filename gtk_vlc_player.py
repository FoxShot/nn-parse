#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk,Gdk,GObject
import vlc

instance = vlc.Instance('--no-xlib')

class VLCWidget(Gtk.DrawingArea):
	"""Simple VLC widget.

	Its player can be controlled through the 'player' attribute, which
	is a vlc.MediaPlayer() instance.
	"""
	def __init__(self, *p):
		Gtk.DrawingArea.__init__(self)
		self.player = instance.media_player_new()
		self.set_size_request(640, 480)

		self.connect("destroy", self.close)
		self.connect("realize", self._realized)

	def _realized(self, widget):
		win_id = widget.get_window().get_xid()
		self.player.set_xwindow(win_id)
		self.player.play()

	def close(self, widget):
		self.player.stop()
		instance.release()
		
class DecoratedVLCWidget(Gtk.VBox):
	"""Decorated VLC widget.

	VLC widget decorated with a player control toolbar.

	Its player can be controlled through the 'player' attribute, which
	is a Player instance.
	"""
	def __init__(self, *p):
		Gtk.VBox.__init__(self)
		self._vlc_widget = VLCWidget(*p)
		self.player = self._vlc_widget.player
		self.pack_start(self._vlc_widget, True, True, 0)
		self._toolbar = self.get_player_control_toolbar()
		self.pack_start(self._toolbar, False, False, 0)
		self.connect("destroy", self.close)

	def get_player_control_toolbar(self):
		"""Return a player control toolbar
		"""
		builder = Gtk.Builder()
		builder.add_from_file("VideonHallinta.glade")
		builder.connect_signals(self)
		self.seekbar = builder.get_object("seekbar")
		self.seekbar.set_range(0,1)
		self.seekbar.set_digits(5)
		GObject.timeout_add(200, self.timeout)
		self.timer_on = True
		self.play = builder.get_object("play")
		self.play.set_label(Gtk.STOCK_MEDIA_PAUSE)
		self.is_playing = True
		return builder.get_object("controls")
		
	def play_pause(self, button):
		if self.is_playing:
			self.player.pause()
			self.is_playing = False
			button.set_label(Gtk.STOCK_MEDIA_PLAY)
		else:
			self.player.play()
			self.is_playing = True
			button.set_label(Gtk.STOCK_MEDIA_PAUSE)
		
	def timeout(self):
		if self.timer_on:
			self.seekbar.set_value(self._vlc_widget.player.get_position())
		return self.timer_on

	def set_time(self, widget, scroll, value):
		if scroll == Gtk.ScrollType.JUMP:
			self.player.set_position(value)
			
	def close(self, widget):
		self.timer_on = False

class VideoPlayer:
	"""Example simple video player.
	"""
	def __init__(self):
		self.vlc = DecoratedVLCWidget()

	def main(self, fname):
		self.vlc.player.set_media(instance.media_new(fname))
		w = Gtk.Window()
		w.add(self.vlc)
		w.show_all()
		self.vlc.player.play()
		w.connect("destroy", Gtk.main_quit)
		Gtk.main()
		
if __name__ == '__main__':
	if not sys.argv[1:]:
		print('You must provide at least 1 movie filename')
		sys.exit(1)
	if len(sys.argv[1:]) == 1:
		# Only 1 file. Simple interface
		p=VideoPlayer()
		p.main(sys.argv[1])
	else:
		# Multiple files.
		p=MultiVideoPlayer()
		p.main(sys.argv[1:])
