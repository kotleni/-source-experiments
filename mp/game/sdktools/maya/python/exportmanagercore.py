import os
import utils
import maya.mel
import vectors
import mayaVectors
import names
import api
import re
import triggered, qcTools, re, vmf
import templateStrings
import modelpipeline as mp
import modelpipeline.apps
from filesystem import *
import maya.cmds as cmd
import maya.OpenMaya as OpenMaya
import mayaVectors as mvectors
from meshUtils import *

try:
	import vs
except ImportError: vs = None

TOOL_NAME = 'zooAssets'
mel = api.mel
melecho = api.melecho

DEFAULT_DEFAULT = ''

import filesystem
filesystem.DEFAULT_CHANGE = 'Maya Auto Checkout'


def getAllParents( object ):
	allParents = []
	parent = [object]
	while parent is not None:
		allParents.append(parent[0])
		parent = cmd.listRelatives(parent,parent=True,pa=True)
	return allParents[1:]


def isSceneUnderCurrentProject():
	'''
	if the current scene is somewhere under the current project return True, otherwise False.  opening a scene that isn't
	under the current project can cause problems when determining asset roots etc...
	'''
	scenePath = cmd.file(q=True, sn=True)
	if scenePath:
		scenePath = Path( scenePath )
		for mod in gameInfo.getSearchMods():
			if scenePath.isUnder( content() / mod ):
				return True

		return False
	#if the scene hasn't been saved, always return true
	else:
		return True


def getAssetRoot( scenePath=None ):
	if scenePath is None:
		scenePath = cmd.file(q=True, sn=True)

	rootPath = mp.apps.getAssetRoot( scenePath )
	if rootPath is None:
		print "WARNING :: root path cannot be determined - using scene directory as fallback"
		rootPath = Path( scenePath ).up()

	return rootPath


def validateExportNodeName():
	'''makes sure the infoNode name matches the scene name'''
	scenePath = Path( cmd.file(q=True, sn=True) )

	suffixesToStrip = ['model', 'reference', 'rig']
	sceneName = scenePath.name()

	for suf in suffixesToStrip:
		sceneName = sceneName.replace('_'+ suf, '').replace(suf, '')

	sceneName += '_exportData'
	if exportManager.node != sceneName:
		exportManager.node = cmd.rename(exportManager.node, sceneName)


VALID_ASSET_SUFFIXES = ['rig']


#this may complain when running under a branch that hasn't implemented modelpipeline - in which case ignore...
try:
	VALID_ASSET_SUFFIXES += list( mp.ComponentInterface_model.SUFFIXES )
	VALID_ASSET_SUFFIXES += list( mp.ComponentInterface_physics.SUFFIXES )
except AttributeError: pass


def getAssetRootAndName():
	scenePath = cmd.file(q=True, sn=True)
	if scenePath == '':
		return None, None

	root = getAssetRoot()
	scenePath = Path(scenePath)

	assetName = scenePath.name().lower()
	for suffix in VALID_ASSET_SUFFIXES:
		assetName = assetName.replace('_%s' % suffix, '')

	if root is None:
		return scenePath.up(), assetName

	return root, assetName


def getDefaultExportPath():
	root, name = getAssetRootAndName()
	cur = cmd.file(q=True, sn=True)

	#in this case, the scene hasn't been saved - default to the models dir...
	if cur == '':
		cur = '%VCONTENT%/'+ mod() +'/models/tmp'  #NOTE: the tmp gets popped off below...

	cur = Path( cur )
	cur = cur.up()  #we never want to take into account the filename, so remove it completely...

	if root is None:
		root = cur

	if 'animation' in cur.lower() or 'animations' in cur.lower():
		return root /'dmx/animation/'

	return root /'dmx/'


class ExportManagerException(Exception):
	'''
	this exception can optionally be used to display the error message in a warning dialog
	instead of spewed to the console - makes errors more visible, and possibly easier to
	act upon for users provided good error messages are present...

	to show the dialog box with the error, use the kwarg:
	show=True
    '''
	def __init__( self, *args, **kwargs ):
		if kwargs.get('show', False):
			cmd.confirmDialog(m=args[0], t='ERROR', b=('OK',), db='OK')
		Exception.__init__(self, args[0])


class ExportComponent(object):
	'''
	this is the interface to a single export component
    '''
	kASSET_FORMAT = "ast%s"            #takes slot arg
	kATTR_FORMAT = "ast%s_%s"          #takes slot and attr args
	### these are the type names
	TYPES =\
		  kANIM, kCAMERA, kHITBOX, kMODEL, kPHYSICS, kVMF, kVTA, kVRD =\
		  'skeletalAnimation', 'camera', 'hitbox', 'model', 'physicsModel', 'vmf', 'vta', 'vrd'

	### the UI labels for the various types
	TYPE_LABELS = {kANIM: 'animation',
				   kCAMERA: 'camera',
				   kHITBOX: 'hitbox',
				   kMODEL: 'model',
				   kPHYSICS: 'physics',
				   kVMF: 'vmf',
				   kVRD: 'helper bones',
				   kVTA: 'face shapes'}

	### list of types that are considered animation types - ie have some sort of time association
	ANIMATION_TYPES = set([kANIM,
						   kCAMERA])

	### the different export file extensions for the various asset types
	DEFAULT_EXTENSION = 'dmx'
	EXTENSIONS = { kVMF: 'vmf',
				   kVRD: 'vrd',
				   kVTA: 'vta' }

	#this may complain when running under a branch that hasn't implemented modelpipeline - in which case ignore...
	try:
		EXTENSIONS[ kHITBOX ] = mp.DmxExtensions.getFormatExtension( mp.DmxExtensions.HITBOX )
	except AttributeError: pass

	### this dict holds the default values (can be method objects) for various attributes - if an attribute name is not found here, '' is used
	ATTR_DEFAULTS = {'disable': 0,
					 'start': lambda: int(cmd.playbackOptions(q=True, min=True)),
					 'end': lambda: int(cmd.playbackOptions(q=True, max=True)),
					 'type': kANIM,
					 'shots': "0:0",
					 'linkToShots': 0,
					 'ignoreError': 0,
					 'skipVST': 1,
					 'flags': '-bc ',
					 'upAxis': lambda: cmd.upAxis(q=True, ax=True).upper()}

	### no default attrs are attributes that never get deleted - ie they always have an actual value
	NO_DEFAULT_ATTRS = set(['type',
							'start',
							'end'])

	### used to define attribute variable types - defaults to string as thats how all data is stored
	GET_TYPE_CONVERSIONS = {'start': int,
							'end': int,
							'path': Path,
							'disable': int,
							'mass': float,
							'excludeList': lambda data: tuple() if data is None else cmd.sets(data, q=True),
							'animLayers': lambda data: tuple() if data is None else cmd.sets(data, q=True)}

	SET_TYPE_CONVERSIONS = {'start': int,
							'end': int,
							'path': Path,
							'disable': int,
							'mass': float }

	### currently not used...
	GOOD_POST_SKINHISTORY_TYPES = set(["vstInfo",
									   "transform",
									   "mesh",
									   "displayLayer",
									   "objectSet",
									   "groupParts",
									   "groupId"])
	def __init__( self, slot, fromNode='' ):
		self.slot = slot
		self._node = fromNode  #record the node that this asset belongs to
		self._generated = []
	def __str__( self ):
		return '<"%s": %s>' % (self.getAttr('name'), self.getAttr('type'))
	__repr__ = __str__
	def __int__( self ):
		return self.slot
	def __contains__( self, item ):
		'''
		returns whether a given object is in the asset or not - NOTE: this doesn't take into account
		generated items...
        '''
		return str(item) in map(str, self.objs)
	def __iter__( self ):
		return iter(self.objs)
	@classmethod
	def GetDefault( cls, attr, node, slot=None ):
		'''
		returns the default value for a given attr.  some attr default values depend on the slot as well,
		so its good practise, although not nessecary to pass the slot arg as well
        '''
		#is there a default already set on the info node?
		globalDefaultAttrname = ExportManager.kDEFAULT_ATTR_FORMAT % attr
		globalDefaultAttrpath = '%s.%s' % (node, globalDefaultAttrname)
		if cmd.objExists(globalDefaultAttrpath):
			if attr == "exportRelative":
				connected = cmd.listConnections(globalDefaultAttrpath, d=False)
				if connected: return connected[0]
				return DEFAULT_DEFAULT
			return cmd.getAttr(globalDefaultAttrpath)

		#is there a preset file for the default setting?  if so grab it
		presetDefault = readPreset(GLOBAL, TOOL_NAME, attr, 'default')
		if presetDefault:
			return presetDefault[0]

		try:
			default = cls.ATTR_DEFAULTS[attr]
			try: return default()
			except TypeError: return default
		except KeyError:
			pass

		return DEFAULT_DEFAULT
	@staticmethod
	def SetDefault( attr, data, node ):
		'''
		sets the value for a scene asset attribute default
        '''
		attrname = ExportManager.kDEFAULT_ATTR_FORMAT % attr
		attrpath = "%s.%s" % (node, attrname)

		#this is a connection based attribute - so deal with it specially
		if attr == "exportRelative":
			if not cmd.objExists(data):
				api.melError( "you're trying to add %s as the default export relative object - this object doesn't exist in the scene!" % data )
				return

			if not cmd.objExists(attrpath): cmd.addAttr(node, at="message", ln=attrname)
			cmd.connectAttr("%s.message" % data, attrpath, f=True)
		else:
			if not cmd.objExists(attrpath): cmd.addAttr(node, dt="string", ln=attrname)
			cmd.setAttr(attrpath, data, type="string")
	@staticmethod
	def DeleteDefault( attr, node ):
		'''
		removes an scene default asset attribute - NOTE: this will not remove any preset based defaults...
        '''
		if not cmd.objExists(node): return
		attrname = ExportManager.kDEFAULT_ATTR_FORMAT % attr
		try:
			cmd.deleteAttr('%s.%s' % (node, attrname))
		except TypeError: pass
	@staticmethod
	def ListAttrsWithSceneDefaults( node ):
		'''
		lists all attributes that have scene defaults - ie are listed as defaults on the exportManger.node node
        '''
		if node is None or not cmd.objExists(node):
			return []

		allAttrs = cmd.listAttr(node, ud=True)
		attrs = []

		if allAttrs is not None:
			regEx = re.compile('^%s$' % (ExportManager.kDEFAULT_ATTR_FORMAT % '([a-zA-Z0-9][a-zA-Z0-9]+)'))
			for attr in allAttrs:
				search = regEx.search(attr)
				if search is not None:
					attrs.append(search.groups()[0])

		return attrs
	def getAttr( self, attr ):
		'''
		returns an attribte value - NOTE: if the attribute doesn't actually exist, its default
		value is returned - if you need to know the actual value of an attribute, use getActualAttr()
        '''
		info = self.getActualAttr(attr)
		if info is None:
			return self.GetDefault(attr, self.node)

		type_conv = self.GET_TYPE_CONVERSIONS.get(attr, DEFAULT_DEFAULT)
		try:
			info = type_conv(info)
		except TypeError: pass

		return info
	def getActualAttr( self, attr ):
		'''
		returns the actual attribute value - if the attribute doesn't exist, None is returned
        '''
		default = self.GetDefault(attr, self.node)
		attrname = self.kATTR_FORMAT % (self.slot, attr)
		attrpath = '%s.%s' % (self.node, attrname)

		#if the attribute doesn't exist, return None
		if not cmd.objExists(attrpath):
			return None

		#deal with this attribute separately - its data is gained by tracing a connection
		if attr == 'exportRelative':
			connected = cmd.listConnections(attrpath, d=False)
			if connected: return connected[0]
			return None
		elif attr == 'excludeList':
			connected = cmd.listConnections(attrpath, d=False)
			if connected: return connected[0]
			return None
		elif attr == 'animLayers':
			connected = cmd.listConnections(attrpath, d=False)
			if connected: return connected[0]
			return None

		data = cmd.getAttr(attrpath)

		return data
	def setAttr( self, attr, data ):
		default = self.GetDefault(attr, self.node, self.slot)
		hasDefault = True
		attrname = self.kATTR_FORMAT % (self.slot, attr)
		attrpath = "%s.%s" % (self.node, attrname)

		#try to type convert the data before setting it...
		type_conv = self.SET_TYPE_CONVERSIONS.get(attr, None)
		if type_conv is not None:
			data = type_conv(data)

		#this section is an optional formatting section - if you want strict formatting
		#of attr data, put in a case for the attr name, and proceed to format the data
		if attr == "name":
			#make sure the name doesn't have any silly characters in it...
			tmpIdx = data.rfind('.')
			if tmpIdx != -1: data = data[:tmpIdx]
			data = api.validateAsMayaName(data)

			if data == '': data = "__blank__"

			#now we need to make sure there are no name clashes - we don't want to create
			#an asset with a name that is already being used
			exportPathAlreadyExists = True

			#first remove *this* asset from the list
			assets = [ a for a in AnExportManager( self.node ).ls() if a.slot != self.slot ]
			thisDir = self.getExportPath().up()
			proposedNewPath = (thisDir / data).setExtension( self.getExtension() )
			while exportPathAlreadyExists:
				try:
					for a in assets:
						aPath = a.getExportPath()
						if proposedNewPath == aPath:
							data += '_dupe'
							proposedNewPath = (thisDir / data).setExtension( self.getExtension() )
							raise BreakException

					exportPathAlreadyExists = False
				except BreakException: pass
		elif attr == "type":
			#make sure the type is valid
			if data not in ExportComponent.TYPES:
				api.melError('no such type: %s' % data)
				return
		elif attr == "path":
			#make the path vcontent relative
			data = Path( data ) << '%VCONTENT%'
		elif attr == "exportRelative":
			if not cmd.objExists(attrpath):
				cmd.addAttr(self.node, at="message", ln=attrname)

			#if the data variable is empty, delete the attribute and bail
			if data == '':
				cmd.deleteAttr(attrpath)
				return
			if not cmd.objExists(data):
				api.melError( "you're trying to add %s as the default export relative object - this object doesn't exist in the scene!" % data)

			cmd.connectAttr("%s.message" % data, attrpath, f=True)
			return
		elif attr == "excludeList":
			if not cmd.objExists( attrpath ):
				cmd.addAttr(self.node, at="message", ln=attrname)

			#if the data variable is empty, delete the attribute and bail
			if not data:
				cmd.deleteAttr( attrpath )
				return

			if isinstance( data, basestring ):
				data = [ data ]

			data = list( data )
			excludeSet = self.getAttrObj( attrname )
			if excludeSet is None:
				excludeSet = AnExportManager.CreateExportSet( data )
				cmd.connectAttr( "%s.message" % excludeSet, attrpath, f=True )
			else:
				cmd.sets( e=True, clear=excludeSet )
				cmd.sets( data, e=True, forceElement=excludeSet )

			return
		elif attr == "animLayers":
			if not cmd.objExists( attrpath ):
				cmd.addAttr(self.node, at="message", ln=attrname)

			#if the data variable is empty, delete the attribute and bail
			if not data:
				cmd.deleteAttr( attrpath )
				return

			if isinstance( data, basestring ):
				data = [ data ]

			data = list( data )
			animLayerSet = self.getAttrObj( attrname )
			if animLayerSet is None:
				animLayerSet = AnExportManager.CreateExportSet( data )
				cmd.connectAttr( "%s.message" % animLayerSet, attrpath, f=True )
			else:
				cmd.sets( e=True, clear=animLayerSet )
				cmd.sets( data, e=True, forceElement=animLayerSet )

			return

		if not cmd.objExists("%s.ast%s" % (self.node, self.slot)):
			api.melError("slot doesn't exist")

		#if the data is being set to the default value, delete the attribute as its no longer needed
		if attr in self.NO_DEFAULT_ATTRS: hasDefault = False
		if data == default and hasDefault:
			if cmd.objExists(attrpath):
				cmd.deleteAttr(attrpath)
			return

		if not cmd.objExists(attrpath):
			cmd.addAttr(self.node, dt="string", ln=attrname)

		cmd.setAttr(attrpath, str(data), type="string")
	def delAttr( self, attr ):
		self.setAttr(attr, self.GetDefault(attr, self.slot))
	def lsAttr( self ):
		'''
		lists all attributes for this asset
        '''
		allAttrs = cmd.listAttr(self.node, ud=True)
		attrs = []

		regEx = re.compile('^%s$' % (ExportComponent.kATTR_FORMAT % (self.slot, '([a-zA-Z0-9][a-zA-Z0-9]+)')))
		for attr in allAttrs:
			search = regEx.search(attr)
			if search is not None:
				attrs.append(search.groups()[0])

		return attrs
	def getResolvedAttr( self, attr='preMEL' ):
		rawCmdStr = self.getAttr(attr)

		#if there is no cmdStr, then return None
		if not rawCmdStr: return None

		#replace the # with the object
		obj = self.getObj()
		rawCmdStr = rawCmdStr.replace('#', obj)

		#resolve any %slot instances...
		slotRE = re.compile('\%slot;')
		rawCmdStr = slotRE.sub(lambda match: str(self.slot), rawCmdStr)

		#resolve any %prefix instances...
		prefix = self.getAttr('prefix')
		prefixRE = re.compile('\%prefix;')
		rawCmdStr = prefixRE.sub(lambda match: prefix, rawCmdStr)

		#if there isn't a user specified path for the asset, use the global export path
		path = self.getAttr('path')
		if not path: path = AnExportManager(self.node).getAttr('path')

		#resolve any %path instances...
		pathRE = re.compile('\%path;')
		rawCmdStr = pathRE.sub(lambda match: path, rawCmdStr)

		#resolve any %objs instances...
		objs = '{"%s"}' % '","'.join( self.getObjs() )
		objsRE = re.compile('\%objs;')
		rawCmdStr = objsRE.sub(lambda match: objs, rawCmdStr)

		#resolve any %xtn instances...  xtn is the exported file extension
		xtn = self.getExtension()
		xtnRE = re.compile('\%xtn;')
		rawCmdStr = xtnRE.sub(lambda match: xtn, rawCmdStr)

		#now resolve any arbitrary attribute instances - NOTE: we handle the above attributes specially as they're not straight forward
		attrRE = re.compile('(\%)([a-zA-Z_]+);')
		def attrSub(match):
			junk, attr = match.groups()
			if attr == 'preMEL' or attr == 'postMEL': return '<caught recursive %s>' % attr
			return self.getAttr(attr)
		rawCmdStr = attrRE.sub(attrSub, rawCmdStr)

		#now pass the string to triggered to resolve the remaining tokens
		rawCmdStr = triggered.Trigger(obj).resolve(rawCmdStr)

		return rawCmdStr
	def getNode( self ):
		node = self._node
		#if not cmd.objExists(node):
			#self._node = ExportManager().node

		return node
	node = property(getNode)
	def convertToSet( self ):
		xSet = AnExportManager.CreateExportSet( self.getObjs() )
		self.setObj( xSet )
	def getAttrObj( self, attrname ):
		attrpath = '%s.%s' % (self.node, attrname)
		if not cmd.objExists(attrpath):
			return None

		objPath = cmd.connectionInfo(attrpath, sfd=True)
		try:
			obj, attr = objPath.split('.')
			return obj
		except ValueError: pass
		return None
	def getObj( self ):
		'''
		returns the name of the node plugged directly into the slot attribute
        '''
		attrname = ExportComponent.kASSET_FORMAT % self.slot
		return self.getAttrObj( attrname )
	def setObj( self, obj ):
		attrname = ExportComponent.kASSET_FORMAT % self.slot
		attrpath = '%s.%s' % (self.node, attrname)
		if not cmd.objExists(attrpath):
			api.melError("slot doesn't exist - use: exportManager.createAsset(['objectName']); to create an asset")
			return

		if not cmd.objExists(obj): return
		if obj == self.getObj(): return
		if cmd.getAttr(attrpath, l=True): return
		cmd.connectAttr("%s.message" % obj, attrpath, f=True)
	obj = property(getObj, setObj)
	def getObjs( self ):
		'''
		returns the objects effectively managed by this slot - ie collapse the set if getobj() returns one
        '''
		obj = self.getObj()
		if obj is None:
			return []

		if cmd.nodeType(obj) == "objectSet":
			setObjs = cmd.sets(obj, q=True)
			if setObjs is None:
				return []
			else:
				return setObjs

		return [obj]
	def setObjs( self, newObjs ):
		obj = self.getObj()

		#if the object already in place isn't an export set, make one
		if obj is None or cmd.nodeType(obj) != 'objectSet':
			exportSet = AnExportManager.CreateExportSet(newObjs)
			self.setObj(exportSet)
			obj = exportSet
		else:
			cmd.sets(cmd.sets(obj, q=True), rm=obj)
			cmd.sets(newObjs, fe=obj)
	objs = property(getObjs, setObjs)
	def addObjs( self, obj ):
		'''
		adds the given items to the export set
        '''
		try:
			cmd.sets( obj, add=self.getObj() )
		except RuntimeError:
			#in this case the self.getObj() isn't a set - so do the conversion
			self.convertToSet()
			cmd.sets( obj, add=self.getObj() )
	add = addObjs
	def removeObjs( self, obj ):
		'''
		given a list of objects (or a single object name) will remove them from the export set
        '''
		cmd.sets( obj, remove=self.getObj() )
	remove = removeObjs
	@api.d_restoreAnimLayers
	def export( self ):
		'''
		exports the current asset instance.  returns a Path instance to the file export, or None
		if the method fails
        '''

		#Set the focus back to what it was before the window was clicked.
		#This has the effect of forcing the export name attribute to be refreshed,
		#even if enter is not pressed in the text field after editing the export name.
		cmd.setFocus(cmd.getPanel(wf=True))

		assert cmd.objExists(self.node)
		objs = self.objs
		type = self.getAttr('type')
		if not len(objs) and type != self.kVRD:
			api.melError("asset doesn't have an object associated with it - look at the properties of the asset to add objects")
			return


		#check the disable state of the slot before proceeding
		if self.getAttr('disable'):
			api.melWarning("slot %d is disabled and won't be exported" % self.slot)
			return


		#next, make sure the target export directory exists - if not, create it
		exportPath = self.getExportPath()
		exportPath.up().create()
		if not exportPath.up().exists:
			api.melError("the export directory doesn't exist, and could not be created...")
			return


		#check to see if the managed object is from a referenced file.  if so, make
		#sure the reference is loaded, and after export, restore its load state
		objUnloadStates = []
		for obj in objs:
			unloadState = cmd.nodeType(obj) == "reference"
			objUnloadStates.append(unloadState)
			if unloadState: cmd.file(lr=obj)


		#check to see that the current maya file is added to perforce - if not, add it
		curFile = P4File( cmd.file(q=True, sn=True) )
		if not curFile.managed():
			curFile.add()


		#check to see if the export file is open for edit - if the file exists
		exportPathP4 = P4File(exportPath)
		inP4 = exportPathP4.managed()
		if inP4:
			action = exportPathP4.action

			#so if the file is in perforce, but its on the users machine - try syncing to it
			if not exportPath.exists and action is None:
				exportPathP4.sync()

			#so if the file isn't open for anything in p4, try to open it
			if action is None:
				if not exportPathP4.edit():
					api.melError("could not open %s for edit - it may be locked by someone else" % exportPath)
					return


		#if certain layers have been marked for export, then make sure all other layers have been muted
		animLayersToUse = self.getAttr( 'animLayers' )
		if animLayersToUse:
			for animLayer in cmd.ls( typ='animLayer' ):
				cmd.animLayer( animLayer, e=True, mute=animLayer not in animLayersToUse )


		#execute pre export MEL command
		self._executePre()


		#build the export command string, and run the export command
		exportCmd = self._buildExportCommandStr( False )
		result = melecho.eval( exportCmd )
		api.melPrint( result )


		#if its a physics object, try to update the ragdoll limit info - if this fails, ignore with
		#a warning...
		if type == self.kPHYSICS:
			try: updateRagdoll( self.slot )
			except:
				print 'WARNING :: updateRagdoll failed on slot %s' % self.slot, sys.exc_info()[ 1 ]


		#cleanup any generated objects
		self._cleanup()


		#if the file wasn't in perforce add it now
		if not inP4:
			if not exportPathP4.add():
				api.melWarning("could not open %s for add - you'll have to do it manually" % exportPath)


		#execute post export MEL command
		self._executePost()


		return exportPath
	def _buildExportCommandStr( self, cleanup=True ):
		'''
		builds the export command string - the string is a mel command...
        '''
		extension = self.getExtension()
		exportPath = self.getExportPath()
		extraFlags = self.getAttr('flags')
		upAxis = self.getAttr('upAxis')

		#if the asset object is a set, then collapse it into a list of objects.  also make
		#sure it has vExportNode label
		if cmd.nodeType(self.getObj()) == "objectSet":
			cmd.sets(self.getObj(), e=True, text='vExportNode')

		#so if the asset type is a camera, we assume its animated and need to specify
		#the -exportType animation flag explicitly
		type = self.getAttr('type')
		if type == self.kCAMERA:
			extraFlags += " -exportType animation"

		#deal with special cases...
		if type == self.kVMF:
			return "python(\"import exportManagerCore; exportManagerCore.updateVmf(%s, '%s')\");" % (self.slot, self.node)
		elif type == self.kHITBOX:
			return "python(\"import exportManagerCore; exportManagerCore.generateHitboxFile(%s,'%s')\");" % (self.slot, self.node)
		elif type == self.kVRD:
			return 'vstHelperBone -e -filename "%s"' % self.getExportPath()
		elif type == self.kVTA:
			objs = self._generateExportObjs()
			return 'vstsmdio -e -et v -up %s -f "%s" -sl %s' % (upAxis, self.getExportPath(), " ".join(objs))

		exportCmdToks = ["vsDmxIO -selection -export"]
		xPrefix = self.getAttr('exportPrefix')
		if xPrefix:
			exportCmdToks.append(' -nodePrefix "%s"' % xPrefix)

		exportCmdToks.append('-exportType "%s"' % type)
		exportCmdToks.append("-frameStart %s" % self.getAttr('start'))
		exportCmdToks.append("-frameEnd %s" % self.getAttr('end'))

		excludeList = self.getAttr( 'excludeList' )
		if excludeList:
			exportCmdToks.append( ' '.join( [ '-ex '+ x for x in excludeList ] ) )

		xRelative = self.getAttr('exportRelative')
		if cmd.objExists(xRelative):
			exportCmdToks.append("-exportRelative %s" % xRelative)

		exportCmdToks.append('-filename "%s"' % exportPath)
		exportCmdToks.append(extraFlags)

		objs = self._generateExportObjs()
		exportCmdToks.append(" ".join(objs))
		if cleanup: self._cleanup()

		return " ".join(exportCmdToks)
	def _setShowState( self, state=True ):
		visPanels = cmd.getPanel(vis=True)
		xman = ExportManager(self.node)

		#first turn the isolateSelect off for all panels
		for p in visPanels:
			if cmd.getPanel( to=p ) == 'modelPanel':
				cmd.isolateSelect( p, state=False )
				xman._isolatedSlot = ExportManager.kVIS_STATE_OFF

		#delete any existing selection connection object
		if cmd.selectionConnection( ExportManager.kASSET_ISO_SET_NAME, ex=True ):
			cmd.deleteUI( ExportManager.kASSET_ISO_SET_NAME )

		#now if we're turning the state on - do it and add all appropriate objects
		if state:
			xman._isolatedSlot = self.slot

			cmd.selectionConnection( ExportManager.kASSET_ISO_SET_NAME )
			items = self._getExportItems()
			for mesh, items in items.iteritems():
				if items is not None:
					items = ['%s.%s' % (mesh, i) for i in items]
					[ cmd.selectionConnection( ExportManager.kASSET_ISO_SET_NAME, e=True, s=i ) for i in items ]
				else:
					cmd.selectionConnection( ExportManager.kASSET_ISO_SET_NAME, e=True, s=mesh )
			for p in visPanels:
				if cmd.getPanel(to=p) == 'modelPanel':
					cmd.modelEditor( p, e=True, vs=True, mlc=ExportManager.kASSET_ISO_SET_NAME )

		#do a preview of anim layers as well
		if state:
			self._animLayerPreShowMuteStates = {}
			for l in cmd.ls( typ='animLayer' ):
				self._animLayerPreShowMuteStates[ l ] = cmd.animLayer( l, q=True, mute=True )

			animLayers = self.getAttr( 'animLayers' )
			for animLayer in cmd.ls( typ='animLayer' ):
				if animLayer in animLayers: cmd.animLayer( animLayer, e=True, mute=False, selected=True )
				else: cmd.animLayer( animLayer, e=True, mute=True, selected=False )
		else:
			for l, muteState in self._animLayerPreShowMuteStates.iteritems():
				cmd.animLayer( l, e=True, mute=muteState )

		cmd.animLayer( forceUIRefresh=True )
	def _getShowState( self ):
		visPanels = cmd.getPanel(vis=True)
		xman = ExportManager(self.node)

		if self.slot == xman._isolatedSlot:
			for p in visPanels:
				if cmd.getPanel(to=p) == 'modelPanel':
					return cmd.isolateSelect(p, q=True, state=True)

		return False
	def _getExportItems( self ):
		#this dict will track the faces associated with each object in the shader assignment
		objs = {}

		#grab any shaders in the export list - we need to do this first
		shadingGroups = []
		try:
			if cmd.nodeType( self.getObj() ) == 'transform':
				raise TypeError

			shadingGroups = [cmd.listConnections(mat, s=0, type='shadingEngine')[0] for mat in cmd.ls(self.getObjs(), type=('lambert'))]
			shadingGroups += cmd.ls(cmd.sets(self.getObj(), q=True), type=('shadingEngine'))
		except TypeError: pass

		for grp in shadingGroups:
			faces = cmd.sets(grp, q=True)
			if faces:
				for f in faces:
					obj, face = f.split('.')
					try: objs[obj].append(face)
					except KeyError: objs[obj] = [face]

		meshes = []
		try: meshes = [v for v in cmd.listRelatives(cmd.listRelatives(self.getObjs(), s=True, type='mesh'), p=True)]
		except TypeError: pass
		for mesh, faces in objs.iteritems():
			meshes.extend( ['%s.%s' % (mesh, f) for f in faces] )

		meshes = set(meshes)

		#now see if there are any volumes in the export set
		volumes = set()
		for obj in self.getObjs():
			try:
				shapes = cmd.listRelatives(obj, s=True, type='nurbsSurface')
				if not shapes: continue
				if cmd.objExists('%s.exportVolume' % obj):
					volumes.add(obj)
			except TypeError: continue
		if len(volumes):
			'''
			so if we have volumes, then ONLY faces contained within the volumes are exported
			'''
			for vol in volumes:
				meshFacesWithin = findFacesInVolume(meshes, vol)
				for mesh, faces in meshFacesWithin.iteritems():
					try: objs[mesh] += faces
					except KeyError: objs[mesh] = faces

		for obj in self.objs:
			objs.setdefault(obj)
		for item in volumes:
			objs.pop(item)

		return objs
	def _generateExportObjs( self ):
		'''
		generates all non-real objects for an asset - so if a user has added a shading group or a material to an
		export set, then this needs to get translated into geometry - which means the creation of an intermediate
		object which gets created at export-time and deleted once exporting has finished.  other meta-objects
		include bounding objects which define geometry by volume to be included in an export
        '''
		objs = self._getExportItems()

		#now duplicate the object, delete unwanted faces and make a record of the newly created object so we can delete it later
		generated = self._generated
		toExport = []
		for obj, faces in objs.iteritems():
			if faces is None:
				toExport.append(obj)
				continue

			dupe = cmd.duplicate(obj)[0]
			cmd.select('%s.f[*]' % dupe)
			newFaces = ['%s.%s' % (dupe, f) for f in faces]
			cmd.select(newFaces, d=True)
			cmd.delete()
			generated.append(dupe)
			toExport.append(dupe)

			#does teh original object have skinning info?
			try:
				influences = cmd.skinCluster(obj, q=True, inf=True)
				cmd.skinCluster(dupe, influences)
				cmd.select(obj, dupe)
				cmd.copySkinWeights(noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='oneToOne')  #closestJoint
			except RuntimeError:
				#if we get an exception here, the object isn't skinned...
				pass

		return toExport
	def _cleanup( self ):
		try:
			for obj in self._generated:
				cmd.delete(obj)
		except (RuntimeError, TypeError): pass
		finally: self._generated = []
	def _execute( self, attr ):
		cmd = self.getResolvedAttr(attr)
		if cmd:
			try: return mel.eval(cmd)
			except:
				api.melError("%s-execution failed for slot %s" % (attr, self.slot))
				return
	def _executePre( self ):
		return self._execute('preMEL')
	def _executePost( self ):
		return self._execute('postMEL')
	def getExportPath( self ):
		'''
		returns the value of the export path for a given slot.  NOTE: takes into account an asset's export
		path, or falls back to the global export path if one isn't present, and appends the asset name.  this
		means the return value will be sans extension and potentially unresolved.  resolvedExportPath() handles
		resolution and extensions
        '''
		exportMan = ExportManager(self.node)
		componentPath = self.getAttr('path')
		globalPath = exportMan.getAttr('path')
		prefix = exportMan.getAttr('prefix')
		assetType = self.getAttr('type')

		exportPath = globalPath if not componentPath else componentPath

		#if the component doesn't have a path set, grab the default path for the asset type - most of these
		#paths are defined in the modelpipeline module by the various component class interfaces
		if not exportPath:
			if assetType == self.kMODEL:
				loc = mp.getDefaultDataLocationsByExtension( mp.ComponentInterface_model.EXTENSION )
				if isinstance( loc, (tuple, list) ): loc = loc[ 0 ]
				exportPath = getAssetRoot() / loc
			elif assetType == self.kANIM:
				loc = mp.getDefaultDataLocationsByExtension( mp.ComponentInterface_animation.EXTENSION )
				if isinstance( loc, (tuple, list) ): loc = loc[ 0 ]
				exportPath = getAssetRoot() / loc
			elif assetType == self.kHITBOX:
				#hitbox assets are actually component class scripts...  so just return the path to the script
				loc, name = getAssetRootAndName()
				hitboxComponentScript = mp.ComponentInterface_hitbox.ComponentFilepath( loc, name )

				return hitboxComponentScript
			elif assetType == self.kPHYSICS:
				loc = mp.getDefaultDataLocationsByExtension( mp.ComponentInterface_physics.EXTENSION )
				if isinstance( loc, (tuple, list) ): loc = loc[ 0 ]
				exportPath = getAssetRoot() / loc
			elif assetType == self.kVRD or assetType == self.kVTA:
				exportPath = getAssetRoot()
			else:
				exportPath = mp.BaseComponentInterface.DataLocations( *getAssetRootAndName() )[ 0 ]

		if componentPath:
			prefix = ''

		exportPath = Path( exportPath )
		filename = '%s%s' % (prefix, self.getAttr('name'))
		filepath = exportPath / filename
		xtn = self.getExtension()

		filepath = filepath.setExtension( xtn )

		return filepath
	def getExtension( self ):
		'''
		convenience method to return the extension for the instances export file
        '''
		return self.EXTENSIONS.get(self.getAttr('type'), self.DEFAULT_EXTENSION)
	def delete( self ):
		'''
		deletes the current asset
        '''
		attrs = self.lsAttr()

		assetAttrname = self.kASSET_FORMAT % self.slot
		assetAttrpath = '%s.%s' % (self.node, assetAttrname)
		if not cmd.objExists(assetAttrpath):
			api.melWarning("no asset existed at slot %d" % self.slot)

		cmd.deleteAttr(assetAttrpath)

		for attr in attrs:
			attrname = self.kATTR_FORMAT % (self.slot, attr)
			attrpath = '%s.%s' % (self.node, attrname)
			if cmd.objExists(attrpath):
				cmd.deleteAttr(attrpath)
	def copyFrom( self, other ):
		'''
		copies all attributes from another asset
        '''
		if isinstance(other, int):
			other = ExportComponent(other)

		assert isinstance(other, ExportComponent)

		#delete all existing attributes
		attrsToDel = set(self.lsAttr()) - self.NO_DEFAULT_ATTRS
		for attr in attrsToDel:
			self.delAttr(attr)

		otherAttrs = other.lsAttr()
		for attr in otherAttrs:
			self.setAttr(attr, other.getAttr(attr))
	def duplicate( self ):
		newAsset = ExportManager().createAsset( self.getObj() )
		newAsset.copyFrom( self )

		return newAsset


class CompileScript(Path):
	'''
	'''
	TYPES = VCOMPILE, QC, CMD, BAT , ROOT = 0, 1, 2, 3, 4
	_type = None
	def __init__( self, cmdStr, type=None ):
		Path.__init__(self, cmdStr)

		#determine the type if none has been specified
		if type is None:
			if self.getExtension() == '':
				self._type = self.VCOMPILE
			elif self.hasExtension( 'qc' ):
				self._type = self.QC
			elif self.hasExtension( 'cmd' ):
				self._type = self.CMD
			elif self.hasExtension( 'bat' ):
				self._type = self.BAT
			elif self.hasExtension( 'root' ):
				self._type = self.ROOT
	def getType( self ):
		return self._type
	def isValid( self ):
		'''
		returns whether the compile script is valid or not
		'''
		if self._type is None:
			return False

		if self._type == self.VCOMPILE:
			return True

		if self._type in self.TYPES:
			return self.exists()

		return False
	def exists( self ):
		if self._type == self.VCOMPILE:
			return True

		return Path.doesExist( self )
	def getAssetLocationAndName( self ):
		'''
		if this is a VCOMPILE script, this method will return the location and name for the asset being compiled by the vcompile cmd
		'''
		if self._type == self.VCOMPILE:
			res = self.resolve()
			return res.up(), res.name()
	def getAsset( self ):
		'''
		if this is a VCOMPILE script, this method will return the Asset instance being compiled by this script
		'''
		if self._type == self.VCOMPILE:
			return mp.Asset( *self.getAssetLocationAndName() )
	def getScriptPath( self ):
		'''
		returns the actual fullpath to the compile script.
		NOTE: this is meaningless for vcompile scripts
		'''
		if self.isUnder( content() ):
			return self

		return content() / self
	def isLatest( self ):
		'''
		returns whether the compile script is the latest version or not
		'''
		if self._type == self.VCOMPILE:
			return self.getAsset().isLatest( True )
		else:
			return self.getScriptPath().asP4().isLatest()
	def getDependencies( self ):
		if self._type == self.VCOMPILE:
			asset = self.getAsset()
			return asset.listAllFiles()
		elif self._type == self.QC:
			return qcTools.getQcIncludes( self.getScriptPath() )

		return []
	def add( self, type=None ):
		'''
		deals with adding teh compile script to perforce
		'''
		if self._type == self.VCOMPILE:
			return

		if self.asP4().isUnderClient():
			Path.add( self )
	def compile( self ):
		pass
	def getCompileCmd( self ):
		'''
		returns a command that can be added to a process queue
		'''
		if self._type == self.VCOMPILE:
			loc, name = self.getAssetLocationAndName()
			return 'vcompile.cmd -compile %s %s' % (loc, name), str( loc.resolve() )
		if self._type == self.QC:
			return 'studiomdl.bat %s' % self.getScriptPath().resolve(), self.getScriptPath().up().resolve()
		elif self._type == self.ROOT:
			myAsset = mp.Asset.FromComponentScript ( self )
			loc = myAsset.location()
			name = myAsset.name()
			return 'vcompile.cmd -compile %s %s' % (loc, name), str( loc.resolve() )
		elif self._type in [self.CMD, self.BAT]:
			return self.getScriptPath().resolve(), self.getScriptPath().up().resolve()




def updateRagdoll( slot ):
	exportManager = ExportManager()
	exportComponent = exportManager[ slot ]
	objs = exportComponent.getObjs()
	children = cmd.listRelatives( objs, ad=True, pa=True )

	try:
		children += objs
	except TypeError: children = objs

	joints = cmd.ls( children, type='joint' )

	if not joints:
		return

	#clear the existing joint constrain values
	asset = exportManager.getAsset()
	# check it out
	assetPath = asset.phys.path()
	assetPath.edit()
	asset.physics.clearJointConstrains()

	for j in joints:
		for axis in asset.phys.ALL_AXES:
			try:
				kw = {'q': True, 'er%s' % axis.lower(): True}
				enabledMin, enabledMax = cmd.transformLimits(j, **kw)
				jClean = j.split( '|' )[ -1 ]
				if enabledMin and enabledMax:
					#grab constrain limits
					kw = {'q': True, 'r%s' % axis.lower(): True}
					min, max = cmd.transformLimits(j, **kw)
					asset.phys.setJointConstrainLimits( jClean, axis, min, max )

					#grab friction
					friction = cmd.getAttr( '%s.stiffness%s' % (j, axis.upper()) )
					asset.phys.setJointConstrainAttr( jClean, axis, 'friction', friction )
				else:
					asset.phys.setJointConstrainAttr( jClean, axis, 'type', asset.phys.FIXED )
			except RuntimeError:
				print 'bad'
				continue

	print asset, 'is applicable', asset.phys.isApplicable()
	asset.phys.write()
	asset.unload()


def getAssociatedInfoNodes( obj ):
	'''
	returns the name of any info nodes associated with the given object.  so if an object lives under an info node
	'''
	#so now what we want to do is grab any info nodes "associated" with the export object
	#and apply any defaults they have set as explicit attribute data to this new asset.  so
	#for example, in a character's model file (or _reference file) you have default attribute
	#data set on its export info node, that default attribute data will be used as the value
	#for those attributes on this asset
	allParents = []
	allChildren = cmd.listRelatives(obj, pa=True, ad=True)
	newParents = cmd.listRelatives(obj, pa=True, p=True)
	n = 0

	#listRelatives returns None if the criteria doesn't match
	if allChildren is None:
		allChildren = []

	#find all parents
	while newParents is not None and n<150:
		allParents += newParents
		newParents = cmd.listRelatives(newParents, pa=True, p=True)
		n += 1

	#
	infoNodes = cmd.ls([obj] + allParents + allChildren, type=AnExportManager.kASSET_NODE_TYPE)
	infoNodes = utils.removeDupes( infoNodes )

	return infoNodes


def isNodeValid( node ):
	'''
	given a node name, this method returns whether its a valid export manager node or not...
	'''
	if node is None: return False
	if not cmd.objExists( node ): return False
	if cmd.nodeType( node ) != AnExportManager.kASSET_NODE_TYPE: return False
	if cmd.referenceQuery(node, inr=True): return False

	return True


def d_validateNode(f):
	'''
	decorator for ensuring an export_data node exists in the scene
    '''
	def dec(*args, **kwargs):
		self = args[0]
		if self.node is None:
			node = ExportManager.CreateAssetNode()
			self.update()
		elif not cmd.objExists(self.node):
			self.getNode(True)

		return f(*args, **kwargs)
	return dec


class AnExportManager(object):
	'''
    '''
	kATTR_FORMAT = "global%s"       #takes attr as the arg
	kDEFAULT_ATTR_FORMAT = "_%s_default"   #takes attr as the arg
	kEXPORT_SET_TOP = 'vExportSetTop'
	kEXPORT_SET = 'vExportSet'
	COMPILE_PREFIX = 'global_compileScript'
	COMPILE_EXTENSIONS = ['cmd', 'qc', 'py', 'bat', 'root' ]
	kASSET_NODE_TYPE = 'vstInfo'
	kVIS_STATE_OFF = -1
	kASSET_ISO_SET_NAME = 'exportSetVis'
	kVOLUME_SPHERE = 0
	kVOLUME_CUBE = 1
	_isolatedSlot = kVIS_STATE_OFF

	### define some order modes - different ways of ordering assets
	ORDER_MODES = ordID, ordNAME, ordSUFFIX, ordTYPE, ordSTART = 0, 1, 2, 3, 4
	__ORDER_METHODS = {ordID: lambda asset: asset.slot,
					   ordNAME: lambda asset: asset.getAttr('name'),
					   ordSUFFIX: lambda asset: asset.getAttr('name').split('_')[-1],
					   ordTYPE: lambda asset: asset.getAttr('type'),
					   ordSTART: lambda asset: asset.getAttr('start')}

	### define attribute defaults
	ATTR_DEFAULTS = {'path': '',
					 'fullNames': 0,
					 'showQC': 1,
					 'showCmd': 1,
					 'showBat': 1,
					 'showRoot': 1,
					 'orderMode': ordID,

					 ###the following attributes are used primarily by the model compiler tool
					 'surfaceprop': 'default',
					 'staticprop': 1,
					 'nophysics': 0,
					 'automass': 1,
					 'concave': 1,
					 'usemodel': 0,
					 'LOD1': 10.0,
					 'LOD2': 20.0,
					 'LOD3': 30.0,
					 'LOD4': 40.0,
					 'LOD5': 50.0,
					 'mass': 50.0}

	### used to define attribute variable types - defaults to string as thats how all data is stored
	ATTR_TYPE_CONVERSIONS = {'fullNames': int,
							 'path': Path,
							 'orderMode': int,
							 'staticprop': int,
							 'nophysics': int,
							 'automass': int,
							 'concave': int,
							 'usemodel': int,
							 'LOD1': float,
							 'LOD2': float,
							 'LOD3': float,
							 'LOD4': float,
							 'LOD5': float,
							 'mass': float}
	def __init__( self, node=None ):
		if node is None or not cmd.objExists(node):
			node = self.getNode()

		self.node = node
		self._compileScripts = None
		if node is None: return

		#populate the slots
		self.ls()

		#deal with older asset data
		oldCompileCmdPath = '%s.globalcompileCmd' % self.node
		if cmd.objExists(oldCompileCmdPath):
			oldScript = cmd.getAttr(oldCompileCmdPath)
			cmd.deleteAttr(oldCompileCmdPath)
			self.setCompileScript(oldScript)

		scriptSlots = self.listCompileSlots()
		if not len(scriptSlots):
			self.createCompileScript()
	def __iter__( self ):
		return iter(self.ls())
	def __str__( self ):
		return self.node
	__repr__ = __str__
	def __getitem__( self, slot ):
		'''
		returns an ExportComponent instance for the given slot
        '''
		newAsset = ExportComponent(slot, self.node)
		return newAsset
	def __len__( self ):
		return len( self.ls() )
	def getSlotDict( self ):
		slots = {}
		for a in self:
			slots[a.slot] = a

		return slots
	slots = property(getSlotDict)
	def setNode( self, node ):
		'''
		sets the current instance to look at a different export manager node in the scene
        '''
		if cmd.objExists(node):
			self.node = node
			self._compileScripts = None
		else:
			msg = "the specified node doesn't exist"
			api.melError(msg)
			raise ExportManagerException(msg)

		return node
	def getNode( self, forceCreate=False ):
		'''
		returns the export manager node for the current scene.  this should only be called when
		this instance's .node attribute no longer exists.  it is rare that this method needs to
		be called directly - instead use .update()
        '''
		nodes = self.__class__.GetAssetNodes(forceCreate)

		#iterate through the nodes and return the first non-referenced one
		refNodesInScene = False
		for node in nodes:
			if not cmd.referenceQuery(node, inr=True):
				return node
			else:
				refNodesInScene = True

		if refNodesInScene and forceCreate:
			node = self.__class__.CreateAssetNode()
			return node

		return None
	def update( self, forceUpdate=False ):
		'''
		used to update the scene node the instance points to when the scene changes
        '''
		#reset cache attributes
		self._compileScripts = None

		#is the current node a valid node?  if not, set the current node attribute to None...
		if isNodeValid( self.node ):
			return
		else: self.node = None

		#try to find a valid node to use, and point the instance node attribute to it
		node = self.getNode(forceUpdate)
		if node is not None:
			self.setNode(node)
	def	isManaged( self ):
		'''
		returns a bool indicating whether there is a currently active export manager node in the scene
        '''
		if self.node is not None:
			return cmd.objExists(self.node)

		return False
	@classmethod
	def Create( cls ):
		'''
		creates a new export node
        '''
		return cls( cls.CreateAssetNode() )
	@staticmethod
	def GetAssetNodes( forceCreate=False, **kwargs ):
		'''
		returns a list of asset nodes in the scene - and optionally creates one if none exist
        '''
		nodes = ExportManager.GetExistingAssetNodes()

		if not nodes and forceCreate:
			newNode = ExportManager.CreateAssetNode()
			nodes.append(newNode)

		return nodes
	@staticmethod
	def GetExistingAssetNodes( **kwargs ):
		'''
		lists all asset nodes in the scene
		NOTE: referenced nodes are excluded based on a user pref...
        '''
		listAll = kwargs.get('listAll', cmd.optionVar(q='listAllAssetNodes'))

		nodes = cmd.ls(type='vstInfo')
		nodesToShow = []

		if listAll: nodesToShow = nodes
		else:
			nodesToShow = [n for n in nodes if not cmd.referenceQuery(n, inr=True)]

		return nodesToShow
	@staticmethod
	def SetListAll( state ):
		'''
		sets the list all state - ie whether to include referenced nodes when listing export manager nodes
		'''
		state = bool(state)
		cmd.optionVar(iv=('listAllAssetNodes', state))
	@staticmethod
	def GetListAll():
		'''
		returns whether all nodes are being listed or not
        '''
		return cmd.optionVar(q='listAllAssetNodes')
	@staticmethod
	def CreateAssetNode():
		'''
		creates a new export manager node - the node name is returned
        '''
		#creating nodes de-selects current, so store current selection so we can restore afterwards
		selObjs = cmd.ls(sl=True)

		nodes = cmd.ls(type=AnExportManager.kASSET_NODE_TYPE)
		node = cmd.createNode(AnExportManager.kASSET_NODE_TYPE)

		node = cmd.rename(node, "export_data#")
		cmd.addAttr(node, ln='zooAssetNode', at='bool')
		asExportNode = AnExportManager(node)
		asExportNode.setAttr('creator', os.environ['USER'])
		mel.zooAttrState("-attrs s v -k 0 -l 1", node)

		#restore selection
		if selObjs: cmd.select(selObjs, ne=True)

		return node
	@classmethod
	def GetDefault( cls, attr ):
		'''
		if no attr default is found in the ATTR_DEFAULTS dict, then return en empty string UNLESS the
		isInt flag is True, in which case 0 is returned...
        '''
		try:
			default = cls.ATTR_DEFAULTS[attr]
			try: return default()
			except TypeError: return default
		except KeyError:
			return DEFAULT_DEFAULT
	@classmethod
	def CreateExportSet( cls, objs=None ):
		'''
		creates an export set for a given list of object - if no list is passed, the selection is implied
        '''
		top = cls.GetExportSetTop()
		if objs is None:
			objs = cmd.ls(sl=True)

		#creates a set and adds all currently selected objects
		exportSet = cmd.sets(em=True)
		cmd.sets(exportSet, e=True, text=cls.kEXPORT_SET)

		if objs:
			exportSet = cmd.rename(exportSet, "%s_exportSet#" % objs[0])
		else:
			exportSet = cmd.rename(exportSet, "an_exportSet#")

		cmd.sets(objs, add=exportSet)
		cmd.sets(exportSet, add=top)

		return exportSet
	@classmethod
	def GetExportSetTop( cls ):
		existing = cmd.ls(type='objectSet')

		for set in existing:
			if cmd.sets(set, q=True, t=True) == cls.kEXPORT_SET_TOP:
				return set

		#so obviously the top export set doesn't exist - so create it
		topSet = cmd.sets(em=True)
		cmd.sets(topSet, e=True, text=cls.kEXPORT_SET_TOP)
		topSet = cmd.rename(topSet, "allExportSets#")

		return topSet
	def getAttr( self, attr ):
		default = self.GetDefault(attr)
		type_conv = self.ATTR_TYPE_CONVERSIONS.get(attr, DEFAULT_DEFAULT)

		attrname = self.kATTR_FORMAT % attr
		attrpath = '%s.%s' % (self.node, attrname)

		data = DEFAULT_DEFAULT
		if not cmd.objExists(attrpath): data = default
		else: data = cmd.getAttr(attrpath)

		try:
			data = type_conv(data)
		except TypeError: pass

		return data
	@d_validateNode
	def setAttr( self, attr, data ):
		default = self.GetDefault(attr)

		#try to type convert the data before setting it...
		type_conv = self.ATTR_TYPE_CONVERSIONS.get(attr, None)
		if type_conv is not None:
			data = type_conv(data)

		#this section is an optional formatting section - if you want strict formatting
		#of attr data, put in a case for the attr name, and proceed to format the data
		if attr == "prefix":
			data = api.validateAsMayaName(data)
		elif attr == "path":
			if data:
				data = Path(data).asdir() << '%VCONTENT%'

		attrname = self.kATTR_FORMAT % attr
		attrpath = '%s.%s' % (self.node, attrname)
		if not cmd.objExists(attrpath):
			cmd.addAttr(self.node, dt="string", ln=attrname)

		cmd.setAttr(attrpath, data, type="string")
	def ls( self ):
		'''
		lists all the assets being managed by this export node - the list is ordered by the value
		listed in the 'orderMode' attribute.  defaults to ordering by asset id
        '''
		assets = []
		try:
			allAttrs = cmd.listAttr(self.node, ud=True)
		except TypeError: return assets

		regEx = re.compile('^%s$' % (ExportComponent.kASSET_FORMAT % '([0-9]+)'))
		try:
			for attr in allAttrs:
				search = regEx.search(attr)
				if search is not None:
					slot = int( search.groups()[0] )
					asset = ExportComponent(slot, self.node)
					assets.append(asset)
		except TypeError: return assets

		#now do ordering
		orderMode = self.getAttr('orderMode')
		orderMethod = self.__ORDER_METHODS[orderMode]
		assets = [(orderMethod(a), a) for a in assets]
		assets.sort()
		assets = [a[1] for a in assets]

		return assets
	@d_validateNode
	def createExportComponent( self, obj ):
		'''
		creates a new export asset - obj can be a single object, or a list of objects to be
		managed by the export asset
        '''
		if isinstance(obj, (list, tuple)):
			obj = self.CreateExportSet(obj)

		slot = self.getAssetSlot()
		attrname = ExportComponent.kASSET_FORMAT % slot
		attrpath = '%s.%s' % (self.node, attrname)
		if not cmd.objExists(attrpath):
			cmd.addAttr(self.node, ln=attrname, at='message')

		asset = ExportComponent(slot, self.node)
		if obj: asset.setObj(obj)
		for attr in ExportComponent.NO_DEFAULT_ATTRS:
			asset.setAttr(attr, ExportComponent.GetDefault(attr, self.node))

		#determine the default name for the asset
		sceneNamePref = cmd.optionVar(q='assetsDefaultNameFromScene')
		defaultName = 'unnamed'
		if sceneNamePref:
			defaultName = Path( cmd.file(q=True, sn=True) )
			defaultName = defaultName.setExtension()[-1]
		else:
			defaultName = str(api.Name(asset.getObjs()[0]).short())

		asset.setAttr('name', defaultName)

		#if no obj was specified, then nothing to determine type from - so bail
		if obj is None: return asset
		objs = asset.getObjs()

		#figure out what the default type should be...  these are just guessing, but most of the
		#time teh guesses should be pretty accurate - ie anything with a camera shape
		objs = asset.getObjs()
		objToDetermineType = objs[0]
		foundType = False

		try:
			if not cmd.objExists(objToDetermineType): raise ExportManagerException

			if cmd.referenceQuery(objToDetermineType, inr=True):
				asset.setAttr('type', ExportComponent.kANIM)
				raise BreakException

			#are any of the objects flagged as phys objects?  either in name, or with "hitboxes"?
			physRegex = re.compile('_phys([bB]ox)?[0-9]*$')
			for obj in objs:
				physName = physRegex.search(objToDetermineType)
				if physName is not None or cmd.objExists("%s.vHitbox" % objToDetermineType):
					asset.setAttr('type', ExportComponent.kPHYSICS)
					raise BreakException

			#do any of the objects have vmf import attributes?
			for obj in objs:
				if cmd.objExists("%s._id" % obj):
					#so we have a potential vmf candidate - try to find what vmf file the object belongs to - if none can be found, abort mission
					parents = cmd.listRelatives(objs, pa=True, p=True)
					while parents:
						for p in parents:
							if cmd.objExists("%s._filename" % p):
								vmfFile = cmd.getAttr("%s._filename" % p)
								vmfFile = Path(vmfFile)

								#great, so set it to be a vmf type asset - now we need to find what vmf file the object belongs to...
								asset.setAttr('type', ExportComponent.kVMF)
								asset.setAttr('path', vmfFile.up())
								asset.setAttr('name', vmfFile.name())
								raise BreakException
						parents = cmd.listRelatives(p, pa=True, p=True)

					#now bail
					raise BreakException

			#any cameras present?
			shapes = cmd.listRelatives(objToDetermineType, f=True, s=True)
			if shapes:
				if cmd.nodeType(shapes[0]) == "camera":
					asset.setAttr('type', ExportComponent.kCAMERA)
					asset.setAttr('name', '%s_cam' % asset.getAttr('name'))
					raise BreakException

			#finally if we haven't determined a type, default it to model
			asset.setAttr('type', ExportComponent.kMODEL)
		except BreakException:
			pass

		#get the list of associated info nodes, and copy any default attributes from said info nodes to the new export component
		infoNodes = getAssociatedInfoNodes( obj )

		#now list the attributes with defaults on them and set the new asset's attributes explicitly
		#to these values
		for infoNode in infoNodes:
			attrs = ExportComponent.ListAttrsWithSceneDefaults(infoNode)
			for attr in attrs:
				asset.setAttr(attr, ExportComponent.GetDefault(attr, infoNode, asset.slot))
				print "adding default value for attr", attr, "from", infoNode

		return asset
	createAsset = createExportComponent
	def getAssetSlot( self ):
		'''
		returns the next available asset slot index
        '''
		slotIdxs = [a.slot for a in self.ls()]
		slotIdxs.sort()

		try:
			return slotIdxs[-1]+1
		except IndexError:
			return 0
	def iterScripts( self ):
		slotScriptDict = {}
		for slot in self.listCompileSlots():
			slotScriptDict[slot] = self.getCompileScript(slot)

		return slotScriptDict.iteritems()
	def exists( self, **attrValueDict ):
		'''
		returns whether an asset with the attribute values given exists or not
        '''
		matches = []
		for asset in self.ls():
			noMatch = False
			for attr,value in attrValueDict.iteritems():
				if asset.getAttr(attr) != value:
					noMatch = True
					break
			if not noMatch: matches.append(asset)

		return matches
	def export( self, slots=None ):
		'''
		slots can be None: all assets are exported,
		list: all slots in the list are exported
		int: the specified asset is exported
        '''
		if slots is None:
			for asset in self.ls():
				asset.export()
		elif isinstance(slots, (list,tuple)):
			for slot in slots:
				self[slot].export()
		elif isinstance(slots, int):
			self[slots].export()
	def listCompileScripts( self ):
		'''
		lists all compile scripts as Path instances for this export node
		'''
		prefix = self.COMPILE_PREFIX
		slots = self.listCompileSlots()
		compileScripts = []

		for slot in slots:
			script = cmd.getAttr('%s.%s%d' % (self.node, prefix, slot))
			compileScripts.append( CompileScript( script ) )

		return compileScripts
	def listCompileSlots( self ):
		'''
		returns a list of ints representing the compile script slots currently present on the export manager node
		'''
		slots = []

		#if no node exists, return an empty list
		if self.node is None:
			return slots

		prefix = self.COMPILE_PREFIX
		prefixLen = len(prefix)
		udAttrs = cmd.listAttr(self.node, ud=True)
		if udAttrs is not None:
			slots = [int( attr[prefixLen:] ) for attr in udAttrs if attr.startswith( prefix )]
			slots.sort()

		return slots
	@d_validateNode
	def createCompileScript( self, slot=None ):
		'''
		'''
		prefix = self.COMPILE_PREFIX
		if slot is None:
			slot = self.getCompileScriptSlot()

		fullpath = '%s.%s%d' % (self.node, prefix, slot)
		if not cmd.objExists(fullpath): cmd.addAttr(self.node, ln='%s%d' % (prefix, slot), dt='string')

		return slot
	def getCompileScriptSlot( self ):
		'''
        returns the next slot id for compileScripts
        '''
		attrs = self.listCompileSlots()

		if len(attrs): return attrs[-1]+1
		return 0
	@d_validateNode
	def setCompileScript( self, script, slot=None ):
		'''
		sets the compile script for a given slot - if slot is None, then a new slot is created.  the slot number
		is returned for the slot regardless...
		'''
		prefix = self.COMPILE_PREFIX
		if slot is None:
			slot = self.createCompileScript()

		fullpath = '%s.%s%d' % (self.node, prefix, slot)
		if script is None:
			script = ''

		if script:
			script = Path(script) - content()
			cmd.setAttr(fullpath, str(script), type='string')

		return slot
	def getCompileScript( self, slot ):
		'''
		returns the value of a given compileScript slot
		'''
		try:
			cmdText = cmd.getAttr('%s.%s%s' % (self.node, self.COMPILE_PREFIX, slot))
		except TypeError:
			return CompileScript('')

		if not cmdText:
			return CompileScript('')

		return CompileScript( content() / cmdText )
	def deleteCompileScript( self, slot ):
		try: cmd.deleteAttr('%s.%s%d' % (self.node, self.COMPILE_PREFIX, slot))
		except RuntimeError: pass
	def getAsset( self ):
		'''
		returns the modelpipeline Asset instance for the asset defined by this scene
		'''
		return mp.Asset( forceLoad=True, *getAssetRootAndName() )
	def compile( self, slot=None ):
		'''
		defaults to compiling ALL compile scripts
		'''
		import maya.utils
		def postGatherCmd():
			maya.utils.executeDeferred( gatherSceneDependenciesIntoChange )
		pq = utils.ProcessQueue( postGatherCmd )
		compileScripts = self.listCompileScripts() if slot is None else [self.getCompileScript(slot)]

		for script in compileScripts:
			assert isinstance( script, CompileScript )

			#if the script isn't in perforce, add it...
			script.add()

			### do some checks to make sure the compile script is up to date, is checked in
			buttons = ansA, ansB, ansC = "Compile Anyway", "Sync First", "Cancel"
			staleDeps = findStaleFiles( script.getDependencies() )
			if staleDeps:
				print 'THE FOLLOWING DEPENDENCIES ARE STALE'
				print '\n'.join( staleDeps )
				ans = cmd.confirmDialog(t="WARNING: stale deps", m="!! WARNING !!\nthe script you're trying to compile has the following out of sync dependencies:\n\n%s" % '\n'.join(map(str, staleDeps)), b=buttons, db=ansA)
				if ans == ansB:
					perforce.syncFiles( staleDeps )
				elif ans == ansC:
					return

			#if its NOT open and it ISNT in sync, then throw up a warning dialog...  just to let the user know
			if not script.isLatest():
				ans = cmd.confirmDialog(t="WARNING: stale compile script", m="!! WARNING !!\nthe compile script you're using isn't up to date", b=buttons, db=ansA)
				if ans == ansB:
					script.sync()
				elif ans == ansC:
					return

			pq.append( *script.getCompileCmd() )
		pq.start()
	def findPossibleCompileScripts( self ):
		'''
		lists all compile scripts available for a given asset
		'''
		if self._compileScripts is not None:
			print 'using cached list of compile scripts'
			return self._compileScripts

		extensions = set(self.COMPILE_EXTENSIONS[:])  #make a copy - coz we're about to modify it

		#remove any extensions the user wants filtered...
		if not self.getAttr('showCmd'):
			try: extensions.remove('cmd')
			except ValueError: pass
		if not self.getAttr('showQC'):
			try: extensions.remove('qc')
			except ValueError: pass
		if not self.getAttr('showBat'):
			try: extensions.remove('bat')
			except ValueError: pass
		if not self.getAttr('showRoot'):
			try: extensions.remove('root')
			except ValueError: pass

		#
		root, name = getAssetRootAndName()
		if root is not None:
			files = [ f for f in root.files(recursive=True) if f.extension in extensions ]

			try: mp.detectAssetsInLocation
			except AttributeError: fromAssets = []
			else: fromAssets = [ (root / mp.ComponentInterface_common.COMPONENT_SCRIPT_LOCATION / assetName).setExtension( mp.ComponentInterface_common.EXTENSION ) for assetName in mp.detectAssetsInLocation( root ) ]

			#now order all the scripts by script name
			self._compileScripts = removeDupes( [ f[ 1 ] for f in sorted( [ (f.name(), f) for f in files + fromAssets ] ) ] )

			return self._compileScripts

		self._compileScripts = []
		return self._compileScripts
	def refresh( self ):
		self._compileScripts = None
		self.findPossibleCompileScripts()
		self.ls()
	def writeBasicQc( self, selectedComponents=None, customName=None ):
		'''
		takes the current asset state and tries to best create a prop .qc file for the scene
		it takes into account LODs, multiple sequences, physicsModel and various small fry
		settings like staticprop etc...
		'''
		root, name = getAssetRootAndName()
		if root is None:
			raise ExportManagerException("no asset root can be determined - perhaps your project's asset structure isn't configured?", show=True)

		if customName is not None:
			name = customName

		assetList = self.ls()
		if selectedComponents is not None:
			assetList = selectedComponents

		qcFilepath = ( root/name ).setExtension('qc')
		mdlName = qcFilepath.asMdl().setExtension('mdl')

		#if teh qc file already exists - throw up a dial to warn
		if qcFilepath.exists:
			ANSWERS = YES, NO = 'Yes', 'No'
			ans = cmd.confirmDialog(t='sure you want to overwrite?!', m='The .qc file "%s" already exists\n\nAre you sure you want to overwrite it?' % qcFilepath, b=ANSWERS, db=YES)
			if ans == NO:
				print 'qc writing aborted by user'
				return None

		qcDirpath = qcFilepath.up()

		#automatically set types based on suffix:
		for asset in assetList:
			assetName = ( asset.getExportPath() - qcDirpath ).setExtension()
			for suffix in mp.ComponentInterface_model.SUFFIXES:
				if ( str( assetName ).rfind( suffix ) != -1 ):
					asset.setAttr( 'type', ExportComponent.kMODEL )
					break
			for suffix in mp.ComponentInterface_physics.SUFFIXES:
				if ( str( assetName ).rfind( suffix ) != -1 ):
					asset.setAttr( 'type', ExportComponent.kPHYSICS )
					break

		#get the model items
		modelAsset = None
		for asset in assetList:
			if asset.getAttr('type') == ExportComponent.kMODEL:
				modelAsset = ( asset.getExportPath() - qcDirpath ).setExtension('dmx')
				break

		#so are there physics items in the scene?  if so, grab them, and make them relative to the qcpath
		physicsAsset = None
		for asset in assetList:
			if asset.getAttr('type') == ExportComponent.kPHYSICS:
				physicsAsset = ( asset.getExportPath() - qcDirpath ).setExtension('dmx')
				break

		usemodel = int(self.getAttr('usemodel'))
		if usemodel:
			physicsAsset = modelAsset

		nophysics = int(self.getAttr('nophysics'))
		if nophysics:
			physicsAsset = None

		#see if there are any model assets that qualify as LODs
		LODs = []
		for asset in assetList:
			if asset.getAttr('type') == ExportComponent.kMODEL:
				name = asset.getAttr('name')
				if name[-4:-1] == 'LOD' and name[-1].isdigit():
					lodPath = (asset.getExportPath() - qcDirpath ).setExtension('dmx')
					lodMetric = self.getAttr('LOD%s' % (len(LODs)+1))
					LODs.append((lodPath, lodMetric))
			#todo: support naming conventions for automatically setting an object as an lod model

		#are there any animation assets?  if so, build the sequences for them
		animAssets = []
		fps = api.getFps()
		for asset in assetList:
			if asset.getAttr('type') == ExportComponent.kANIM:
				animAssets.append(( asset.getAttr('name'), ( asset.getExportPath() - qcDirpath ).setExtension('dmx'), fps ))
			#todo: support naming conventions for automatically setting an object as an animation asset

		#get some data from the node about qc properties to set
		automass = int(self.getAttr('automass'))
		concave = int(self.getAttr('concave'))
		surfaceprop = self.getAttr('surfaceprop')
		staticprop = int(self.getAttr('staticprop'))
		mass = self.getAttr('mass')
		if automass: mass = None
		if not surfaceprop: surfaceprop = 'metal'

		qcContentsStr = templateStrings.basicQC(mdlName, modelAsset, surfaceprop=surfaceprop, staticprop=staticprop, collisionmodel=physicsAsset, mass=mass, sequences=animAssets, concave=concave, LODs=LODs)
		qcFilepath.write(qcContentsStr)

		return qcFilepath


class ExportManager(utils.Singleton, AnExportManager):
	'''
	singleton version of the AnExportManager class
	'''
	def __init__( self, node=None ):
		AnExportManager.__init__(self, node)


def createExportVolume( type=ExportManager.kVOLUME_SPHERE ):
	newVolume = None
	if type == ExportManager.kVOLUME_SPHERE:
		newVolume = cmd.sphere(ax=(0,1,0), ch=False)[0]
	elif type == ExportManager.kVOLUME_CUBE:
		newVolume = cmd.cylinder(ax=(0, 1, 0), hr=1, d=1, s=4, ch=1)[0]
		mel.nurbsPrimitiveCap(3, 1, 0)
		cmd.setAttr('%s.sx' % newVolume, 0.707106781*2)
		cmd.setAttr('%s.sy' % newVolume, 2)
		cmd.setAttr('%s.sz' % newVolume, 0.707106781*2)
		cmd.setAttr('%s.ry' % newVolume, 45)
		cmd.makeIdentity(newVolume, a=1, r=1, s=1)
		cmd.delete(newVolume, ch=1)
	else:
		raise KeyError('volume type is not supported')

	newVolume = cmd.rename(newVolume, 'exportVolume#')
	newVolumeShape = cmd.listRelatives(newVolume, s=True, pa=True)[0]
	for chan in ('t','r','s'):
		for ax in ('x','y','z'):
			cmd.setAttr('%s.%s%s' % (newVolume, chan, ax), k=False, cb=True)
	cmd.setAttr('%s.v' % newVolume, k=False)
	cmd.addAttr(newVolume, ln='exportVolume', dt='string')
	cmd.setAttr('%s.exportVolume' % newVolume, type, type='string')

	#add trigger commands to preview selection
	asTrigger = triggered.Trigger.CreateMenu(newVolume, 'select face in volume', '''python "cmd.select(assets.findFacesInVolumeForMaya(set(cmd.ls(type='mesh')), '#'))";''')
	asTrigger.setMenuInfo(None, 'select verts in volume', '''python "cmd.select(assets.findVertsInVolumeForMaya(set(cmd.ls(type='mesh')), '#'))";''')
	asTrigger.killState = True

	return newVolume


def createHitbox( joint, minBounds, maxBounds ):
	'''
	given a parent, min bounds and max bounds, this will deal with the conversion to a maya
	representation of the hitbox
	'''
	if not cmd.objExists( joint ):
		print 'WARNING :: hitbox import - cannot find', joint, '- skipping'
		return None

	scaleX = maxBounds.x - minBounds.x
	scaleY = maxBounds.y - minBounds.y
	scaleZ = maxBounds.z - minBounds.z

	hbox = cmd.createNode( 'implicitBox' )
	hboxDag = cmd.listRelatives( hbox, p=True, pa=True )[ 0 ]

	cmd.setAttr( '%s.size' % hbox, 1, 1, 1 )
	cmd.setAttr( '%s.sx' % hboxDag, scaleX )
	cmd.setAttr( '%s.sy' % hboxDag, scaleY )
	cmd.setAttr( '%s.sz' % hboxDag, scaleZ )

	cmd.parent( hboxDag, joint, r=True )

	pos = (maxBounds.x + minBounds.x) / 2.0, (maxBounds.y + minBounds.y) / 2.0, (maxBounds.z + minBounds.z) / 2.0
	cmd.setAttr( '%s.t' % hboxDag, *pos )

	jPos = cmd.xform( joint, q=True, rp=True, ws=True )
	cmd.move( jPos[ 0 ], jPos[ 1 ], jPos[ 2 ], '%s.scalePivot' % hboxDag, '%s.rotatePivot' % hboxDag, a=True )


	### SETUP MAYA INTERFACE TO HITBOX ###

	#lock translate and rotate
	cmd.setAttr( '%s.t' % hboxDag, l=True )
	cmd.setAttr( '%s.r' % hboxDag, l=True )
	cmd.setAttr( '%s.v' % hboxDag, k=False, cb=False )

	cmd.addAttr( hbox, at='long', ln='vHboxGroup', min=0, dv=0 )
	cmd.setAttr( hbox +'.vHboxGroup', k=True)

	cmd.addAttr( hbox, at="enum", en= 'default:effects:bone:flesh:goo:fire:poison:blood:ice', ln='vHboxSet'  )
	cmd.setAttr( hbox +'.vHboxSet', k=True)

	hboxDag = cmd.rename(hboxDag, joint +'_vHitbox')

	return hboxDag


def importHitbox( asset ):
	'''
	imports the asset's hitbox script into the current scene - joints that aren't found in the scene
	are skipped
	'''
	set0 = asset.hitbox.root.hitboxSetList[ 0 ]
	for hitbox in set0.hitboxList:
		minB, maxB = hitbox.minBounds, hitbox.maxBounds
		createHitbox( hitbox.name, minB, maxB )


def createBoundForJoints( jointName=None, threshold=0.65 ):
	'''
	creates an implicitBox used for authoring hitboxes for objects/characters.  the script looks
	at the verts the given joint (or list of joints) and determines a local space (local to the first
	joint in the list if multiple are given) bounding box of the verts, and positions the hitbox
	accordingly
	'''
	if jointName is None: jointName = cmd.ls(sl=True)
	theJoint = jointName
	verts = []

	#so this is just to deal with the input arg being a tuple, list or string.  you can pass in a list
	#of joint names and the verts affected just get accumulated into a list, and the resulting bound
	#should be the inclusive bounding box for the given joints
	import skinCluster
	if isinstance( jointName, (tuple,list) ):
		theJoint = jointName[0]
		for joint in jointName:
			verts += skinCluster.jointVertsForMaya(joint, threshold)
	else:
		verts += skinCluster.jointVertsForMaya(jointName, threshold)

	jointDag = api.getMDagPath(theJoint)
	jointMatrix = jointDag.inclusiveMatrix()
	vJointPos = OpenMaya.MTransformationMatrix(jointMatrix).rotatePivot(OpenMaya.MSpace.kWorld) + OpenMaya.MTransformationMatrix(jointMatrix).getTranslation(OpenMaya.MSpace.kWorld)
	vJointPos = vectors.Vector( [vJointPos.x, vJointPos.y, vJointPos.z] )
	vJointBasisX = OpenMaya.MVector(-1,0,0) * jointMatrix
	vJointBasisY = OpenMaya.MVector(0,-1,0) * jointMatrix
	vJointBasisZ = OpenMaya.MVector(0,0,-1) * jointMatrix

	bbox = OpenMaya.MBoundingBox()
	for vert in verts:
		#get the position relative to the joint in question
		vPos = vectors.Vector( cmd.xform(vert, query=True, ws=True, t=True) )
		vPos = vJointPos - vPos

		#now transform the joint relative position into the coordinate space of that joint
		#we do this so we can get the width, height and depth of the bounds of the verts
		#in the space oriented along the joint
		vPosInJointSpace = mvectors.MayaVector(vPos.x, vPos.y, vPos.z)
		vPosInJointSpace.change_space(vJointBasisX, vJointBasisY, vJointBasisZ)
		bbox.expand( OpenMaya.MPoint( *vPosInJointSpace ) )

	minB, maxB = bbox.min(), bbox.max()

	return createHitbox( theJoint, minB, maxB )


def createBoundsForJoints( joint, threshold=0.65 ):
	hboxes = []
	for j in joints:
		hboxes.append( createBoundForJoints( j, threshold ) )

	return hboxes


def generateSkeletonHitboxes():
	'''
	define the "standard" set of joints to have hitboxes on them - we use these joints to derive
	bounding boxes based on the geo skinned to those objects
	'''
	hiboxJoints = [ ("Bip01_Pelvis",),
					("Bip01_Spine","Bip01_Spine1"),
					("Bip01_Spine2","Bip01_Spine4"),
					("Bip01_Head1",),
					("Bip01_L_UpperArm",),
					("Bip01_L_Forearm",),
					("Bip01_L_Hand","Bip01_L_Finger1","Bip01_L_Finger2","Bip01_L_Finger3","Bip01_L_Finger4","Bip01_L_Finger0"),
					("Bip01_R_UpperArm",),
					("Bip01_R_Forearm",),
					("Bip01_R_Hand","Bip01_R_Finger1","Bip01_R_Finger2","Bip01_R_Finger3","Bip01_R_Finger4","Bip01_R_Finger0"),
					("Bip01_L_Thigh",),
					("Bip01_L_Calf",),
					("Bip01_L_Foot",),
					("Bip01_R_Thigh",),
					("Bip01_R_Calf",),
					("Bip01_R_Foot",)]

	#now get a list of joint names in the current scene - we need to match the standard joints to these as joint
	#names are often slightly different for whatever reasons...
	hitboxes = []
	sceneJoints = cmd.ls(type='joint')
	for joints in hiboxJoints:
		matches = names.matchNames(joints,sceneJoints,parity=True,threshold=0.25)
		matches = [ match for match in matches if match!='' ]  #strip empty matches...
		if not len(matches):
			api.melWarning('no matches found for %s' % joints)
			continue

		hitboxes.append( createBoundForJoints(matches) )

	#finally, create an physicsModel asset for export - to do this, grab the skeleton node that has all the
	#hitboxes underneath
	parents = cmd.listRelatives(hitboxes, pa=True, p=True)
	parent = None
	while parents is not None:
		parent = parents[0]
		parents = cmd.listRelatives(parents,pa=True,p=True)

	asset = ExportManager().createAsset([parent])
	asset.setAttr('type', ExportComponent.kHITBOX)
	asset.setAttr('name', asset.getAttr('name') +'_hb')

	return hitboxes

def colorcodeHitboxes():
	'''
	go through all the hitboxes and color code them based on their hitbox set
	makes visualizing hitboxes sets in maya easier
	'''
	#get all the hitboxes
	hitboxShapes = cmd.ls( type='implicitBox' )
	hitboxes = cmd.listRelatives( hitboxShapes, pa=True, p=True )
	if hitboxes == None:
		print ( "There are no hitboxes in this scene" )
		return
	print ( "Color coding hitboxes" )
	# these colors match the hitbox set enum attr
	# default, effects, bone, flesh, goo, fire, poison, blood, ice
	colors = [1,5,7,10,15,20,23,4,29]
	hitboxColor = 0
	for n, hitbox in enumerate( hitboxes ):

		hbShapes = cmd.listRelatives(hitbox, s=True, type='implicitBox')
		for hbShape in hbShapes:
			if cmd.attributeQuery( 'vHboxSet', node=str(hbShape), ex=True ):
				hbSetName = cmd.getAttr(hbShape +'.vHboxSet', asString=True)
				if hbSetName == "":
					hitboxColor = 0
				else:
					hitboxColor = cmd.getAttr(hbShape +'.vHboxSet')
			else:
				hitboxColor = 0
			cmd.setAttr('%s.overrideEnabled' % hbShape, 1)
			cmd.setAttr('%s.overrideColor' % hbShape, colors[hitboxColor])


def generateHitboxFile( slot, node=None ):
	'''
	first grab a list of all the hitboxes associated with the current info node
	basically this just lists ALL objects in ALL export sets, and lists all hitbox
	objects in the heirarchy.  so it should grab all hitboxes associated with the
	export node
	'''
	exportComponent = AnExportManager( node )[slot]
	assert isinstance(exportComponent, ExportComponent)

	objects = exportComponent.getObjs()
	hitboxShapes = cmd.listRelatives( objects, pa=True, ad=True, type='implicitBox' )
	hitboxes = cmd.listRelatives( hitboxShapes, pa=True, p=True )
	if hitboxes == None:
		return

	theAsset = mp.Asset( *getAssetRootAndName() )
	script = theAsset.hitbox
	script.reset()  #this effectively clears the existing data (if any)

	#figure out all the sets first, default needs to always be first
	hbSets = ["default"]
	setIndex = 0
	for n, hitbox in enumerate( hitboxes ):
		hbShapes = cmd.listRelatives(hitbox, s=True, type='implicitBox')
		for hbShape in hbShapes:
			if cmd.attributeQuery( 'vHboxSet', node=str(hbShape), ex=True ):
				hbSetName = cmd.getAttr(hbShape +'.vHboxSet', asString=True)
				if hbSetName == "":
					#if there is no value make it the default
					newHbSet = "default";
				else:
					newHbSet = hbSetName;
			else:
				#if there is no attribute ( from old assets ) assume default
				newHbSet = "default";
			#only append it if it does not exist
			try:
				i = hbSets.index(newHbSet)
			except ValueError:
				i = -1 # no match
				hbSets.append( newHbSet )

	#make these sets
	script.createHitBoxSets ( hbSets )
	'''
	print ( "\nTOTAL MAYA HITBOX SETS = %i" % len (hbSets) )
	for hb in hbSets:
		print ( hb )
	print ("\n" )
	'''
	for n, hitbox in enumerate( hitboxes ):
		hbShapes = cmd.listRelatives(hitbox, s=True, type='implicitBox')
		for hbShape in hbShapes:
			if cmd.attributeQuery( 'vHboxGroup', node=str(hbShape), ex=True ):
				name = str( cmd.listRelatives(hitbox, p=True)[0] )
				hbGroupId = cmd.getAttr(hbShape +'.vHboxGroup')

				"""
				There's some weirdness with .spt stuff on drone so this isn't
				getting the right answer

				The right answer would be:

				hbMin = box.matrix * -( hbShape.size / 2 )
				hbMax = box.matrix *  ( hbShape.size / 2 )

				hbPos = vectors.Vector( cmd.getAttr( hitbox +".t" )[0] )
				hbHalfScale = vectors.Vector( cmd.getAttr( hitbox +".s" )[0] )/2
				hbMin = hbPos - hbHalfScale
				hbMax = hbPos + hbHalfScale
				"""
				# This is invalid if the node has children
				hbMin = vectors.Vector( cmd.getAttr( hitbox + ".bbmn" )[0] )
				hbMax = vectors.Vector( cmd.getAttr( hitbox + ".bbmx" )[0] )

				#figure out what set the hitbox belongs to
				if cmd.attributeQuery( 'vHboxSet', node=str(hbShape), ex=True ):
					hbSetName = cmd.getAttr(hbShape +'.vHboxSet', asString=True)
					if hbSetName == "":
						#if there is no value make it the default
						myHbSet = "default";
					else:
						myHbSet = hbSetName;
				else:
					#if there is no attribute ( from old assets ) assume default
					myHbSet = "default";
				#see what set we match too
				try:
					i = hbSets.index(myHbSet)
				except ValueError:
					i = -1 # no match
				'''
				print ( "\nHitbox: %s " %name )
				print ( "Set: %s"% myHbSet )
				print ( "Index: %i\n"% i )
				'''
				setIndex = i;
				script.appendNewHitbox( name, name, hbMin, hbMax, hbGroupId , setIndex , myHbSet)
	script.write()


def createRagdollPiece( joint, threshold=0.65 ):
	verts = []

	#so this is just to deal with the input arg being a tuple, list or string.  you can pass in a list
	#of joint names and the verts affected just get accumulated into a list, and the resulting bound
	#should be the inclusive bounding box for the given joints
	import skinCluster
	if isinstance( jointName, (tuple,list) ):
		theJoint = jointName[0]
		for j in joint:
			verts += skinCluster.jointVertsForMaya(joint, threshold)
	else:
		assert isinstance( joint, basestring )
		verts += skinCluster.jointVertsForMaya(joint, threshold)


	dmeMesh = vs.datamodel.CreateElement( 'DmeMesh', '%s' % joint, vs.datamodel.DMFILEID_INVALID )
	assert isinstance( dmeMesh, vs.movieobjects.CDmeMesh )
	positions = dmeMesh.GetCurrentBaseState().positions
	for vert in verts:
		vPos = vs.mathlib.Vector( *cmd.xform(vert, query=True, ws=True, t=True) )
		positions.append( vPos )

	from vs import dmxedit
	dmxedit.ComputeConvexHull3D( dmeMesh )

	return createHitbox( theJoint, minB, maxB )


def updateVmf( assetSlot, node='', autocompile=True ):
	'''
	simply grabs the objects being managed by a given slot, looks for their id's in their source
	vmf file, and pushes any changes to positioning if any - deals with perforce and all that jazz
	'''

	#create the asset object
	asset = ExportComponent(assetSlot, node)

	vmfFilepath = asset.getExportPath()
	if not vmfFilepath.exists:
		raise Exception( "can't determine what vmf files the objects come from" )

	#setup the progressWindow and create the callback function to update it - this isn't required, but
	#it does provide the user with a visual representation of progress as vmf reads on large files are slow...
	progressWindow = cmd.progressWindow
	progressWindow(progress=0, title='updating the vmf', status='updating the vmf', max=100)
	updateProgressCallback = api.updateProgressCallback

	mapFile = vmf.VmfFile(vmfFilepath, readCallback=updateProgressCallback)
	progressWindow(endProgress=True)

	#get the list of objects to update
	changesMade = False
	for obj in asset.objs:
		if not cmd.objExists( obj +'._id' ):
			api.melWarning("%s doesn't have an _id attribute - it is being ignored" % obj)
			continue

		id = cmd.getAttr(obj +'._id')
		match = mapFile.getById(id)

		#if there is no match, throw up a warning
		if match == None:
			api.melWarning("%s with id %d wasn't found in %s" % (obj, id, vmfFilepath))
			continue
			#answer = cmd.promptDialog(m=msg, t='entity doesnt exist in map', b=('Yes','No'), db='Yes')
			#if answer == 'No': continue
			##TODO: create the new entity

		#grab the transforms for the maya objects and compare them to the transforms in teh map file
		#and then reshuffle angles - they're Y Z X
		mayaPos = cmd.getAttr('%s.t' % obj)[0]
		mayaRot = cmd.getAttr('%s.r' % obj)[0]
		mayaRot = (mayaRot[1],mayaRot[2],mayaRot[0])

		#try to grab the origin attr - wrapping this in a try statement is faster then testing for the attributes
		#existence for cases where the attribute exists - similarly in the angles case below
		try:
			origin = match.origin
			mapPos = tuple( map(float,origin.value.split()) )
			if not compareLists( mayaPos, mapPos, 1e-4 ):
				origin.value = ' '.join(map(str,mayaPos))
				changesMade = True
		except AttributeError: print 'no pos found'

		try:
			angles = match.angles
			mapRot = tuple( map(float,angles.value.split()) )
			hasPitch = False

			#if the entity has pitch then grab the Y angle from the pitch attribute - who knows why things work like this...
			if match.hasAttr('pitch'):
				pitch = float(match.pitch.value)
				mapRot = (-pitch,mapRot[1],mapRot[2])
				hasPitch = True

			if not compareLists( mayaRot, mapRot, 1e-4 ):
				if hasPitch:
					match.pitch.value = -mayaRot[0]
					mayaRot = (0,mayaRot[1],mayaRot[2])
				angles.value = ' '.join(map(str,mayaRot))
				changesMade = True
		except AttributeError: print 'no angles found'

		#now look for any other user attrs and see if they exist in the vmf - if so, make sure they're up to date
		attrs = map(str,cmd.listAttr(obj,ud=True))
		updateAttrs = False
		if updateAttrs:
			for attr in attrs:
				try:
					mapValue = getattr(match,attr).value
					mayaValue = str(cmd.getAttr('%s.%s' % (obj, attr)))
					if mapValue != mayaValue:
						getattr(match,attr).value = mayaValue
						changesMade = True
				except AttributeError: pass


	#write any changes back to the source file
	if changesMade:
		try:
			mapFile.write()
		except IOError:
			api.melError("there was an error writing the file - vmf wasn't updated")
			raise

		compileProcess = None
		try:
			#compile the map
			if autocompile:
				pathObj = Path( vmfFilepath )
				vmfName = pathObj.setExtension('')[-1]
				bspFilepath = resolvePath( '%VPROJECT%/maps/'+ vmfName +'.bsp' )

				#make sure the target .bsp is checked out first
				mel.p4_sync([bspFilepath],0)
				if os.path.exists(bspFilepath):
					mel.p4_edit([bspFilepath],-1)

				#run the cmd
				#pathObj.putcwd()
				cmdStr = 'compile_vmf_pause.bat -onlyents %s' % vmfName
				compileProcess = utils.spawnProcess(cmdStr, pathObj)
				print 'firing off the compile cmd: %s%s' % (Path.getcwd(), cmdStr)
		except IOError:
			#no idea what sort of exceptions might be thrown here...
			api.melError("there was an error compiling the vmf - you'll need to do that manually...  sorry")
			raise


		#now try to send an update to the engine that the map has changed, and re-run the choreo test script
		#so choreo scene update commands are stored in a .engineScript file in the same directory as the current
		#maya scene with the same name as the maya file.  so a maya scene called badlands_01_finale.ma would
		#have a script called badlands_01_finale.engineScript
		try:
			#make sure the compileProcess has finished...
			compileProcess.wait()

			#first do a map reload...
			mapName = Path(mapFile.filepath)[-1].replace('.vmf','')
			mel.system('ipccomm --e -- map %s' % mapName)
			print 'fired off map reload command to engine'

			#now check to see if there are any engine scripts to fire off...
			curFile = Path( cmd.file(q=True,sn=True) )
			xtn = str( curFile )[ str(curFile).rfind('.'): ]
			curFile[-1] = curFile[-1].replace(xtn,'.engineScript')

			if curFile.exists:
				engineUpdateScript = file(curFile)
				engineUpdateCmds = engineUpdateScript.readlines()
				engineUpdateScript.close()
		except IOError:
			api.melError('oops there was an error')
			raise


def updateFromVmf( slot, node='' ):
	'''
	updates existing scene objects to any changes made in their source vmf
	'''
	asset = ExportComponent(slot, node)

	vmfFilepath = asset.getExportPath().resolve().setExtension('vmf')

	updateProgressCallback = api.updateProgressCallback
	progressWindow = cmd.progressWindow
	progressWindow(progress=0,title='updating from vmf',status='updating from vmf',max=100)

	mapFile = vmf.VmfFile(vmfFilepath,readCallback=updateProgressCallback)
	progressWindow(endProgress=True)

	global ENTITY_ATTRS_TO_SKIP
	for obj in asset.objs:
		if not cmd.objExists( obj +'._id' ):
			continue

		id = cmd.getAttr(obj +'._id')
		match = mapFile.getById(id)
		if match is not None:
			classname = ''
			try:
				classname = cmd.getAttr('%s.classname' % obj)
				if classname != match.classname.value:
					api.melWarning("the classname of %s with id %d doesn't match the entity in the vmf - it is being skipped for now..." % (obj, id))
					continue

			#this exception should only be thrown when the classname attribute doesn't exist on the maya node - which should only be the case with
			#vmfs imported before the classname attributes were created on import (june 04th '08)
			except TypeError: pass

			#do transforms
			pos,rot = entityTransformToMaya(match)
			cmd.setAttr('%s.t' % obj, *pos)
			cmd.setAttr('%s.r' % obj, *rot)

			#update other attributes
			assert isinstance(match, Chunk)
			for attr in match.listAttr():
				if attr in ENTITY_ATTRS_TO_SKIP: continue
				try:
					newValue = getattr(match,attr).value
					if newValue is not None: cmd.setAttr( '%s.%s' % (obj, attr), newValue, type='string' )
				except RuntimeError: pass


def entityTransformToMaya( entity ):
	'''
	given a Chunk instance (usually from a findKey or getById method) this will return the entity's
	maya transforms.  transforms in vmf files are represented weirdly...
	'''
	pos = ()
	try:
		origin = entity.origin
		pos = tuple( map(float,origin.value.split()) )
	except AttributeError: pass

	rot = ()
	try:
		angles = entity.angles
		rot = map(float,angles.value.split())

		#if the entity has pitch then grab the Y angle from the pitch attribute - who knows why things work like this...
		if entity.hasAttr('pitch'):
			pitch = float(entity.pitch.value)
			rot = (-pitch,rot[1],rot[2])

		#now rearrange rotations to xyz
		rot = ( rot[2], rot[0], rot[1] )
	except AttributeError: pass

	return pos,rot

def mayaTransformToEntity( obj ):
	'''
	given a maya object this will return the object's entity transforms.  transforms in vmf files are
	represented weirdly...
	'''
	pos = cmd.getAttr('%s.t'%obj)[0]

	rot = cmd.getAttr('%s.r'%obj)[0]
	rot = (rot[1],rot[2]-90,rot[0])

	return pos,rot


def compareLists( listA, listB, delta ):
	deltaList = [delta]*len(listA)
	if False in map( compareWithin, listA, listB, deltaList ): return False
	return True


def compareWithin( numberA, numberB, delta ):
	try:
		if abs( numberA - numberB ) <= delta: return True
	except TypeError: pass
	return False


def loadPlayerStart( slot ):
	#grab the vmf path
	asset = ExportManager()[slot]
	assert isinstance(asset, ExportComponent)

	theVmf = asset.getExportPath()

	#build the read progress window
	cmd.progressWindow(t='parsing vmf for player start',st='parsing vmf for player start')
	def updateProgressCallback( curLine, numLines ):
		progress = int( curLine/float(numLines)*100 )
		cmd.progressWindow(edit=True,progress=progress)

	vmf = vmf.VmfFile(resolvePath(theVmf+'.vmf'), readCallback=updateProgressCallback)
	cmd.progressWindow(ep=True)

	playerStarts = vmf.findKeyValue('classname','info_player_start')
	for start in playerStarts:
		startChunk = start.parent
		startId = int(startChunk.id.value)
		pos = map(float,startChunk.origin.value.split())
		rot = map(float,startChunk.angles.value.split())
		#pos = [pos[1],pos[2],pos[0]]
		rot = [rot[2],rot[0],rot[1]+90]

		#import the player start model
		playerModel = cmd.vsMdlIO(i=True, returnCreated=True, filename=resolvePath("%VGAME%/hl2/models/editor/playerstart.mdl"))[0]
		cmd.setAttr('%s.rz' % playerModel,90)
		cmd.makeIdentity(playerModel, apply=True, r=True)

		#get the map group to parent the player model to
		parents = asset.getObjs()
		vmfGroup = ''
		while vmfGroup == '':
			for p in parents:
				if cmd.objExists(p +'._filename'):
					vmfGroup = p
			parents = cmd.listRelatives(parents,p=True,pa=True)

		#set transform attrs
		playerModel = cmd.parent(playerModel,vmfGroup,r=True)[0]
		cmd.setAttr(playerModel +'.t',*pos)
		cmd.setAttr(playerModel +'.r',*rot)

		#set the id and parent under the vmf group so it can be re-exported, and add it to the asset
		cmd.addAttr(playerModel,ln='_id',at='long')
		cmd.setAttr(playerModel +'._id',startId)
		setName = asset.getObj()
		cmd.sets(playerModel,e=True,fe=setName)

		#finally collapse the player start group - the mdl importer brings it in as a moderately complex hierarchy...
		shapes = cmd.listRelatives(playerModel,ad=True,type='mesh',pa=True)
		for shape in shapes:
			cmd.parent(shape,playerModel,add=True,s=True)
		cmd.delete( cmd.listRelatives(playerModel,ad=True,type='transform') )


def getVmfFileFromObjs( objs ):
	'''
	given a list of objects, this method will recurse up the hierarchy searching for the _filename attribute
	that is created by teh vmf importer.  if one isn't found, None is returned
	'''
	def getFilePathFromObjs( objs ):
		for obj in objs:
			if cmd.objExists(obj +'._filename'):
				vmfFilepath = cmd.getAttr(obj +"._filename")
				return vmfFilepath

		return None

	parents = cmd.listRelatives(objs,p=True)
	while parents != None:
		vmfFilepath = getFilePathFromObjs( parents )
		if vmfFilepath != None: return Path( vmfFilepath )
		parents = cmd.listRelatives(parents,p=True)

	return None


def writePosesPreset( poseTrigger, filename, groupName=None ):
	undo = vs.CDisableUndoScopeGuard()
	dm = vs.g_pDataModel

	if groupName is None: groupName = Path(filename).setExtension()[-1]
	fileId = dm.FindOrCreateFileId( filename )

	#build the presetGroup
	presetGrpId = dm.CreateElement( "DmePresetGroup", "%s"%groupName, fileId )
	presetGrp = dm.GetElement( presetGrpId )

	a_presetsArray = presetGrp.AddAttribute( "presets", vs.AT_ELEMENT_ARRAY )

	#build the cmd strings so we can set the poses
	asTrigger = triggered.Trigger(poseTrigger)
	objects = asTrigger.connects()
	cleanlyNamedObjects = [obj.split("|")[-1] for obj in objects]
	cmdSlots = asTrigger.listMenus()

	#now remove the first one - we assume its the base pose - and get its resolved cmd string
	basePose = cmdSlots.pop(0)
	basePoseCmd = asTrigger.getMenuCmd(basePose,True)

	#the infos contains a list of tuples - each tuple contains the name/cmdStr for each menu item.  cmdStrs are resolved...
	infos = [asTrigger.getMenuInfo(cmdSlot,True) for cmdSlot in cmdSlots]

	#add the pose to the group
	for pose,cmdStr in infos:
		idx = pose.rfind('_')
		poseName = pose
		if idx > 0:
			poseName = pose[:idx]
			poseValue = int( pose[idx+1:] )
			if poseValue < 0:
				poseName += 'Down'
				continue


		#set the pose - set the base pose first, then the actual pose...
		mel.eval(basePoseCmd)
		mel.eval(cmdStr)

		presetId = dm.CreateElement( "DmePreset", str(poseName), fileId )
		preset = dm.GetElement( presetId )
		a_presetsArray.AddToTail( preset )

		a_controlsArray = preset.AddAttribute( "controlValues", vs.AT_ELEMENT_ARRAY )
		a_procedural = preset.AddAttribute( "procedural", vs.AT_INT )
		a_procedural.SetValue(0)


		#build the elements - these are the position and rotation values per joint for the pose
		for obj,clean in zip(objects,cleanlyNamedObjects):
			pos = cmd.getAttr('%s.t'%obj)[0]
			rot = OpenMaya.MTransformationMatrix( api.getMDagPath(obj).inclusiveMatrix() ).rotation()


			jointPosId = dm.CreateElement( "DmElement", "%s - pos"%str(clean), fileId )
			jointPos = dm.GetElement( jointPosId )
			a_controlsArray.AddToTail( jointPos )

			a_position = jointPos.AddAttribute( "valuePosition", vs.AT_VECTOR3 )
			a_position.SetValue( vs.Vector( *pos ) )


			jointRotId = dm.CreateElement( "DmElement", "%s - rot"%str(clean), fileId )
			jointRot = dm.GetElement( jointRotId )
			a_controlsArray.AddToTail( jointRot )

			a_rotation = jointRot.AddAttribute( "valueOrientation", vs.AT_QUATERNION )
			a_rotation.SetValue( vs.Quaternion( rot.x, rot.y, rot.z, rot.w ) )

	#<!-- dmx encoding keyvalues2 1 format preset 3 -->
	dm.SaveToFile( filename, "preset", "keyvalues2", dm.GetFileFormat(fileId), presetGrp )
	dm.UnloadFile( fileId )
	api.melPrint('DONE!')


ENTITY_ATTRS_TO_SKIP = set( ['id','classname','origin','angles'] )
def create_info_target():
	theAsset, vmfFile, vmfTopNode, entityObj = createMayaBaseEntity()

	infoTarget = cmd.spaceLocator()[0]
	cmd.parent(infoTarget,entityObj,r=True)

	vmfFile = vmf.VmfFile( vmfFile )
	infoTargetChunk = vmfFile.create_info_target('')
	vmfFile.write()

	#create the id attribute
	cmd.addAttr(infoTarget, ln="_id", at="long")
	cmd.setAttr('%s._id' % infoTarget, int(infoTargetChunk.id.value))
	cmd.setAttr('%s._id' % infoTarget, lock=True, keyable=True)

	#add all entity attributes to the maya node
	attrs = infoTargetChunk.listAttr()
	for attr in attrs:
		if attr in ENTITY_ATTRS_TO_SKIP: continue
		cmd.addAttr(infoTarget, ln=attr, dt="string")

	cmd.setAttr('%s.localScale' % cmd.listRelatives(infoTarget,s=True)[0], 10, 10, 10)

	#add the info target to the export asset, and name it sensibly
	theAsset.add(infoTarget)
	cmd.rename(infoTarget,'info_target#')

	return infoTarget


def create_scripted_sequence():
	theAsset, vmfFile, vmfTopNode, entityObj = createMayaBaseEntity()

	scriptedSequence = cmd.vsMdlIO(i=True, vstInfo=False, lod='root', importSkeleton=False, filename="models/editor/scriptedsequence.mdl")[0]
	cmd.parent(scriptedSequence,entityObj,r=True)

	vmfFile = vmf.VmfFile( vmfFile )
	infoTargetChunk = vmfFile.create_scripted_sequence('')
	vmfFile.write()

	#create the id attribute
	cmd.addAttr(scriptedSequence, ln="_id", at="long")
	cmd.setAttr('%s._id' % scriptedSequence, int(infoTargetChunk.id.value))
	cmd.setAttr('%s._id' % scriptedSequence, lock=True, keyable=True)

	#add all entity attributes to the maya node
	attrs = infoTargetChunk.listAttr()
	for attr in attrs:
		if attr in ENTITY_ATTRS_TO_SKIP: continue
		cmd.addAttr(scriptedSequence, ln=attr, dt="string")

	scriptedSequenceShape = cmd.listRelatives(scriptedSequence,s=True)[0]
	cmd.setAttr('%s.overrideEnabled' % scriptedSequenceShape, 1)
	cmd.setAttr('%s.overrideLevelOfDetail' % scriptedSequenceShape, 1)
	cmd.setAttr('%s.overrideColor' % scriptedSequenceShape, 9)

	#add the info target to the export asset, and name it sensibly
	theAsset.add(scriptedSequence)
	cmd.rename(scriptedSequence,'scripted_sequence#')

	return scriptedSequence


def createMayaBaseEntity():
	exportMan = ExportManager()
	vmfFile = None
	theAsset = None
	vmfTopNode = None

	for asset in exportMan:
		if asset.getAttr('type') == ExportComponent.kVMF:
			theAsset = asset
			break

	if theAsset is None:
		#in this case go searching in the scene for an object that refers to a vmf file
		for node in cmd.ls(type='transform'):
			try:
				vmfFile = Path( cmd.getAttr('%s._filename' % node) )
				theAsset = exportMan.createAsset([node])
				vmfTopNode = node
				theAsset.setAttr('path', vmfFile.up())
				theAsset.setAttr('type', ExportComponent.kVMF)
				vmfTopNode = node
			except TypeError: continue
	else:
		vmfFile = theAsset.getExportPath()

	if vmfFile is None:
		raise AttributeError('no vmf file can be found in this scene - you need to import a vmf first so I know what map to add the info_target node to')

	#now find the top of the vmf hierarchy
	if vmfTopNode is None:
		upHierarchy = [theAsset.objs[0]] + getAllParents( theAsset.objs[0] )
		upHierarchy.reverse()
		for obj in upHierarchy:
			try:
				cmd.getAttr( '%s._filename' % obj )
				vmfTopNode = obj
			except TypeError: pass

	#make sure the entities group exists
	entityObj = None#'%s|entities' % vmfTopNode
	for child in cmd.listRelatives(vmfTopNode,type='transform'):
		if str(names.Name(child).strip(False)) == 'entities':
			entityObj = child
			break

	if not cmd.objExists(entityObj):
		entityObj = cmd.group(name='entities', empty=True)
		cmd.parent(entityObj,vmfTopNode,r=True)

	return theAsset, vmfFile, vmfTopNode, entityObj


def entsToGeo():
	'''
	super hacky method to deal with creating geometrical representations for various imported vmf
	nodes brought in by vsVmfIO.  it is done this way simply because it was about 1000 times easier
	for me to just write a script to do it than figure out how to code it into the plugin...
	'''
	locs = cmd.ls(type='locator')
	if locs is None: return

	entsGrp = cmd.listRelatives(locs[0], pa=True, parent=True)[0]
	entsGrp = cmd.listRelatives(entsGrp, pa=True, parent=True)[0]

	for loc in locs:
		loc = cmd.listRelatives(loc, pa=True, parent=True)[0]
		try:
			classname = cmd.getAttr('%s.classname' % loc)
			if classname == 'scripted_sequence':
				cube, node = cmd.polyCube(w=32, h=32, d=72)
				shape = cmd.listRelatives(cube, s=True)[0]

				#move pivots etc...
				cmd.move(0, 0, -36, '%s.scalePivot' % cube, '%s.rotatePivot' % cube, r=True)
				cmd.move(0, 0, 36, cube)
				cmd.makeIdentity(cube, apply=True, t=True)

				#remove locator shapes
				cmd.delete( cmd.listRelatives(loc, s=True) )

				#parent the shape to the scripted sequence transforms
				cmd.parent(shape, loc, add=True, s=True)
				cmd.delete(cube)
		except TypeError: pass


def getSceneDependencies( **kwargs ):
	'''
	returns a list of the current scene's external file dependencies

	ignoreTextures=True will stop textures from being listed as dependencies
	'''
	ignoreTextureFiles = cmd.optionVar(q='vIgnoreTexturesOnCheckin') if cmd.optionVar(ex='vIgnoreTexturesOnCheckin') else kwargs.get('ignoreTextures', False)
	thatMayaKnowsAbout = cmd.file(q=True, l=True)
	if thatMayaKnowsAbout is not None:
		thatMayaKnowsAbout = map(Path, thatMayaKnowsAbout)
		thatMayaKnowsAbout = [p for p in thatMayaKnowsAbout if p.exists]

	existingFromMaya = []
	fromAssets = []
	allFiles = []


	###  MODEL AND RIG DEPENDENCIES  ###
	#look to see if we have a "model" file open.  if so, look for a corresponding "rig" file
	#one tricky, and not uncommon path is if you have made changes to a reference file AND a rig
	#file, but you have the reference open when building a changelist, the rig can get overlooked
	assetRoot = getAssetRoot()
	filepath = Path( cmd.file(q=True, sn=True) )
	filename = filepath[-1]
	sFilename = str(filename)
	isModel = sFilename.find('_model.m') != -1 or sFilename.find('_reference.m') != -1

	try:
		rigBuildScript = assetRoot / 'scripts/build_rig.mel'
		if rigBuildScript.exists: fromAssets.append(rigBuildScript)
	except TypeError: pass

	if isModel:
		idx = sFilename.rfind('_')
		basename = sFilename[:idx]
		rigName = '%s_rig.%s' % (basename, filepath.extension)
		rigPath =  filepath[:-1] / rigName

		if rigPath.exists: fromAssets.append( rigPath )


	###  EXPORT MANAGER DEPENDENCIES  ###
	#now go through all the info nodes in the scene, and look for the assets they spit out (if any)
	#and add them to the list
	allInfoNodes = cmd.ls(type='vstInfo')
	for node in allInfoNodes:
		xman = AnExportManager(node)
		for asset in xman:
			assert isinstance(asset, ExportComponent)
			path = asset.getExportPath()
			fromAssets.append(path)

		#look at the .qc file associated with the scene - if any
		compileScripts = xman.listCompileScripts()
		qcDeps = []
		dirListingCache = {}
		for script in compileScripts:
			if script is None or script == '':
				continue
			
			script = script.getScriptPath()
			fromAssets.append(script)
			if script.getExtension().lower() != 'qc':
				continue

			if not script.exists:
				api.melWarning("%s doesn't exist on disk, so it can't be parsed for qc dependencies" % script)
				continue

			mdlPath = qcTools.getMdlFromQc(script)
			if mdlPath is not None:
				mdlFiles = mp.getMdlFiles( mdlPath )
				fromAssets += mdlFiles

			fromAssets += qcTools.getQcIncludes(script)


	###  TEXTURE/MATERIAL DEPENDENCIES  ###
	#look for any vmt nodes in the scene and add them - vmt files are easy to miss when checking in a bunch of changes...
	vmtNodes = cmd.ls(type='vsVmtToTex')
	if not ignoreTextureFiles:
		for node in vmtNodes:
			relPath = cmd.getAttr("%s.materialPath" % node)
			pathToVMT = Path( "%VGAME%/%VMOD%/materials/"+ relPath +".vmt" )

			if pathToVMT.exists:
				fromAssets.append(pathToVMT)

			#what about content textures?  are there any on the users machine?
			#models/props_street/police_barricade
			relPathToContent = Path("materialsrc/%s" % relPath)
			for ext in ['psd', 'tga']:
				contentTexture = relPathToContent.expandAsContent(gameInfo, ext)
				if contentTexture is not None:
					fromAssets.append(contentTexture)
					break

	#now remove any texture files if they're not wanted
	textureExtensions = set(["tga", "bmp", "psd", "vtf"])
	if ignoreTextureFiles:
		thatMayaKnowsAbout = [p for p in thatMayaKnowsAbout if p.extension.lower() not in textureExtensions]
	else:
		#make sure textue .txt files are included in the list of dependencies
		for t in thatMayaKnowsAbout:
			if t.extension.lower() in textureExtensions:
				txtFile = Path(t).setExtension('txt')
				if txtFile.exists: thatMayaKnowsAbout.append(txtFile)


	###  REMOVE DUPES, RETURN  ###
	tmpAllFiles = list( set(thatMayaKnowsAbout + fromAssets) )
	allFiles = []
	
	# Always remove debugEmpty.*
	# Would just do this... but builtin filter has been overridden by some import * :(
#	allFiles = filter( lambda x: not re.search( "[\\/]debugempty\.((vtf)|(vmt))$", str( x ), re.IGNORECASE ) , allFiles )
	print
	print "*tmpAllFiles:", len(tmpAllFiles), tmpAllFiles
	
	reNotDebugEmpty = re.compile( "[\\/]debugempty\.((vtf)|(vmt))$", re.IGNORECASE )
	
	for sFile in tmpAllFiles:
		if reNotDebugEmpty.search( str( sFile ) ):
			continue
		allFiles.append( sFile )
	
	print "*ALLFILES:", len(allFiles), allFiles

	return allFiles


@api.d_progress(t='syncing stale dependencies', status='determining dependencies...', ii=True)
def syncStaleSceneDependencies():
	deps = getSceneDependencies()
	progress, inc = 0, 100.0/len(deps)
	p4 = P4File()
	for dep in deps:
		dep = str(dep.resolve())
		latest = p4.isLatest(dep)
		progress += inc
		if latest is None:
			print dep, 'is not in perforce'
			continue

		if not latest:
			displayDep = Path(dep)-'%VCONTENT%'
			print 'syncing to', displayDep
			try:
				if cmd.progressWindow(q=True, ic=True): break
				cmd.progressWindow(e=True, progress=progress, status='syncing to %s' % displayDep)
			except: pass
			p4.sync(dep)


def printSceneDeps():
	'''
	prints the scene's depdencies - grouped by file extension
	'''
	deps = getSceneDependencies()
	allFilesExt = {}
	for f in deps:
		try:
			allFilesExt[f.extension].append(f)
		except KeyError: allFilesExt[f.extension] = [f]

	for a, files in allFilesExt.iteritems():
		print '[%s]' % a
		for f in files: print f


@api.d_showWaitCursor
def gatherSceneDependenciesIntoChange():
	'''
	gathers the current scene and all its dependencies into the same changelist as the current scene.  if the
	current scene isn't open in any way, then the default change is used
	'''
	curScene = cmd.file(q=True, sn=True)
	change = None
	if curScene is None:
		cmd.promptDialog(m='the current scene is not saved\n\na scene specific changelist cannot be created until the scene has a name', t='scene not saved', b='OK')
		return
	
	curScene = Path(curScene)
	desc = str( '%s Auto Checkout\n%s' % (curScene[-1], curScene))
	change = P4File().getChangeNumFromDesc(desc)
	deps = getSceneDependencies()
	gathered = gatherFilesIntoChange(deps, change)
	
	print ''
	print 'GATHERED THE FOLLOWING FILES INTO A SINGLE CHANGELIST: %s' % desc
	for sFile in gathered:
		print sFile

	return gathered


@api.d_progress(t='generating debug report', status='generating debug report')
def generateSceneReport():
	'''
	generates a "scene report" for the currently open scene.  the report includes the a dump of
	the script editor since either when maya was last opened, or when the script editor was last
	cleared.  the report also enumerates ALL scene dependencies, as well as stale dependencies,
	dependencies NOT in perforce, and a dump of all environment variables
	'''
	msgLines = []

	curScene = Path(cmd.file(q=True, sn=True))
	if not curScene.exists: curScene = '<not saved>'
	msgLines.append('current scene: %s' % curScene)
	msgLines.append('')

	#gather scene dependencies
	notInP4 = []
	staleDeps = []
	deps = getSceneDependencies()
	progress, inc = 0, 100.0

	if deps:
		msgLines.append('##########DEPS##########')
		for dep in deps:
			msgLines.append(dep)
		msgLines.append('##########END DEPS##########')

	try: inc /= len(deps)
	except ZeroDivisionError: pass

	p4 = P4File()
	for dep in deps:
		dep = str(dep.resolve())
		latest = p4.isLatest(dep)
		progress += inc
		if latest is None:
			notInP4.append(dep)
			continue

		if not latest:
			staleDeps.append(dep)

	if notInP4:
		msgLines.append('##########START NOT IN P4##########')
		msgLines += notInP4
		msgLines.append('\n##########END NOT IN P4##########')
		msgLines.append('')


	#add environment data...
	msgLines.append('##########START ENV##########')
	msgLines += ['%s = %s' % a for a in os.environ.iteritems()]
	msgLines.append('\n##########END ENV##########')
	msgLines.append('')

	if staleDeps:
		msgLines.append('##########START STALE DEPS##########')
		msgLines += staleDeps
		msgLines.append('\n##########END STALE##########')
		msgLines.append('')

	#finally construct the actual message text
	return u'\n'.join( map(str, msgLines) )


def emailSceneReport( emailRecipient='hamish@valvesoftware.com' ):
	import smtplib

	knownRecipients = {'everyone': ['hamish@valvesoftware.com', 'wade@valvesoftware.com', 'stevek@valvesoftware.com', 'bronwen@valvesoftware.com']}
	emailRecipient = knownRecipients.get(emailRecipient, emailRecipient)
	reportStr = generateSceneReport()

	subject = '[BUG] report on %s' % os.environ['VPROJECT']
	message = u'Subject: %s\n\n%s' % (subject, reportStr)
	svr = smtplib.SMTP( MAIL_SERVER )
	svr.sendmail(os.environ['USER'], emailRecipient, message)

	api.melPrint('emailed debug report to %s' % emailRecipient)


#end
