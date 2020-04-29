import os
import sys
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication, QPushButton,QFileDialog
import pickle 
from audio import record_word 
from audio import play_word, save_to_file
from functools import partial
import json

######################GLOBAL#######################
DIR = os.path.abspath(os.path.dirname(__file__))
LABELS = {
	"الطويل": "taweel",
	"المديد": "madeed",
	"البسيط": "baseet",
	"الوافر": "wafir",
	"الكامل": "kamil",
	"الهزج": "hazj",
	"الرجز": "rajz",
	"الرمل": "ramal",
	"السريع": "sareea",
	"المنسرح": "monsareh",
	"الخفيف": "khafeef",
	"المضارع": "modareea",
	"المقتضب": "mogtadab",
	"المجتث": "mojtath",
	"المتقارب": "motagarib",
	"المحدث": "mohdath"
}

QDialog, Ui_Dialog = uic.loadUiType(os.path.join(DIR, "ba77ar_labeler.ui"), resource_suffix='') 

with open("data.json") as f:
	DATA_DICT = json.loads(f.read())
	DATA_KEYS = list(DATA_DICT.keys())
	DATA = [DATA_DICT[k]["bayt"] for k in DATA_KEYS]
	DATA_LABELS = {k: LABELS[DATA_DICT[k]["bahar"]] for k in DATA_KEYS}

######################UTILS########################
def _error(msg):
	msg = QMessageBox()
	msg.setIcon(QMessageBox.Critical)
	msg.setText(msg)  	
	msg.setWindowTitle("Alert")
	msg.setStandardButtons(QMessageBox.Close)
	retval = msg.exec_()
#--------------------------------------------------
def notify(msg,ntype="error"):
	if ntype == "error":
		_error(msg)
#--------------------------------------------------
def getDirBrowser():
	dialog = QFileDialog()
	dialog.setFileMode(QFileDialog.Directory)
	dialog.setOption(QFileDialog.ShowDirsOnly)
	directory = dialog.getExistingDirectory(None, 'Choose Directory', os.path.curdir)
	return str(directory)
#--------------------------------------------------
def saveFileBrowser():
	fileName = QFileDialog.getSaveFileName(None, 'Save Project', '.')
	return str(fileName[0])
#--------------------------------------------------
def openFileBrowser():
	fileName = QFileDialog.getOpenFileName(None, 'Open Project', '.')
	return str(fileName[0])
#--------------------------------------------------
def browse(btype = "folder"):
	if btype == "folder":
		return getDirBrowser()
	elif btype == "savefile":
		return saveFileBrowser()
	elif btype == "openfile":
		return openFileBrowser()
#--------------------------------------------------
######################CORE CLASS#########################
class Project:
	def __init__(self,path=None,new=True):
		self._path = path
		self._new = new
		self._recordings = {}
		self._labels = DATA_LABELS
	def record(self,word):
		data,sample_width = record_word()
		self._recordings[word] = (data,sample_width)
	def play(self,word):
		data = self._recordings[word][0]
		play_word(data)
	def has_recording(self,key):
		return key in self._recordings
	def completed(self,key):
		return key in self._recordings and key in self._labels
	def missing_one(self,key):
		return key in self._recordings or key in self._labels
	def has_label(self,key):
		return key in self._labels
	def get_label(self,key):
		return self._labels[key]
	def label(self,key,btnName):
		self._labels[key] = LABELS[btnName]
	def save(self,ofile=None):
		if not ofile and not self._path:
			return
		elif not ofile:
			ofile = self._path

		with open(f'{ofile}.rec', 'wb') as handle:
			pickle.dump(self._recordings, handle)
		with open(f'{ofile}.json',"w") as f:
			f.write(json.dumps(self._labels))
		self._path = ofile
	def publish(self, pathName,subjectName):
		sPath = f'{pathName}/{subjectName}'
		if not os.path.exists(sPath):
			os.mkdir(sPath)
		for k, v in self._labels.items():
			if k in self._recordings:
				rec,sample_width = self._recordings[k]
				filename = f'{sPath}/{k}_{v}.wav'
				save_to_file(rec,sample_width,filename)
	@classmethod
	def load(cls,ofile):
		project = Project(ofile.strip(".json"),new=False)
		recfile = ofile.replace(".json",".rec")
		jsonfile = ofile
		with open(recfile, 'rb') as handle:
			project._recordings = pickle.load(handle)
		with open(jsonfile, 'r') as f:
			project._labels = json.loads(f.read())
		return project

######################GUI Class#########################
class Wazzan(QDialog, Ui_Dialog):
	def __init__(self, parent=None):
		super(Wazzan,self).__init__(parent)
		self.setupUi(self)
		self.wordsList.addItems(DATA_KEYS)
		self._openFlag = False
		self._project = None
		self._firstLoad = True
		self._selectedItem = -1
		self.actionNew_Project.triggered.connect(self.new_project)
		self.actionSave_Project.triggered.connect(self.save_project)
		self.actionOpen_Project.triggered.connect(self.load_project)
		self.pbNextFrame.clicked.connect(self.next_frame)
		self.pbPrevFrame.clicked.connect(self.prev_frame)
		self.wordsList.itemSelectionChanged.connect(self.on_wordsListSelectionChanged)
		self.wordsList.setEnabled(False)
		self.pbDatasetPath.clicked.connect(self.publishPath)
		self.currentLabel = None
		self.subjectNameLine.textChanged.connect(self.checkPublishButton)
		self.publishPathLine.textChanged.connect(self.checkPublishButton)
		self.pbPublish.clicked.connect(self.publish)


		self.labelsButton = self.labelWidget.findChildren(QPushButton)
		for b in self.labelsButton:
			b.toggled.connect(partial(self.onLabelClicked,b))
	def checkPublishButton(self):
		if self.publishPathLine.text().strip() == "" or self.subjectNameLine.text().strip() == "":
			self.pbPublish.setEnabled(False)
		else:
			self.pbPublish.setEnabled(True)
	def record(self):
		index = int(self.wordsList.currentRow())
		word = str(self.wordsList.item(index).text())
		self.pbRecord.setEnabled(False)
		self.pbPlay.setEnabled(False)
		self._project.record(word)
		if self._project.completed(DATA_KEYS[index]):
			self.wordsList.item(index).setBackground(QtGui.QColor("green"))
		elif self._project.completed(DATA_KEYS[index]):
			self.wordsList.item(index).setBackground(QtGui.QColor("yellow"))
		self.update_view()
	def play(self):
		index = int(self.wordsList.currentRow())
		word = str(self.wordsList.item(index).text())
		self._project.play(word)
	def new_project(self):
		if self._openFlag:
			self.save_project()
		self._project = Project()
		self.enable_actions()
		self._selectedItem = -1
		self.publishInfoWidget.setEnabled(True)
		self.pbRecord.setEnabled(False)
		self.pbPlay.setEnabled(False)
		self.refresh_color()
	def enable_actions(self):
		self.actionSave_Project.setEnabled(True)
		self.pbRecord.setEnabled(True)
		self.pbPlay.setEnabled(True)
		self.wordsList.setEnabled(True)
	def save_project(self):
		if self._project._path:
			self._project.save()
		else:
			oPath = browse("savefile")
			if not oPath:
				return
			self._project.save(oPath)
	def refresh_color(self):
		for i in range(self.wordsList.count()):
			if self._project.completed(DATA_KEYS[i]):
				self.wordsList.item(i).setBackground(QtGui.QColor("green"))
			elif self._project.missing_one(DATA_KEYS[i]):
				self.wordsList.item(i).setBackground(QtGui.QColor("yellow"))
			else:
				self.wordsList.item(i).setBackground(QtGui.QColor("white"))
	def refresh_color_selectred(self):
		if self._project.completed(DATA_KEYS[self._selectedItem]):
			self.wordsList.item(self._selectedItem).setBackground(QtGui.QColor("green"))
		elif self._project.missing_one(DATA_KEYS[self._selectedItem]):
			self.wordsList.item(self._selectedItem).setBackground(QtGui.QColor("yellow"))
		else:
			self.wordsList.item(self._selectedItem).setBackground(QtGui.QColor("white"))
	def load_project(self):
		oPath = browse("openfile")
		if not oPath:
			return
		if self._openFlag:
			self.save_project()
		self._project = Project.load(oPath)
		self.enable_actions()
		self._selectedItem = -1
		self.publishInfoWidget.setEnabled(True)
		self.pbRecord.setEnabled(False)
		self.pbPlay.setEnabled(False)
		self.refresh_color()
		self.update_view()
	def publishPath(self):
		oPath = browse("folder")
		if not oPath:
			return
		self.publishPathLine.setText(oPath)
	def enable_labels(self,enable):
		for b in self.labelsButton:
			b.setEnabled(enable)
			b.repaint()
	def onLabelClicked(self,button):
		if not self.currentLabel:
			self.currentLabel = button
			self._project.label(DATA_KEYS[self._selectedItem],button.text())
			self.refresh_color_selectred()
			return
		if button == self.currentLabel:
			self.currentLabel = None
			self.refresh_color_selectred()
		else:
			self.currentLabel.setChecked(False)
			self.currentLabel = button
			self._project.label(DATA_KEYS[self._selectedItem],button.text())
			self.refresh_color_selectred()
	def on_wordsListSelectionChanged(self):
		index = int(self.wordsList.currentRow())
		self._selectedItem = index
		self.update_view()
	def on_pbRecord_released(self):
		self.record()
	def on_pbPlay_released(self):
		self.play()
	def update_view(self):
		#print(WORDS_AR[self._selectedItem],self._selectedItem)
		self.lblInstance.setText(DATA[self._selectedItem])
		self.pbRecord.setEnabled(True)
		index = int(self.wordsList.currentRow())
		if index <0:
			return
		if not self._project.has_recording(DATA_KEYS[self._selectedItem]):
			self.refresh_color_selectred()
			self.pbPlay.setEnabled(False)
			self.enable_labels(False)
			self.labelWidget.update()
		else:
			self.pbPlay.setEnabled(True)
			self.labelWidget.setEnabled(True)
			self.enable_labels(True)
		if self._project.has_label(DATA_KEYS[self._selectedItem]):
			self.refresh_color_selectred()
			label = self._project.get_label(DATA_KEYS[self._selectedItem])
			
			for b in self.labelsButton:
				if LABELS[b.text()] == label:
					b.setChecked(True)
				else:
					b.setChecked(False)
				b.repaint()
		else:
			for b in self.labelsButton:
				b.setChecked(False)
				b.repaint()


		#print("update_view",self._selectedItem)
		if self._selectedItem  == 0:
			self.pbPrevFrame.setEnabled(False)
		else:
			self.pbPrevFrame.setEnabled(True)

		if self._selectedItem  == len(DATA) -1:
			self.pbNextFrame.setEnabled(False)
		else:
			self.pbNextFrame.setEnabled(True)
	def next_frame(self):
		self.wordsList.setCurrentRow(self._selectedItem+1)
	def prev_frame(self):
		self.wordsList.setCurrentRow(self._selectedItem-1)
	def publish(self):
		self._project.publish(self.publishPathLine.text(),self.subjectNameLine.text())

if __name__ == '__main__':
	app = QApplication(sys.argv)
	form = Wazzan(None)
	form.show()
	sys.exit(app.exec_())
