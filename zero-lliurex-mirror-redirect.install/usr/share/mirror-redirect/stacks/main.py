from PySide2.QtWidgets import QApplication, QLabel, QWidget, QPushButton,QGridLayout,QLineEdit,QHBoxLayout,QComboBox,QCheckBox
from PySide2 import QtGui
from PySide2.QtCore import Qt
from appconfig.appConfigStack import appConfigStack as confStack
from appconfig.appConfigN4d import appConfigN4d
import lliurex.interfacesparser
import os
import subprocess
import time
import threading
import sys
import ssl
import yaml

import gettext
_ = gettext.gettext

class main(confStack):
	def __init_stack__(self):
		self.dbg=True
		self._debug("Main Stack loaded")
		self.description="Redirect Mirror"
		self.visible=False
		self.enabled=True
		self.level='n4d'
		self.n4d_master=appConfigN4d()
		self.mirror_dir="/net/mirror/llx19"
	#def __init__
	
	def _load_screen(self):
		self._set_server_data()
		box=QGridLayout()
		#self.statusBar=QAnimatedStatusBar.QAnimatedStatusBar()
		#box.addWidget(self.statusBar)
		self.setLayout(box)
		self.chkEnabled=QCheckBox(_("Enable mirror redirection"))
		#self.chkEnabled.stateChanged.connect(self._on_sw_state)
		box.addWidget(self.chkEnabled,0,0,1,1)
		self.updateScreen()
		return(self)
	#def _load_screen

	def updateScreen(self):
		self._set_server_data()
			#self.name.setDescription(_("name of the repository"),_("Insert repository name"))
		if self.is_enabled():
			self.chkEnabled.setChecked(True)
	#def _udpate_screen

	def _on_sw_state(self,state):
			pass
	#def _on_sw_state

	def is_enabled(self):
		sw_enabled=False
		self.slave_ip=self._get_replication_ip()
		self._debug("Slave IP: {}".format(self.slave_ip))
		try:
				#sw_enabled=self.n4dMaster.is_mirror_shared("","NfsManager","/net/mirror/llx19",self.slave_ip)['status']
			resp=self.n4d_master.n4dQuery("NfsManager","is_mirror_shared","/net/mirror/llx19",self.slave_ip)
			if isinstance(resp,dict):
				if resp['status']==0:
					sw_enabled=True
				elif resp['status']<0:
					self.showMsg("Error Code: {}".format(resp['status']))
		except Exception as e:
			print(e)
			self._debug(e)
			sw_enabled=False
		self._debug("Redirect enabled: {}".format(sw_enabled))
		return(sw_enabled)
	#def is_enabled
	
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
	
	def _set_server_data(self):
			#self.master_ip=self.n4dQuery("VariablesManager","get_variable","MASTER_SERVER_IP")
		master_ip=self.n4dGetVar(var="MASTER_SERVER_IP")
		self.master_ip=''
		if isinstance(master_ip,dict):
			self.master_ip=master_ip.get('ip','')
		if (self.master_ip):
			self.sw_slave=True
		else:
			master_ip=self.n4dGetVar(var="SRV_IP")
			if isinstance(master_ip,dict):
				self.master_ip=master_ip.get('ip','')
		if self.n4d_master.server=='server':
			self.n4d_master.server=self.master_ip
	#def _set_server_data
	
	def enable_redirect(self):
		sw_add=False
		if not os.path.isdir(self.mirror_dir):
			try:
				os.makedirs(self.mirror_dir)
			except:
				self._debug("Can't create dir %s"%self.mirror_dir)
				self.showMsg(_("Can't create dir {}".format(self.mirror_dir)))
				return sw_add
		
		try:
			sw_add=self.n4d_master.n4dQuery("NfsManager","add_mirror",self.mirror_dir,self.slave_ip)
			if not self.n4dQuery("NfsManager","is_mount_configured",self.mirror_dir):
				self._debug("Mounting on boot")
				try:
					self.n4dQuery("NfsManager","configure_mount_on_boot",self.master_ip+":"+self.mirror_dir,self.mirror_dir)
				except Exception as e:
					print("Mount error: {}".format(e))
					sw_add=False
		except Exception as e:
			print("Add mirror err: {}".format(e))
			self.showMsg(_("Add mirror error {}".format(e)))
			sw_add=False
		return sw_add
	#def enable_redirect
	
	def writeConfig(self):
		state=self.chkEnabled.isChecked()
		self._debug("State changed to {}".format(state))
#widget.set_sensitive(False)
#		self.spinner.start()
		if state:
			self._debug("Redirecting mirror...")
#			self.lbl_state.set_text(_("Redirecting mirror..."))
			#th=threading.Thread(target=self.enable_redirect)
			#th.start()
			if not self.enable_redirect():
				self.chkEnabled.setChecked(False)
		else:
			self.lbl_state.set_text(_("Redirecting mirror..."))
			if not self.disable_redirect():
				self.chkEnabled.setChecked(False)
#			th=threading.Thread(target=self.redirectMirror.disable_redirect)
#			th.start()
		self._debug("Done")
	#def writeConfig

