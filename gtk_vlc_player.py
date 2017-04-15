#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk,GObject
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
		self.player_paused=False
		self.is_player_active = False
		_vlc_widget = VLCWidget(*p)
		self.player = _vlc_widget.player
		self.pack_start(_vlc_widget, True, True, 0)
		_toolbar = self.get_player_control_toolbar()
		self.pack_start(_toolbar, False, False, 0)
		self.connect("destroy", self.close)
		self.events = self.player.event_manager()
		self.events.event_attach(vlc.EventType.MediaPlayerVout, self._realized)

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
		self.playback_button = builder.get_object("play")
		self.play_image = Gtk.Image.new_from_icon_name(
				"gtk-media-play",
				Gtk.IconSize.MENU
			)
		self.pause_image = Gtk.Image.new_from_icon_name(
				"gtk-media-pause",
				Gtk.IconSize.MENU
			)
		self.volume = builder.get_object("volume")
		return builder.get_object("controls")
		
	def toggle_player_playback(self, widget, data=None):
		"""	Handler for Player's Playback Button (Play/Pause).
		"""
		if self.is_player_active == False and self.player_paused == False:
			self.player.play()
			self.playback_button.set_image(self.pause_image)
			self.is_player_active = True

		elif self.is_player_active == True and self.player_paused == True:
			self.player.play()
			self.playback_button.set_image(self.pause_image)
			self.player_paused = False

		elif self.is_player_active == True and self.player_paused == False:
			self.player.pause()
			self.playback_button.set_image(self.play_image)
			self.player_paused = True
		else:
			pass
		
	def timeout(self):
		if self.timer_on:
			self.seekbar.set_value(self.player.get_position())
		return self.timer_on

	def set_media(self, path):
		media = instance.media_new(path)
		self.player.set_media(media)

	def set_time(self, widget, scroll, value):
		if scroll == Gtk.ScrollType.JUMP:
			self.player.set_position(value)
			
	def set_volume(self, widget, value):
		value = round(value) #vlc takes ints as volume
		self.player.audio_set_volume(value)
		
	def _realized(self, event):
		self.volume.set_value(self.player.audio_get_volume())
		self.is_player_active = True
		self.events.event_detach(vlc.EventType.MediaPlayerVout)
			
	def close(self, widget):
		self.timer_on = False

class VideoPlayer:
	"""Example simple video player.
	"""
	def __init__(self):
		self.vlc = DecoratedVLCWidget()

	def main(self, fname):
		self.vlc.set_media(fname)
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