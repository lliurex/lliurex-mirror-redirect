#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk
import shutil
import os
import subprocess
import time
import threading
import sys
import ssl
import xmlrpc.client as n4d
import lliurex.interfacesparser
import yaml
from edupals.ui.n4dgtklogin import *
import gettext
gettext.textdomain('zero-lliurex-mirror-redirect')
_ = gettext.gettext

class redirectMirror(threading.Thread):
	def __init__(self,callback):
		threading.Thread.__init__(self)
		self.dbg=9
		self.sw_slave=False
		self.master_ip=''
		self.callback=callback
		self.hostFile="/var/lib/dnsmasq/hosts/mirror"
		self.cnameFile="/var/lib/dnsmasq/config/cname-mirror"
		self.mirror_dir="/net/mirror/llx19"
		self.slave_ip=''
		self.master_ip='10.3.0.254'
		self.n4d=self._n4d_connect("localhost")
		self._set_server_data()
		self.n4dMaster=self._n4d_connect(self.master_ip)
		self.credentials=[]
	#def __init__

	def _debug(self,msg):
		if self.dbg==1:
			print(("DBG: "+str(msg)))
	#def _debug

	def _n4d_connect(self,server):
		context=ssl._create_unverified_context()
		n4dclient=n4d.ServerProxy("https://%s:9779"%server,allow_none=True,context=context)
		return(n4dclient)

	def set_credentials(self,credentials):
		self.credentials=credentials

	def _set_server_data(self):
		self.master_ip=self.n4d.get_variable("","VariablesManager","MASTER_SERVER_IP")
		if (self.master_ip):
			self.sw_slave=True
		else:
			self.master_ip=self.n4d.get_variable("","VariablesManager","SRV_IP")
	#def _set_server_data

	def is_enabled(self):
		sw_enabled=False
		self.slave_ip=self._get_replication_ip()
		try:
			sw_enabled=self.n4dMaster.is_mirror_shared("","NfsManager","/net/mirror/llx19",self.slave_ip)['status']
		except:
			sw_enabled=False
		return(sw_enabled)
	#def is_enabled

	def enable_redirect(self):
		sw_add=False
		if not os.path.isdir(self.mirror_dir):
			try:
				os.makedirs(self.mirror_dir)
			except:
				self._debug("Can't create dir %s"%self.mirror_dir)
		
		try:
			sw_add=self.n4dMaster.add_mirror(self.credentials,"NfsManager",self.mirror_dir,self.slave_ip)['status']
			if not self.n4d.is_mount_configured(self.credentials,"NfsManager",self.mirror_dir)['status']:
				self.n4d.configure_mount_on_boot(self.credentials,"NfsManager",self.master_ip+":"+self.mirror_dir,self.mirror_dir)
				self._debug("Mounting on boot")
		except Exception as e:
			print(e)
			sw_add=False
		GObject.idle_add(self.callback,sw_add)
		return sw_add
	#def enable_redirect

	def disable_redirect(self):
		try:
			self.n4d.remove_mount_on_boot(self.credentials,"NfsManager",self.mirror_dir)
			sw_rm=self.n4dMaster.remove_ip_from_mirror(self.credentials,"NfsManager",self.mirror_dir,self.slave_ip)['status']
		except:
			sw_rm=False
		GObject.idle_add(self.callback,1)
		return sw_rm
	#def disable_redirect

	def _get_replication_ip(self):
				
		path="/etc/netplan/30-replication-lliurex.yaml"
		try:
			if os.path.exists(path):
				with open(path,"r") as stream:
					data=yaml.safe_load(stream)
				eth=list(data["network"]["ethernets"].keys())[0]
				return data["network"]["ethernets"][eth]["addresses"][0].split("/")[0]
		except Exception as e:
			print("Failed getting replication IP")
			print(e)
			raise e		
		
	#def _get_replication_ip
	
class mainWindow(Gtk.Window):
	def __init__(self):
		self.redirectMirror=redirectMirror(self._callback)
		if not self.redirectMirror.sw_slave:
			print("[!] You need to be on a slave server to run this program [!]")
			label = Gtk.Label(_("You need to be on a slave server to run mirror-redirect"))
			dialog = Gtk.Dialog("Warning", None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
			dialog.vbox.pack_start(label,True,True,10)
			label.show()
			dialog.set_border_width(6)
			response = dialog.run()
			dialog.destroy()
			sys.exit(0)

		self.dbg=False
		Gtk.Window.__init__(self,title=_("Mirror Redirect"))
		self.set_resizable(False)
		self.stack=Gtk.Stack()
		self.stack.set_transition_duration(1000)
		self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
		form_grid=Gtk.Grid()
		form_grid.set_valign(Gtk.Align.START)
		form_grid.set_halign(Gtk.Align.CENTER)
		form_grid.set_column_homogeneous(False)
		form_grid.set_row_homogeneous(False)
		form_grid.set_margin_right(0)
		login=N4dGtkLogin()
		desc=_("From here you can redirect the mirror in a slave server to the master server's own mirror")
		login.set_info_text("<span foreground='black'>Mirror Redirect</span>",_("Redirect mirror"),"<span foreground='black'>"+desc+"</span>")
		login.set_info_background(image='/usr/share/mirror-redirect/rsrc/redirect.svg',cover=True)
		login.set_allowed_groups(['adm'])
		login.after_validation_goto(self._signin)
		login.set_mw_proportion_ratio(2,1)
		img_banner=Gtk.Image()
		img_banner.set_from_file('/usr/share/mirror-redirect/rsrc/redirect_banner.png')
		form_grid.attach(img_banner,0,0,2,1)
		lbl_switch=Gtk.Label(_("Enable mirror redirection"))
		lbl_switch.set_halign(Gtk.Align.END)
		form_grid.attach(lbl_switch,0,2,1,1)
		self.sw_enable=Gtk.Switch()
		self.sw_enable.set_halign(Gtk.Align.START)
		form_grid.attach(self.sw_enable,1,2,1,1)
		self.lbl_state=Gtk.Label('')
		self.lbl_state.set_width_chars(30)
		self.lbl_state.set_halign(Gtk.Align.CENTER)
		self.lbl_state.set_valign(Gtk.Align.START)
		self.lbl_state.set_xalign(0)
		self.lbl_state.modify_fg(Gtk.StateType.NORMAL,Gdk.color_parse('#888'))
		form_grid.attach(self.lbl_state,0,3,2,1)
		self.spinner = Gtk.Spinner()
		form_grid.attach(self.spinner,0,1,2,3)
		self.sw_enable.set_active(self.redirectMirror.is_enabled())
		if self.sw_enable.get_state():
			service_label=_("Using master server mirror")
		else:
			service_label=_("Using local mirror")
		self.lbl_state.set_text(_(service_label))
		self.sw_enable.connect("state-set",self._on_sw_state)
		
		self.stack.add_titled(login, "login", "Login")
		self.stack.add_titled(form_grid, "gui", "Gui")
		self.stack.set_visible_child_name("login")
		self.add(self.stack)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.connect("delete-event", Gtk.main_quit)

		self.show_all()
	#def __init__
				
	def _signin(self,user,pwd,server):
		self.credentials=[user,pwd]
		self.redirectMirror.set_credentials(self.credentials)
		self.stack.set_visible_child_name("gui")

	def _debug(self,msg):
		if self.dbg==1:
			print(("DBG: "+str(msg)))
	#def _debug

	def _on_sw_state(self,widget,data):
		self._debug("State changed")
		widget.set_sensitive(False)
		self.spinner.start()
		sw_state=widget.get_state()
		if not sw_state:
			self._debug("Redirecting mirror...")
			self.lbl_state.set_text(_("Redirecting mirror..."))
			th=threading.Thread(target=self.redirectMirror.enable_redirect)
			th.start()
		else:
			self.lbl_state.set_text(_("Redirecting mirror..."))
			th=threading.Thread(target=self.redirectMirror.disable_redirect)
			th.start()
		self._debug("Done")
	#def _on_sw_state

	def _callback(self,action=None):
		self.spinner.stop()
		if action:
			self.lbl_state.set_text(_("Using master server mirror"))
		else:
			self.lbl_state.set_text(_("Using local mirror"))
			self.sw_enable.handler_block_by_func(self._on_sw_state)
			self.sw_enable.set_state(False)
			self.sw_enable.handler_unblock_by_func(self._on_sw_state)
		self.sw_enable.set_sensitive(True)
	#def _callback

def read_key():
	try:
		f=open("/etc/n4d/key")
		f.close()
		#hack
		return True
	except:
		return False

status=read_key()
status=True

if not status:
	print("[!] You need root privileges to run this program [!]")
	label = Gtk.Label(_("You need root privileges to run mirror-redirect"))
	dialog = Gtk.Dialog("Warning", None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
	dialog.vbox.pack_start(label,True,True,10)
	label.show()
	dialog.set_border_width(6)
	response = dialog.run()
	dialog.destroy()
#	sys.exit(0)

GObject.threads_init()
Gdk.threads_init()
win = mainWindow()
Gtk.main()
