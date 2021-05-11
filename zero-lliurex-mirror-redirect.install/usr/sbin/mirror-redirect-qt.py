#!/usr/bin/env python3
import sys
import os
from PySide2.QtWidgets import QApplication
from appconfig.appConfigScreen import appConfigScreen as appConfig
app=QApplication(["Mirror Redirect"])
config=appConfig("redirect",{'app':app})
config.setRsrcPath("/usr/share/mirror-redirect/rsrc")
#config.setIcon('')
config.setBanner('redirect_banner.png')
config.setTextDomain('zero-lliurex-mirror-redirect')
config.setWiki('')
config.setBackgroundImage('redirect_login.svg')
config.setConfig(confDirs={'system':'/usr/share/mirror-redirect','user':'%s/.config'%os.environ['HOME']},confFile="redirect.conf")
config.Show()
config.setFixedSize(config.width(),config.height())

app.exec_()
