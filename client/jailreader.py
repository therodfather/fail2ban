# This file is part of Fail2Ban.
#
# Fail2Ban is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Fail2Ban is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fail2Ban; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# Author: Cyril Jaquier
# 
# $Revision$

__author__ = "Cyril Jaquier"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Cyril Jaquier"
__license__ = "GPL"

import logging, re
from configreader import ConfigReader
from filterreader import FilterReader
from actionreader import ActionReader

# Gets the instance of the logger.
logSys = logging.getLogger("fail2ban.client.config")

class JailReader(ConfigReader):
	
	actionCRE = re.compile("^((?:\w|-|_|\.)+)(?:\[(.*)\])?$")
	
	def __init__(self, name):
		ConfigReader.__init__(self)
		self.name = name
		self.filter = None
		self.actions = list()
	
	def setName(self, value):
		self.name = value
	
	def getName(self):
		return self.name
	
	def read(self):
		ConfigReader.read(self, "jail")
	
	def isEnabled(self):
		return self.opts["enabled"]
	
	def getOptions(self):
		opts = [["bool", "enabled", "false"],
				["string", "logpath", "/var/log/messages"],
				["int", "maxretry", 3],
				["int", "maxtime", 600],
				["int", "bantime", 600],
				["string", "filter", ""],
				["string", "action", ""]]
		self.opts = ConfigReader.getOptions(self, self.name, opts)
		
		if self.isEnabled():
			# Read filter
			self.filter = FilterReader(self.opts["filter"], self.name)
			ret = self.filter.read()
			if ret:
				self.filter.getOptions(self.opts)
			else:
				logSys.error("Unable to read the filter")
				return False
			
			# Read action
			for act in self.opts["action"].split('\n'):
				try:
					splitAct = JailReader.splitAction(act)
					action = ActionReader(splitAct, self.name)
					ret = action.read()
					if ret:
						action.getOptions(self.opts)
						self.actions.append(action)
					else:
						raise AttributeError("Unable to read action")
				except AttributeError, e:
					logSys.error("Error in action definition " + act)
					logSys.debug(e)
					return False
		return True
	
	def convert(self):
		stream = [["add", self.name]]
		for opt in self.opts:
			if opt == "logpath":
				stream.append(["set", self.name, "logpath", self.opts[opt]])
			elif opt == "maxretry":
				stream.append(["set", self.name, "maxretry", self.opts[opt]])
			elif opt == "maxtime":
				stream.append(["set", self.name, "maxtime", self.opts[opt]])
			elif opt == "bantime":
				stream.append(["set", self.name, "bantime", self.opts[opt]])
		stream.extend(self.filter.convert())
		for action in self.actions:
			stream.extend(action.convert())
		return stream
	
	@staticmethod
	def splitAction(action):
		m = JailReader.actionCRE.match(action)
		d = dict()
		if m.group(2) <> None:
			for param in m.group(2).split(','):
				p = param.split('=')
				d[p[0].strip()] = p[1].strip()
		return [m.group(1), d]
