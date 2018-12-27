# -*- coding: utf-8 -*-
#--------------------------------
#更新日志:
#0.0.1:完成了基本功能
#0.0.2:添加了UV预处理功能,加了UI
#0.0.3:修改了__get_fileSource,可以获取支持的shander上的所有file了
#--------------------------------
#本应用基本上等于是面向过程,使用类来封装为了避免覆盖其他应用的函数
#--------------------------------
# 使用时使用python模式下使用以下代码初始化   (mayaWarpImg_03)为本应用的文件名,根据实际情况修改
# import mayaWarpImg_03 as mayaWarpImg
# mayaWarpImg.mayaWarpUI().showWindow()
#--------------------------------

import pymel.core as pm
import os.path as path
import errno
import re
#仅仅加载flatten这个方法来实现对多维组一维化
from compiler.ast import flatten

##定义几个绝对会出的异常
#所有的错误类型设置为FuckingError
class FuckingError(Exception):
    pass
class NoChoosedError(FuckingError):
	pass
class NoFileError(FuckingError):
	pass
class SameUVError(FuckingError):
	pass
class BadUVError(FuckingError):
	pass
class ShaderTypeError(FuckingError):
	pass
#传入选择对象
def mwi_selection ():
	#用来传选择的对象,少于1个直接返回None|抛出异常
	selection = pm.selected()
	try:
		if len(selection) < 1 or type(selection) == type(None):
			raise NoChoosedError
			return None
	except NoChoosedError :
		print (u'未选择对象\n')
		raise NoChoosedError
	else:
		print (u'对象大于0个,开始工作\n')
		return selection

#防坑爹,加utf8编码函数转到str备用,长名称mwi_mwi_unicode_2_utf8,短名称mwi_tutf
def mwi_unicode_2_utf8(input):
    if type(input) is str:
        return input.encode('utf-8')
    elif type(input) is list:
        for i in range(len(input)):
            input[i] = mwi_unicode_2_utf8(input[i])
        return input
    elif type(input) is dict:
        newinput={}
        for (key,value) in input.items():
            key = mwi_unicode_2_utf8(key)
            value = mwi_unicode_2_utf8(value)
            newinput[key] = value
        return newinput
    elif type(input) is tuple:
        return tuple(mwi_unicode_2_utf8(list(input)))
    elif type(input) is unicode:
        return input.encode('utf-8')
    else:
        print "WTF is input?",type(input)
        return input

def mwi_tutf(input):
	input = mwi_unicode_2_utf8(input)
	return input


#创建UI类,方便使用
class mayaWarpUI :
	u"""
	这是为mayaWarpImg创建的UI部分的类
	通过mayaWarpUI().showWindow()调用窗口
	"""
	def __init__(self):
		__author__ = 'MineClever'
		__contact__ = 'chnisesbandit@live.cn'
		__website__ = 'https://steamcommunity.com/id/chinsesbandit/home'
		self.version = '0.0.3'
		#初始化预设参数
		self.mwui_win='mayaWarpImageTool'
		self.mwui_win_icon='MWT'
		self.exportDir = pm.system.Workspace.getPath() + '/images'
		self.tBaseUV = 'tBaseUV'
		self.tWorkUV = 'tWorkUV'
		self.tFtype = 'tExportForm'
		self.baseUV = 'map1'
		self.workUV = 'map1'
		self.ftype = 'png'
		self.tRx = 'tRx'
		self.tRy = 'tRy'
		self.rx=self.ry=2048
		self.defaultnum=2048

	def __copyUV_ButtonPressed(self,*args):
		print '\n###################################'
		self.__changeUV()
		mayaWarp_UV_Prefix(self.workUV).copyUV(self.baseUV)

	def __prefixBaseUV_ButtonPressed(self,*args):
		print '\n###################################'
		self.__changeUV()
		mayaWarp_UV_Prefix(self.baseUV).prefixUV()

	def __prefixWorkUV_ButtonPressed(self,*args):
		print '\n###################################'
		self.__changeUV()
		mayaWarp_UV_Prefix(self.workUV).prefixUV()

	def __workButtonPressed(self,*args):
		print '\n###################################'
		#执行方法的时候对设置的参数进行输出,方便出错的时候进行检查
		self.__changeUV()
		self.__changeForm()
		self.__changeRy()
		self.__changeRx()
		if self.chkBoxAlpha.getValue():
			print u'当前输出原始图像的Alpha!'
			chkNoAlpha = False
		else:
			print u'当前不输出任何Alpha!'
			chkNoAlpha = True
		if self.chkBoxOver.getValue():
			print u'当前输出覆盖存在的文件!'
			chkOver = True
		else:
			print u'当前输出将不会覆盖存在的文件!'
			chkOver = False
		if self.chkBoxTile.getValue():
			print u'当前对输出图像进行平铺!'
			chkTile = True
		else:
			print u'当前不对输出图像进行平铺!'
			chkTile = False

		print '\n'
		#运行设置的指令(直接在mayaWarpImg的class上完成初始化并执行)
		mayaWarpImg( exportDir=self.exportDir, baseUV=self.baseUV, workUV =self.workUV, ftype=self.ftype, noAlpha=chkNoAlpha,
		Over=chkOver, Tile=chkTile, rx=self.rx, ry=self.ry).warpImg()

	def __browserDir(self,*args):
		self.exportDir=pm.system.fileDialog2( ds=1, fm=2, cap=u'浏览输出文件夹')
		#但返回是列表,取列表首个作为目录
		if isinstance(self.exportDir,list):
			self.exportDir = self.exportDir[0]
		#返回空目录,使用缺省images目录
		if self.exportDir is None:
			self.exportDir = pm.system.Workspace.getPath() + '/images'
		pm.windows.textField(self.dirIput,tx='%s'%(self.exportDir), e=True)
		d = u'设置输出目录为:%s'%(self.exportDir)
		pm.warning(d)

	def __changeUV(self):
		self.baseUV = pm.windows.textField(self.tBaseUV, q=True, text=True)
		if len(self.baseUV)<1:
			self.baseUV = 'map1'
		self.workUV = pm.windows.textField(self.tWorkUV, q=True, text=True)
		if len(self.workUV)<1:
			self.workUV = 'map1'
		d = u'当前的 基础UV为:%s , 工作UV为:%s'%(str(self.baseUV),str(self.workUV))

		pm.warning(d)
	def __changeForm (self):
		self.ftype = pm.windows.textField(self.tFtype, q=True, text=True)
		if len(self.ftype)<1:
			self.ftype = 'png'
		d = u'当前输出的文件格式为:%s'%(str(self.ftype))
		pm.warning(d)

	def __changeRx (self) :
		self.rx = pm.windows.textField(self.tRx, q=True, text=True)
		try:
			if self.rx is None or len(self.rx)<1:
				self.rx = self.defaultnum
			elif int(self.rx) == 0:
				raise ValueError
			else:
				self.rx = int (self.rx)
			d = u'当前输出的贴图宽度为:%s'%(str(self.rx))
		except ValueError:
			self.rx = self.defaultnum
			d = u'数值错误,设置缺省贴图宽度为:%s'%(str(self.rx))
		pm.warning(d)
	def __changeRy (self) :
		self.ry = pm.windows.textField(self.tRy, q=True, text=True)
		try:
			if self.ry is None or len(self.ry)<1:
				self.ry = self.defaultnum
			elif int(self.ry) == 0:
				raise ValueError
			else:
				self.ry = int (self.ry)
			d = u'当前输出的贴图宽度为:%s'%(str(self.ry))
		except ValueError:
			self.ry = self.defaultnum
			d = u'数值错误,设置缺省贴图宽度为:%s'%(str(self.ry))
		pm.warning(d)
	def showWindow(self):
		#确认是否已经存在功能窗口,存在时,直接结束存在窗口,重新初始化
		print u'\n################################################\n\n欢迎使用MineClever的小工具\n\n################################################'
		if pm.window(self.mwui_win,exists=True):
			print u'当前存在窗口%s,关闭并启动新窗口\n'%(self.mwui_win)
			pm.deleteUI(self.mwui_win, window=True)
			pm.windowPref(self.mwui_win, remove = True)

		#初始化功能窗口
		self.win = pm.window(self.mwui_win, title = u'Maya批量WarpImage V%s'%(self.version), iconName=self.mwui_win_icon, wh=(256, 512), toolbox=True,
		titleBar=True, resizeToFitChildren=True)
		layout = pm.columnLayout( columnAttach=('both', 32), rowSpacing=12, columnWidth=250,adjustableColumn=True)
		bLayout = pm.columnLayout( columnAttach=('both', 5), rowSpacing=5, columnWidth=50,adjustableColumn=True)
		#输入变量
		pm.windows.text(l=u'--这个区域用来填写输入变量--', parent=bLayout)
		pm.windows.textField(self.tBaseUV, tx='', editable=True, bgc=(0,0,0,), placeholderText=u'基础UV,默认map1', changeCommand=pm.Callback(self.__changeUV))
		pm.windows.textField(self.tWorkUV,tx='', editable=True, bgc=(0,0,0,), placeholderText=u'工作UV,默认map1', changeCommand=pm.Callback(self.__changeUV))
		#输出标记
		pm.windows.text(l=u'\n--这个区域用来设置输出参数--', parent=layout)
		self.dirIput = pm.windows.textField('tDirIput',tx='%s'%(self.exportDir), editable=False, parent=layout)
		pm.windows.textField(self.tFtype, tx='png', editable=True, bgc=(0,0.2,0), placeholderText=u'文件格式,默认png', changeCommand=pm.Callback(self.__changeForm), parent=layout)
		pm.windows.textField(self.tRx,tx='', editable=True, bgc=(0,0,0,),
		placeholderText=u'输出宽度,默认2048',
		changeCommand=pm.Callback(self.__changeRx), parent=layout)
		pm.windows.textField(self.tRy,tx='', editable=True, bgc=(0,0,0,),
		placeholderText=u'输出高度,默认2048',
		changeCommand=pm.Callback(self.__changeRy), parent=layout)

		self.chkBoxTile = pm.checkBox(label = u'进行平铺', value=True, parent=layout)
		self.chkBoxOver = pm.checkBox(label = u'覆盖已有文件', value=True, parent=layout)
		self.chkBoxAlpha = pm.checkBox(label = u'输出Alpha', value=True, parent=layout)
		#按钮
		pm.button(label=u'浏览输出目录', parent=layout, command=self.__browserDir, bgc=(0.5,0.5,0.5))
		pm.windows.text(l=u'\n--UV预处理--', parent=bLayout)
		pm.button(label=u'统一当前UV为基础UV', parent=bLayout, command=self.__prefixBaseUV_ButtonPressed, bgc=(0.35,0.35,0.45))
		pm.button(label=u'统一当前UV为工作UV', parent=bLayout, command=self.__prefixWorkUV_ButtonPressed, bgc=(0.35,0.35,0.45))
		pm.button(label=u'复制工作UV到基础UV', parent=bLayout, command=self.__copyUV_ButtonPressed, bgc=(0.0,0.0,0.2))
		pm.button(label=u'烘焙基础UV的贴图给工作UV', parent=layout, bgc=(0.3,0.0,0.0), command=self.__workButtonPressed)
		pm.windows.text(l=u'----------------------------\n'
		+u'作者:MineClever\n'
		+u'BUG报告邮箱:chnisesbandit@live.cn\n'
		+u'----------------------------\n'
		, parent=layout)
		#显示窗口
		self.win.show()

#这个部分是核心功能区域
class mayaWarpImg :
	u"""
	初始化参数
	exportDir (输出目录) <-必须为存在的目录,否则调用工程文件夹的images目录
	baseUV (基础UV) <-默认参数map1
	workUV (工作UV) <-默认参数map1
	ftype (输出文件后缀/类型) <-默认参数png
	NoAlpha (不输出图像ALPHA) <-默认参数False
	Over(覆盖存在的文件) <-默认参数True
	Tile(自动平铺) <-默认参数True
	rx,ry (x,y的分辨率) <-默认参数2048


	这是一个可以快速将所有选择对象的UV2烘焙成UV1的工具
	作者:"MineClever"
	联系与报告BUG:"chnisesbandit@live.cn"
	STEAM:"https://steamcommunity.com/id/chinsesbandit/home"
	"""
	def __init__( self, exportDir=None, baseUV='map1', workUV ='map1', ftype='png',
	noAlpha=False, Over=True, Tile=True, rx=2048, ry=2048):
		__author__ = 'MineClever'
		__contact__ = 'chnisesbandit@live.cn'
		__website__ = 'https://steamcommunity.com/id/chinsesbandit/home'
		#定位当前工程文件夹的images目录
		self.images = pm.system.Workspace.getPath() + '/images'
		self.exportDir = exportDir
		print u'初始化输出目录为:%s'%(self.exportDir)
		self.bakeTempDir=str(self.images+'/bakeTemp')
		self.baseUV = baseUV
		self.workUV = workUV
		self.ftype = ftype
		self.noAlpha = noAlpha
		self.over = Over
		self.Tile = Tile
		self.rx=rx
		self.ry=ry


	def __path_fix (self):
		exportDir = str(self.exportDir)
		#判断是否存在images目录,不存在,则创建一个images目录
		if not path.exists(self.images):
			try:
				os.makedirs(self.images)
			except OSError as e:
				if e.errno != errno.EEXIST:
					raise
		#判断是否有传入的目录
		if exportDir == None :
			print (u'!传入目录为空')
			self.exportDir = self.images + r'/'
		else :
			print (u'!传入目录非空')
			#有传入的目录时,确保目录存在,防作死
			if not path.exists(exportDir):
				print (u'目录不存在')
				try:
					os.makedirs(exportDir)
				except OSError as e:
					#抛出除了有文件存在的外的异常--可能多此一举
					if e.errno != errno.EEXIST:
						raise
				else:
					print (u'目录已不存在')
					self.exportDir = exportDir + r'/'
			else :
				self.exportDir = exportDir + r'/'
		d = u'修正后的输出目录为:%s'%(self.exportDir)
		print (d)

	#创建一个工作时的临时目录用于存储烘焙材质纯色
	def __getTempDir (self):
		#判断是否存在临时目录
		if not path.exists(self.bakeTempDir):
			print u'当前不存在临时烘焙目录,自动创建一个'
			try:
				os.makedirs(self.bakeTempDir)
			except OSError as e:
				if e.errno != errno.EEXIST:
					raise
		else:
			print u'当前临时烘焙目录已经存在,为:%s'%self.bakeTempDir


	def checkUV (self,obj):
		state = True
		print (u'正在检查UV')
		#查询对象的所有UV
		allUV = pm.polyUVSet( obj, query=True, allUVSets=True )
		#检查指定的UV是否存在
		try:
			if self.baseUV not in allUV:
				print u'基础UV:%s不存在于对象UV中,跳过当前对象%s'%(self.baseUV,str(obj))
				state = False
				return state
			if self.workUV not in allUV:
				print u'工作UV:%s不存在于对象UV中,跳过当前对象%s'%(self.workUV,str(obj))
				state = False
				return state
		except TypeError :
			d = u'UV有错误'
			pm.warning (d)
			state = False
			return state
		return state

	def __uniformUV (self,obj):
		#查询对象的所有UV
		#另一种风格写法:allUV=obj.getUVSetNames()
		allUV = pm.polyUVSet( obj, query=True, allUVSets=True )
		#强制指定当前UV为self.baseUV
		pm.polyUVSet( obj, currentUVSet=True, uvSet=self.baseUV )
		#创建新UV为mwi_showUV
		if 'mwi_showUV' in allUV:
			pm.polyUVSet( obj, delete=True, uvSet='mwi_showUV')
		##另外一种风格写法:obj.createUVSet('mwi_showUV')
		pm.polyUVSet( obj, create=True, uvSet='mwi_showUV' )
		#复制当前UV到mwi_showUV
		pm.polyUVSet( obj, copy=True, nuv='mwi_showUV' )

		#判断是否存在self.workUV的传入UV,不存在着创建self.workUV的传入UV
		if self.workUV not in allUV:
			pm.polyUVSet( obj, create=True, uvSet=self.workUV )

		#创建新UV为mwi_refUV
		if 'mwi_refUV' in allUV:
			pm.polyUVSet( obj, delete=True, uvSet='mwi_refUV')
		pm.polyUVSet( obj, create=True, uvSet='mwi_refUV' )
		#复制self.workUV到mwi_refUV
		pm.polyUVSet( obj, copy=True, nuv='mwi_refUV', uvSet=self.workUV)
		print u'UV统一完毕'
		state = True
		return state



	def __delUniformedUV (self,obj):
		#删除工作中尝试的临时UV
		allUV = pm.polyUVSet( obj, query=True, allUVSets=True )
		if 'mwi_showUV' in allUV:
			pm.polyUVSet( obj, delete=True, uvSet='mwi_showUV')
		if 'mwi_refUV' in allUV:
			pm.polyUVSet( obj, delete=True, uvSet='mwi_refUV')

	def __doWarp ( self, obj, file, ftype) :
		print 'WarpNow!'
		#防止传入的时候为list类型
		if isinstance(file,list):
			print (u'选取传入文件')
			if len(file) == 0:
				raise NoFileError
			else:
				file=file[0]

		fImportName = str(pm.getAttr(file.fileTextureName))
		fExportName = '%s_%s_warp.%s'%(str(obj),str(file),ftype)
		print (u'\n当前输入%s'%fImportName)
		print (u'输出为: '+fExportName)
		pm.other.polyWarpImage ( obj, b=True, ff=ftype, t=self.Tile, xr=self.rx, yr=self.ry,
		o=self.over, inputName=fImportName, outputName=self.exportDir+fExportName, na=self.noAlpha,
		iuv='mwi_showUV', ouv='mwi_refUV')
		d=u'已输出%s\n'%fExportName
		print (d)
		pm.warning(d)

	def __get_fileSource (self,obj):

		print (u'正在获取%s的贴图文件'%(str(obj)))
		#获得对象的Shape,再获取对象Shape的所有shadingEngine输出
		geo = obj.getShape()
		sg = geo.outputs(type='shadingEngine')
		#遍历每个shadingEngine获得materialInfo
		sgInfo = []
		for i in xrange(len(sg)) :
			sgInfo.append(sg[i].connections(type='materialInfo'))

		#确认shader类型,不支持的类型直接抛出异常
		shaderType=sgInfo[i][0].connections()
		shaderNodes = []
		#初始化一个gtype 的字段.用来存储shader 的类型
		gtype=''
		for i in shaderType:#判断shader类型
			if type(i) is pm.nodetypes.Phong:
				gtype = 'phong'
			if type(i) is pm.nodetypes.Lambert:
				gtype = 'lambert'
			if type(i) is pm.nodetypes.PhongE:
				gtype = 'phongE'
			if type(i) is pm.nodetypes.Blinn:
				gtype = 'blinn'
		print (u'找到Shader类型为 %s'%gtype)
		if gtype == '' :#如果没有改写shaderType,那么即为不支持的类型
			raise ShaderTypeError
		#获取materialInfo 节点上的shader
		for i in xrange(len(sgInfo)):
			shaderNodes.append(sgInfo[i][0].connections(type=gtype))
		#获取shader上的bump2d的file节点,添加到文件列表中
		listNodes = []
		for i in xrange(len(shaderNodes)):
			listNodes.append(shaderNodes[i][0].connections())
		fileNodes=[]
		for i in listNodes[0]:
			if type(i) is pm.nodetypes.Bump2d:
				print (u'找到 Bump2D 节点')
				fileNodes.append(i.connections(t='file'))
		#获取直接连接的File节点,添加到文件列表中
		for i in xrange(len(shaderNodes)):
			fileNodes.append(shaderNodes[i][0].connections(t='file'))
		rlist = [] #建立一个空列表用于最终输出
		#一维化列表//重要,否则导致运行过程中无法正确输出所有的贴图的FILE
		fileNodes=flatten(fileNodes)
		#过滤重复的文件
		for element in fileNodes:
			if element not in rlist:
				rlist.append(element)
		return rlist
	def warpImg(self):
		#传入选择的对象
		try:
			selection = mwi_selection ()
			if type(selection) == type(None):


				raise NoChoosedError
		except NoChoosedError:
			d= u'warpImg未传入对象\n'
			pm.warning(d)
			return
		#self.__getTempDir()
		#进行目录矫正
		print (u'进行目录修复')
		self.__path_fix()
		#对传入的对象逐个进行统一UV名称,再进行图像包裹/扭曲,最后删除统一UV名称
		try:
			for obj in selection :
				print ('----------------------------------------------')
				print (u'\n\n正在处理对象' + str(obj))
				#使用BOOL来确定UV是否有效,无效则跳过当前对象
				print (u'准备检查UV')
				stateUV = self.checkUV(obj)
				print (u'完成检查UV')

				if not stateUV :
					d=u'当前对象无某个指定UV,跳过当前对象,请通过控制台检查日志'

					pm.warning (d)
					continue
				print (u'准备统一UV')
				self.__uniformUV(obj)
				print (u'完成统一UV')
				#获取文件列表
				flist = self.__get_fileSource(obj)
				print (u'正在warp处理%s'%(str(obj)))
				print (u'列出所有文件节点'+str(flist))
				for file in flist :
					self.__doWarp(obj,file,self.ftype)

		except NoFileError:
			d=u'对象没有贴图文件'
			pm.warning(d)
		except ShaderTypeError:
			d=u'对象的Shader类型不支持'
			pm.warning(d)
		#强制删除工作时生成的UV
		finally:
			for obj in selection :
				self.__delUniformedUV(obj)
			

class mayaWarp_UV_Prefix :
	u"""
	UV预处理
	"""
	#将当前UV统一为指定的基础UV
	def __init__ (self,UV='nothing'):
		self.UV = UV
		self.preErr = u'无错误'
		#直接给个空类型,未选择时,直接抛出异常
		self.selection = None
		#传入选择的对象
		try:
			self.selection = mwi_selection ()
		except NoChoosedError:
			d= u'初始化时,未选择对象\n'
			pm.warning(d)
	def __checkUV (self,obj):
		state=True
		print('----------------------------------------------')
		print u'预处理程序,正在检查UV'
		#查询对象的所有UV
		allUV = pm.polyUVSet( obj, query=True, allUVSets=True )
		#检查指定的UV是否存在
		if type(self.UV) == type(None):
			state = False
			err= '无UV'.decode('utf-8')
			raise NoChoosedError
			return state,err
		try:
			if self.UV not in allUV:
				d = u'UV:%s不存在于对象UV集中'%(self.UV)
				pm.warning (d)
				state=False
				err= u'有不存在的UV,请通过控制台检查日志'
				return state,err
		except TypeError :
			d = u'UV:%s不存在于对象UV集中'%(self.UV)
			pm.warning (d)
			state=False
			err= u'有不存在的UV,请通过控制台检查日志'
			return state,err
		print u'UV:%s存在于对象UV集中,当前对象%s'%(self.UV,str(obj))
		err = self.preErr
		return state,err

	def prefixUV (self):
		#查询对象的所有UV,返回状态值和错误值,用于和其他方法交互
		err=u'初始化错误'
		state= False
		try:
			if self.selection is None:
				raise NoChoosedError
				return
			for obj in self.selection :
				stateUV,err = self.__checkUV(obj)
				if stateUV is False :
					continue
				#指定当前UV为self.UV
				pm.polyUVSet( obj, currentUVSet=True, uvSet=self.UV )
		except NoChoosedError:
			d=u'可能为无选择导致的程序错误'
			pm.warning(d)
			state = False
			err = d
			return state,err
		else :
			d=u'完成操作,运行时 %s'%err
			pm.warning(d)
			state = True
			return state,err

	def copyUV (self,uv2):
		#强制设定当前UV为工作UV,无法设定则不继续执行
		state,err = self.prefixUV()
		print u'完成预设操作'
		if state is True and err == self.preErr:
			try:
				if self.UV == uv2:
					raise SameUVError
			except SameUVError:
				d= u'无法将 UV 集复制到自身'
				pm.warning(d)
				return
			else:
				self.UV = uv2
				print self.UV
		else :
			d = u'工作UV错误或不存在,无法继续执行'
			print(d)
			pm.warning(d)
			return
		for obj in self.selection :
			state = self.__checkUV(obj)
			if not state :
				d = u'基础UV错误或不存在,无法继续执行'
				print(d)
				pm.warning(d)
				return
		    #将工作UV复制到当前UV
			pm.polyUVSet( obj, copy=True, nuv=uv2)
#启动UI界面
mayaWarpUI().showWindow()