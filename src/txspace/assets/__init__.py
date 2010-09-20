# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import os.path

import pkg_resources as pkg

from twisted.python import filepath

from nevow import static, dirlist

# def enable_assets(rsrc, moduleName, modulePath=None):
# 	if(modulePath is None):
# 		modulePath = 'webroot'
# 	assets_root = EggFile(moduleName, modulePath)
# 	rsrc.putChild('assets', assets_root)

def enable_assets(rsrc, assets_path=None, name='assets'):
	if(assets_path is None):
		assets_path = pkg.resource_filename(__name__, 'webroot')
	assets_root = static.File(assets_path)
	rsrc.putChild(name, assets_root)

def get(*path):
	item_path = os.path.join(os.path.dirname(__file__), *path)
	absolute_path = os.path.abspath(item_path)
	return absolute_path

class EggFile(static.File):
	def __init__(self, moduleName, modulePath):
		static.File.__init__(self, modulePath)
		self.moduleName = moduleName
		self.modulePath = modulePath
	
	def directoryListing(self):
		return dirlist.EggFileDirectoryLister(self.moduleName, self.modulePath)
	
	def openForReading(self):
		return pkg.resource_stream(self.moduleName, self.modulePath)
	
	def getFileSize(self):
		return len(pkg.resource_string(self.moduleName, self.modulePath))

class EggFileDirectoryLister(dirlist.DirectoryLister):
	def __init__(self, moduleName, modulePath):
		dirlist.DirectoryLister.__init__(self, modulePath)
		self.moduleName = moduleName
		self.modulePath = modulePath
	
	def data_listing(self, context, data):
		from nevow.static import getTypeAndEncoding
		
		directory = pkg.resource_listdir(self.moduleName, self.modulePath)
		directory.sort()
		
		files = []; dirs = []
		
		for path in directory:
			url = urllib.quote(path, '/')
			if pkg.resource_is_dir(self.moduleName, os.path.join(self.modulePath, path)):
				url = url + '/'
				dirs.append({
					'link': url,
					'linktext': path + "/",
					'type': '[Directory]',
					'filesize': '',
					'encoding': '',
					})
			else:
				mimetype, encoding = getTypeAndEncoding(
					path,
					self.contentTypes, self.contentEncodings, self.defaultType)
				
				content = pkg.resource_string(self.moduleName, os.path.join(self.modulePath, path))
				filesize = len(content)
				del content
				files.append({
					'link': url,
					'linktext': path,
					'type': '[%s]' % mimetype,
					'filesize': formatFileSize(filesize),
					'encoding': (encoding and '[%s]' % encoding or '')})
		
		return dirs + files
