import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from collections import defaultdict
import analysis
import plots
import config as c
import generateplots
from dataclass import Data
import yaml

from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.pyplot import close as closeFigure
from numpy.random import randint
from os.path import dirname, exists
from os import makedirs

# Commonly used LineEdit
class LineEdit(QFormLayout):
	def __init__(self, label, defaultText):
		super(LineEdit, self).__init__()
		self.ButtonLayout = QHBoxLayout()

		self.Label = QLabel(label)

		self.LineEdit = QLineEdit()
		self.LineEdit.setText(defaultText)
		self.LineEdit.setMaximumWidth(50)

		self.ButtonLayout.addWidget(self.LineEdit)
		self.insertRow(0,self.Label,self.ButtonLayout)

# Commonly used ComboBox
class ComboBox(QFormLayout):
	def __init__(self, label, items, defaultItem):
		super(ComboBox, self).__init__()

		self.Label = QLabel(label)

		self.ComboBox = QComboBox()
		self.ComboBox.setMaximumWidth(60)
		self.ComboBox.addItems(items)
		self.ComboBox.setCurrentIndex(defaultItem)

		self.insertRow(0,self.Label,self.ComboBox)

# Worker for the data analysis thread
class DataAnalysisWorker(QObject):
	finished = pyqtSignal()
	progress = pyqtSignal(int)

	def __init__(self, config):
		super(DataAnalysisWorker, self).__init__()
		self.config = config

	def run(self):
		analysis.DataAnalysis(self.config, self.progress)
		self.finished.emit()

# Plot tab
class Plot(QWidget):
	def __init__(self,parent,*args,**kwargs):
		super().__init__(parent,*args,**kwargs)
		self.parent = parent

		mainLayout = QHBoxLayout(self)

		# PLOTWINDOW
		self.plotWindowLayout = QVBoxLayout()
		mainLayout.addLayout(self.plotWindowLayout)

		# BUTTONS
		plotWindowButtonLayout = QHBoxLayout()
		self.plotWindowLayout.addLayout(plotWindowButtonLayout)

		self.showHistogramButton = QPushButton()
		self.showHistogramButton.setText("Histogram")
		self.showHistogramButton.clicked.connect(self.showHistogram)

		self.showHistogram2dButton = QPushButton()
		self.showHistogram2dButton.setText("2D Histogram")
		self.showHistogram2dButton.clicked.connect(self.showHistogram2D)

		self.showViolinplotButton = QPushButton()
		self.showViolinplotButton.setText("Violinplot")
		self.showViolinplotButton.clicked.connect(self.showViolinplot)

		self.showSimpleplotButton = QPushButton()
		self.showSimpleplotButton.setText("Simpleplot")
		self.showSimpleplotButton.clicked.connect(self.showSimplePlot)

		self.showECDFButton = QPushButton()
		self.showECDFButton.setText("ECDF")
		self.showECDFButton.clicked.connect(self.showECDF)

		plotWindowButtonLayout.addWidget(self.showHistogramButton)
		plotWindowButtonLayout.addWidget(self.showHistogram2dButton)
		plotWindowButtonLayout.addWidget(self.showViolinplotButton)
		plotWindowButtonLayout.addWidget(self.showSimpleplotButton)
		plotWindowButtonLayout.addWidget(self.showECDFButton)


		# CANVAS
		self.canvas = FigureCanvas()
		self.plotWindowLayout.addWidget(self.canvas)


		# PLOTPARAM
		plotParamLayout = QVBoxLayout()
		plotParamLayout.setAlignment(Qt.AlignTop)
		mainLayout.addLayout(plotParamLayout)

		# LOADDATA
		loadDataLayout = QVBoxLayout()
		loadDataLayout.setAlignment(Qt.AlignTop)
		loadDataBox = QGroupBox("General Options")
		loadDataBox.setLayout(loadDataLayout)
		plotParamLayout.addWidget(loadDataBox)

		# Load export config
		exportConfigLayout = QFormLayout()

		exportConfigLabel = QLabel("Load export config:")
		self.exportConfigLine = QLineEdit()
		self.exportConfigLine.setMaximumWidth(200)
		exportConfigLineAction = self.exportConfigLine.addAction(QIcon("folder.png"), QLineEdit.TrailingPosition)
		exportConfigLineAction.triggered.connect(self.chooseExportConfig)

		exportConfigLayout.insertRow(0,exportConfigLabel,self.exportConfigLine)
		loadDataLayout.addLayout(exportConfigLayout)

		self.useLatexCheckBox = QCheckBox()
		self.useLatexCheckBox.setText("Use LaTeX to generate text")
		loadDataLayout.addWidget(self.useLatexCheckBox)


		# HISTOGRAM
		self.histogramFrame = QWidget()
		self.histogramFrame.setVisible(False)
		self.histogramFrameLayout = QVBoxLayout()
		self.histogramFrame.setLayout(self.histogramFrameLayout)

		self.histogramLayout = QVBoxLayout()
		self.histogramLayout.setAlignment(Qt.AlignTop)
		self.histogramBox = QGroupBox("Histogram")
		self.histogramBox.setLayout(self.histogramLayout)
		self.histogramBox.setCheckable(True)
		self.histogramBox.setChecked(False)
		self.histogramBox.toggled.connect(lambda state: self.histogramFrame.setVisible(state!=Qt.Unchecked))
		self.histogramLayout.addWidget(self.histogramFrame)
		plotParamLayout.addWidget(self.histogramBox)

		# Widgets
		self.histogramGenerateCheckBox = QCheckBox()
		self.histogramGenerateCheckBox.setText("Save")
		self.histogramFrameLayout.addWidget(self.histogramGenerateCheckBox)

		self.histogramXdim = LineEdit("Width:", "10")
		self.histogramFrameLayout.addLayout(self.histogramXdim)		

		self.histogramYdim = LineEdit("Height:", "7")
		self.histogramFrameLayout.addLayout(self.histogramYdim)

		self.histogramColorHistogram = LineEdit("Color Histogram:", "tab:blue")
		self.histogramFrameLayout.addLayout(self.histogramColorHistogram)	

		self.histogramColorFit = LineEdit("Color Fit:", "red")
		self.histogramFrameLayout.addLayout(self.histogramColorFit)

		self.histogramColorKDE = LineEdit("Color KDE:", "orange")
		self.histogramFrameLayout.addLayout(self.histogramColorKDE)

		self.histogramAlphaHistogram = LineEdit("Alpha Histogram:", "0.7")
		self.histogramFrameLayout.addLayout(self.histogramAlphaHistogram)

		self.histogramScaleLine = LineEdit("Line Size:", "1")
		self.histogramFrameLayout.addLayout(self.histogramScaleLine)

		self.histogramLabelFontSize = LineEdit("Label Font Size:", "30")
		self.histogramFrameLayout.addLayout(self.histogramLabelFontSize)

		self.histogramTickFontSize = LineEdit("Tick Font Size:", "15")
		self.histogramFrameLayout.addLayout(self.histogramTickFontSize)

		self.histogramFileType = ComboBox("File Type:", ["pdf", "svg", "png", "jpeg"], 0)
		self.histogramFrameLayout.addLayout(self.histogramFileType)

		self.histogramDPI = LineEdit("DPI:", "300")
		self.histogramFrameLayout.addLayout(self.histogramDPI)



		# HISTOGRAM2D
		self.histogram2dFrame = QWidget()
		self.histogram2dFrame.setVisible(False)
		self.histogram2dFrameLayout = QVBoxLayout()
		self.histogram2dFrame.setLayout(self.histogram2dFrameLayout)

		self.histogram2dLayout = QVBoxLayout()
		self.histogram2dLayout.setAlignment(Qt.AlignTop)
		self.histogram2dBox = QGroupBox("2D Histogram")
		self.histogram2dBox.setLayout(self.histogram2dLayout)
		self.histogram2dBox.setCheckable(True)
		self.histogram2dBox.setChecked(False)
		self.histogram2dBox.toggled.connect(lambda state: self.histogram2dFrame.setVisible(state!=Qt.Unchecked))
		self.histogram2dLayout.addWidget(self.histogram2dFrame)
		plotParamLayout.addWidget(self.histogram2dBox)

		# Widgets
		self.histogram2dGenerateCheckBox = QCheckBox()
		self.histogram2dGenerateCheckBox.setText("Save")
		self.histogram2dFrameLayout.addWidget(self.histogram2dGenerateCheckBox)

		self.histogram2dErrorCheckBox = QCheckBox()
		self.histogram2dErrorCheckBox.setChecked(True)
		self.histogram2dErrorCheckBox.setText("Show error bars")
		self.histogram2dFrameLayout.addWidget(self.histogram2dErrorCheckBox)

		self.histogram2dBinMethod = ComboBox("Bin Method:", ["ss", "auto", "fd", "doane", "scott", "stone", "rice", "sturges", "sqrt"], 0)
		self.histogram2dFrameLayout.addLayout(self.histogram2dBinMethod)

		self.histogram2dNormalisation = ComboBox("Normalisation Method:", ["area", "amplitude"], 0)
		self.histogram2dFrameLayout.addLayout(self.histogram2dNormalisation)

		self.histogram2dXdim = LineEdit("Width:", "10")
		self.histogram2dFrameLayout.addLayout(self.histogram2dXdim)		

		self.histogram2dYdim = LineEdit("Height:", "7")
		self.histogram2dFrameLayout.addLayout(self.histogram2dYdim)

		self.histogram2dColorUnimodalScatter = LineEdit("Color Unimodal Points:", "red")
		self.histogram2dFrameLayout.addLayout(self.histogram2dColorUnimodalScatter)	

		self.histogram2dColorBimodalScatter = LineEdit("Color Bimodal Points:", "orange")
		self.histogram2dFrameLayout.addLayout(self.histogram2dColorBimodalScatter)

		self.histogram2dColorError = LineEdit("Color Error:", "black")
		self.histogram2dFrameLayout.addLayout(self.histogram2dColorError)

		self.histogram2dScaleScatter = LineEdit("Point Size:", "1.5")
		self.histogram2dFrameLayout.addLayout(self.histogram2dScaleScatter)

		self.histogram2dScaleError = LineEdit("Error Size:", "0.5")
		self.histogram2dFrameLayout.addLayout(self.histogram2dScaleError)

		self.histogram2dLabelFontSize = LineEdit("Label Font Size:", "30")
		self.histogram2dFrameLayout.addLayout(self.histogram2dLabelFontSize)

		self.histogram2dTickFontSize = LineEdit("Tick Font Size:", "15")
		self.histogram2dFrameLayout.addLayout(self.histogram2dTickFontSize)

		self.histogram2dFileType = ComboBox("File Type:", ["pdf", "svg", "png", "jpeg"], 0)
		self.histogram2dFrameLayout.addLayout(self.histogram2dFileType)

		self.histogram2dDPI = LineEdit("DPI:", "300")
		self.histogram2dFrameLayout.addLayout(self.histogram2dDPI)


		# VIOLINPLOT
		self.violinplotFrame = QWidget()
		self.violinplotFrame.setVisible(False)
		self.violinplotFrameLayout = QVBoxLayout()
		self.violinplotFrame.setLayout(self.violinplotFrameLayout)

		self.violinplotLayout = QVBoxLayout()
		self.violinplotLayout.setAlignment(Qt.AlignTop)
		self.violinplotBox = QGroupBox("Violinplot")
		self.violinplotBox.setLayout(self.violinplotLayout)
		self.violinplotBox.setCheckable(True)
		self.violinplotBox.setChecked(False)
		self.violinplotBox.toggled.connect(lambda state: self.violinplotFrame.setVisible(state!=Qt.Unchecked))
		self.violinplotLayout.addWidget(self.violinplotFrame)
		plotParamLayout.addWidget(self.violinplotBox)

		# Widgets
		self.violinplotGenerateCheckBox = QCheckBox()
		self.violinplotGenerateCheckBox.setText("Save")
		self.violinplotFrameLayout.addWidget(self.violinplotGenerateCheckBox)

		self.violinplotNormaliseCheckBox = QCheckBox()
		self.violinplotNormaliseCheckBox.setChecked(True)
		self.violinplotNormaliseCheckBox.setText("Normalise by area")
		self.violinplotFrameLayout.addWidget(self.violinplotNormaliseCheckBox)

		self.violinplotErrorCheckBox = QCheckBox()
		self.violinplotErrorCheckBox.setChecked(True)
		self.violinplotErrorCheckBox.setText("Show error bars")
		self.violinplotFrameLayout.addWidget(self.violinplotErrorCheckBox)

		self.violinplotXdim = LineEdit("Width:", "14")
		self.violinplotFrameLayout.addLayout(self.violinplotXdim)		

		self.violinplotYdim = LineEdit("Height:", "7")
		self.violinplotFrameLayout.addLayout(self.violinplotYdim)

		self.violinplotColorUnimodalScatter = LineEdit("Color Unimodal Points:", "red")
		self.violinplotFrameLayout.addLayout(self.violinplotColorUnimodalScatter)	

		self.violinplotColorBimodalScatter = LineEdit("Color Bimodal Points:", "orange")
		self.violinplotFrameLayout.addLayout(self.violinplotColorBimodalScatter)

		self.violinplotColorError = LineEdit("Color Error:", "black")
		self.violinplotFrameLayout.addLayout(self.violinplotColorError)

		self.violinplotColorViolin = LineEdit("Color Violin:", "#3397b5")
		self.violinplotFrameLayout.addLayout(self.violinplotColorViolin)

		self.violinplotScaleScatter = LineEdit("Point Size:", "0.5")
		self.violinplotFrameLayout.addLayout(self.violinplotScaleScatter)

		self.violinplotScaleError = LineEdit("Error Size:", "0.1")
		self.violinplotFrameLayout.addLayout(self.violinplotScaleError)

		self.violinplotLabelFontSize = LineEdit("Label Font Size:", "30")
		self.violinplotFrameLayout.addLayout(self.violinplotLabelFontSize)

		self.violinplotTickFontSize = LineEdit("Tick Font Size:", "15")
		self.violinplotFrameLayout.addLayout(self.violinplotTickFontSize)

		self.violinplotFileType = ComboBox("File Type:", ["pdf", "svg", "png", "jpeg"], 0)
		self.violinplotFrameLayout.addLayout(self.violinplotFileType)

		self.violinplotDPI = LineEdit("DPI:", "300")
		self.violinplotFrameLayout.addLayout(self.violinplotDPI)



		# SIMPLEPLOT
		self.simpleplotFrame = QWidget()
		self.simpleplotFrame.setVisible(False)
		self.simpleplotFrameLayout = QVBoxLayout()
		self.simpleplotFrame.setLayout(self.simpleplotFrameLayout)

		self.simpleplotLayout = QVBoxLayout()
		self.simpleplotLayout.setAlignment(Qt.AlignTop)
		self.simpleplotBox = QGroupBox("Simple plot")
		self.simpleplotBox.setLayout(self.simpleplotLayout)
		self.simpleplotBox.setCheckable(True)
		self.simpleplotBox.setChecked(False)
		self.simpleplotBox.toggled.connect(lambda state: self.simpleplotFrame.setVisible(state!=Qt.Unchecked))
		self.simpleplotLayout.addWidget(self.simpleplotFrame)
		plotParamLayout.addWidget(self.simpleplotBox)

		# Widgets
		self.simpleplotGenerateCheckBox = QCheckBox()
		self.simpleplotGenerateCheckBox.setText("Save")
		self.simpleplotFrameLayout.addWidget(self.simpleplotGenerateCheckBox)

		self.simpleplotXdim = LineEdit("Width:", "10")
		self.simpleplotFrameLayout.addLayout(self.simpleplotXdim)		

		self.simpleplotYdim = LineEdit("Height:", "7")
		self.simpleplotFrameLayout.addLayout(self.simpleplotYdim)

		self.simpleplotColorScatter = LineEdit("Color Points:", "red")
		self.simpleplotFrameLayout.addLayout(self.simpleplotColorScatter)	

		self.simpleplotColorError = LineEdit("Color Error:", "Black")
		self.simpleplotFrameLayout.addLayout(self.simpleplotColorError)

		self.simpleplotScaleScatter = LineEdit("Point Size:", "5")
		self.simpleplotFrameLayout.addLayout(self.simpleplotScaleScatter)

		self.simpleplotScaleError = LineEdit("Error Size:", "0.5")
		self.simpleplotFrameLayout.addLayout(self.simpleplotScaleError)

		self.simpleplotLabelFontSize = LineEdit("Label Font Size:", "30")
		self.simpleplotFrameLayout.addLayout(self.simpleplotLabelFontSize)

		self.simpleplotTickFontSize = LineEdit("Tick Font Size:", "15")
		self.simpleplotFrameLayout.addLayout(self.simpleplotTickFontSize)

		self.simpleplotFileType = ComboBox("File Type:", ["pdf", "svg", "png", "jpeg"], 0)
		self.simpleplotFrameLayout.addLayout(self.simpleplotFileType)

		self.simpleplotDPI = LineEdit("DPI:", "300")
		self.simpleplotFrameLayout.addLayout(self.simpleplotDPI)



		#ECDF
		self.ECDFFrame = QWidget()
		self.ECDFFrame.setVisible(False)
		self.ECDFFrameLayout = QVBoxLayout()
		self.ECDFFrame.setLayout(self.ECDFFrameLayout)

		self.ECDFLayout = QVBoxLayout()
		self.ECDFLayout.setAlignment(Qt.AlignTop)
		self.ECDFBox = QGroupBox("ECDF")
		self.ECDFBox.setLayout(self.ECDFLayout)
		self.ECDFBox.setCheckable(True)
		self.ECDFBox.setChecked(False)
		self.ECDFBox.toggled.connect(lambda state: self.ECDFFrame.setVisible(state!=Qt.Unchecked))
		self.ECDFLayout.addWidget(self.ECDFFrame)
		plotParamLayout.addWidget(self.ECDFBox)

		# Widgets
		self.ECDFGenerateCheckBox = QCheckBox()
		self.ECDFGenerateCheckBox.setText("Save")
		self.ECDFFrameLayout.addWidget(self.ECDFGenerateCheckBox)

		self.ECDFXdim = LineEdit("Width:", "10")
		self.ECDFFrameLayout.addLayout(self.ECDFXdim)		

		self.ECDFYdim = LineEdit("Height:", "7")
		self.ECDFFrameLayout.addLayout(self.ECDFYdim)

		self.ECDFColorScatter = LineEdit("Color Points:", "Black")
		self.ECDFFrameLayout.addLayout(self.ECDFColorScatter)	

		self.ECDFColorFit = LineEdit("Color Fit:", "Black")
		self.ECDFFrameLayout.addLayout(self.ECDFColorFit)

		self.ECDFAlphaFit = LineEdit("Alpha Fit:", "0.3")
		self.ECDFFrameLayout.addLayout(self.ECDFAlphaFit)

		self.ECDFScaleLine = LineEdit("Line Size:", "0.5")
		self.ECDFFrameLayout.addLayout(self.ECDFScaleLine)

		self.ECDFScaleScatter = LineEdit("Point Size:", "10")
		self.ECDFFrameLayout.addLayout(self.ECDFScaleScatter)

		self.ECDFLabelFontSize = LineEdit("Label Font Size:", "30")
		self.ECDFFrameLayout.addLayout(self.ECDFLabelFontSize)

		self.ECDFTickFontSize = LineEdit("Tick Font Size:", "15")
		self.ECDFFrameLayout.addLayout(self.ECDFTickFontSize)

		self.ECDFFileType = ComboBox("File Type:", ["pdf", "svg", "png", "jpeg"], 0)
		self.ECDFFrameLayout.addLayout(self.ECDFFileType)

		self.ECDFDPI = LineEdit("DPI:", "300")
		self.ECDFFrameLayout.addLayout(self.ECDFDPI)


		# GENERATE BUTTON
		self.generateButton = QPushButton()
		self.generateButton.setText("Save")
		self.generateButton.setMaximumWidth(100)
		plotParamLayout.addWidget(self.generateButton)
		self.generateButton.clicked.connect(self.generatePlots)

	def showHistogram(self):
		closeFigure("all")
		dataList = self.setConfigsAndGetData()
		plots.setFont()

		rand = randint(low = 0, high = len(dataList))
		figure = plots.HistogramPlot(dataList[rand])
		self.plotWindowLayout.removeWidget(self.canvas)
		self.canvas.deleteLater()
		self.canvas = FigureCanvas(figure)
		self.plotWindowLayout.addWidget(self.canvas)

	def showHistogram2D(self):
		closeFigure("all")
		dataList = self.setConfigsAndGetData()
		plots.setFont()

		Histogram2D = plots.Histogram2D(dataList)
		figure = plots.Histogram2DPlot(Histogram2D)
		self.plotWindowLayout.removeWidget(self.canvas)
		self.canvas.deleteLater()
		self.canvas = FigureCanvas(figure)
		self.plotWindowLayout.addWidget(self.canvas)

	def showViolinplot(self):
		closeFigure("all")
		dataList = self.setConfigsAndGetData()
		plots.setFont()

		figure = plots.ViolinPlot(dataList)
		self.plotWindowLayout.removeWidget(self.canvas)
		self.canvas.deleteLater()
		self.canvas = FigureCanvas(figure)
		self.plotWindowLayout.addWidget(self.canvas)

	def showSimplePlot(self):
		closeFigure("all")
		dataList = self.setConfigsAndGetData()
		plots.setFont()

		figure = plots.SimplePlot(dataList)
		self.plotWindowLayout.removeWidget(self.canvas)
		self.canvas.deleteLater()
		self.canvas = FigureCanvas(figure)
		self.plotWindowLayout.addWidget(self.canvas)

	def showECDF(self):
		closeFigure("all")
		dataList = self.setConfigsAndGetData()
		plots.setFont()

		rand = randint(low = 0, high = len(dataList))
		figure = plots.ECDF(dataList[rand])
		self.plotWindowLayout.removeWidget(self.canvas)
		self.canvas.deleteLater()
		self.canvas = FigureCanvas(figure)
		self.plotWindowLayout.addWidget(self.canvas)

	def setConfigsAndGetData(self):
		configPlot = self.constructConfigPlot()
		with open(self.data_dir[0]) as file:
			configExport = yaml.load(file, Loader = yaml.Loader)

		c.Config(configExport["Config"])
		c.PlotConfig(configPlot)

		dataList = []
		for key in configExport["Data"]:
			dataList.append(Data(**configExport["Data"][key]))

		return dataList

	def chooseExportConfig(self):
		self.data_dir = QFileDialog.getOpenFileName(None, "Select Export Config")
		try:
			self.exportConfigLine.setText(self.data_dir[0])
		except NameError:
			None

	def generatePlots(self):
		closeFigure("all")
		dataList = self.setConfigsAndGetData()

		outputDir = dirname(self.data_dir[0])
		if not exists(outputDir):
			makedirs(outputDir)

		generateplots.generateplots(dataList, outputDir)

	def constructConfigPlot(self):
		configPlot = defaultdict(dict)

		# GENERAL
		if self.useLatexCheckBox.checkState() == Qt.Checked:
			configPlot["General"]["LaTeX"] = True
		else:
			configPlot["General"]["LaTeX"] = False


		# HISTOGRAM

		if self.histogramGenerateCheckBox.checkState() == Qt.Checked:
			configPlot["Histogram"]["Generate"] = True
		else:
			configPlot["Histogram"]["Generate"] = False

		configPlot["Histogram"]["XDim"] = int(self.histogramXdim.LineEdit.text())	

		configPlot["Histogram"]["YDim"] = int(self.histogramYdim.LineEdit.text())

		configPlot["Histogram"]["ColorHistogram"] = self.histogramColorHistogram.LineEdit.text()

		configPlot["Histogram"]["ColorFit"] = self.histogramColorFit.LineEdit.text()

		configPlot["Histogram"]["ColorKDE"] = self.histogramColorKDE.LineEdit.text()

		configPlot["Histogram"]["AlphaHistogram"] = float(self.histogramAlphaHistogram.LineEdit.text())

		configPlot["Histogram"]["ScaleLine"] = float(self.histogramScaleLine.LineEdit.text())

		configPlot["Histogram"]["LabelFontSize"] = float(self.histogramLabelFontSize.LineEdit.text())

		configPlot["Histogram"]["TickFontSize"] = float(self.histogramTickFontSize.LineEdit.text())

		configPlot["Histogram"]["OutputType"] = self.histogramFileType.ComboBox.currentText()

		configPlot["Histogram"]["DPI"] = int(self.histogramDPI.LineEdit.text())

		# HISTOGRAM2D

		if self.histogram2dGenerateCheckBox.checkState() == Qt.Checked:
			configPlot["Histogram2D"]["Generate"] = True
		else:
			configPlot["Histogram2D"]["Generate"] = False

		if self.histogram2dErrorCheckBox.checkState() == Qt.Checked:
			configPlot["Histogram2D"]["Error"] = True
		else:
			configPlot["Histogram2D"]["Error"] = False

		configPlot["Histogram2D"]["Bin"] = self.histogram2dBinMethod.ComboBox.currentText()

		configPlot["Histogram2D"]["Normalisation"] = self.histogram2dNormalisation.ComboBox.currentText()

		configPlot["Histogram2D"]["XDim"] = int(self.histogram2dXdim.LineEdit.text())

		configPlot["Histogram2D"]["YDim"] = int(self.histogram2dYdim.LineEdit.text())

		configPlot["Histogram2D"]["ColorUnimodalScatter"] = self.histogram2dColorUnimodalScatter.LineEdit.text()

		configPlot["Histogram2D"]["ColorBimodalScatter"] = self.histogram2dColorBimodalScatter.LineEdit.text()

		configPlot["Histogram2D"]["ColorError"] = self.histogram2dColorError.LineEdit.text()

		configPlot["Histogram2D"]["ScaleScatter"] = float(self.histogram2dScaleScatter.LineEdit.text())

		configPlot["Histogram2D"]["ScaleError"] = float(self.histogram2dScaleError.LineEdit.text())

		configPlot["Histogram2D"]["LabelFontSize"] = float(self.histogram2dLabelFontSize.LineEdit.text())

		configPlot["Histogram2D"]["TickFontSize"] = float(self.histogram2dTickFontSize.LineEdit.text())

		configPlot["Histogram2D"]["OutputType"] = self.histogram2dFileType.ComboBox.currentText()

		configPlot["Histogram2D"]["DPI"] = int(self.histogram2dDPI.LineEdit.text())

		# VIOLINPLOT

		if self.violinplotGenerateCheckBox.checkState() == Qt.Checked:
			configPlot["Violinplot"]["Generate"] = True
		else:
			configPlot["Violinplot"]["Generate"] = False

		configPlot["Violinplot"]["XDim"] = int(self.violinplotXdim.LineEdit.text())

		configPlot["Violinplot"]["YDim"] = int(self.violinplotYdim.LineEdit.text())

		if self.violinplotNormaliseCheckBox.checkState() == Qt.Checked:
			configPlot["Violinplot"]["Normalisation"] = True
		else:
			configPlot["Violinplot"]["Normalisation"] = False

		if self.violinplotErrorCheckBox.checkState() == Qt.Checked:
			configPlot["Violinplot"]["Error"] = True
		else:
			configPlot["Violinplot"]["Error"] = False

		configPlot["Violinplot"]["ColorUnimodalScatter"] = self.violinplotColorUnimodalScatter.LineEdit.text()

		configPlot["Violinplot"]["ColorBimodalScatter"] = self.violinplotColorBimodalScatter.LineEdit.text()

		configPlot["Violinplot"]["ColorError"] = self.violinplotColorError.LineEdit.text()

		configPlot["Violinplot"]["ColorViolin"] = self.violinplotColorViolin.LineEdit.text()

		configPlot["Violinplot"]["ScaleScatter"] = float(self.violinplotScaleScatter.LineEdit.text())

		configPlot["Violinplot"]["ScaleError"] = float(self.violinplotScaleError.LineEdit.text())

		configPlot["Violinplot"]["LabelFontSize"] = float(self.violinplotLabelFontSize.LineEdit.text())

		configPlot["Violinplot"]["TickFontSize"] = float(self.violinplotTickFontSize.LineEdit.text())

		configPlot["Violinplot"]["OutputType"] = self.violinplotFileType.ComboBox.currentText()

		configPlot["Violinplot"]["DPI"] = int(self.violinplotDPI.LineEdit.text())

		# SIMPLEPLOT

		if self.simpleplotGenerateCheckBox.checkState() == Qt.Checked:
			configPlot["Simpleplot"]["Generate"] = True
		else:
			configPlot["Simpleplot"]["Generate"] = False

		configPlot["Simpleplot"]["XDim"] = int(self.simpleplotXdim.LineEdit.text())

		configPlot["Simpleplot"]["YDim"] = int(self.simpleplotYdim.LineEdit.text())

		configPlot["Simpleplot"]["ColorScatter"] = self.simpleplotColorScatter.LineEdit.text()

		configPlot["Simpleplot"]["ColorError"] = self.simpleplotColorError.LineEdit.text()

		configPlot["Simpleplot"]["ScaleScatter"] = float(self.simpleplotScaleScatter.LineEdit.text())

		configPlot["Simpleplot"]["ScaleError"] = float(self.simpleplotScaleError.LineEdit.text())

		configPlot["Simpleplot"]["LabelFontSize"] = float(self.simpleplotLabelFontSize.LineEdit.text())

		configPlot["Simpleplot"]["TickFontSize"] = float(self.simpleplotTickFontSize.LineEdit.text())

		configPlot["Simpleplot"]["OutputType"] = self.simpleplotFileType.ComboBox.currentText()

		configPlot["Simpleplot"]["DPI"] = int(self.simpleplotDPI.LineEdit.text())


		# ECDF

		if self.ECDFGenerateCheckBox.checkState() == Qt.Checked:
			configPlot["ECDF"]["Generate"] = True
		else:
			configPlot["ECDF"]["Generate"] = False

		configPlot["ECDF"]["XDim"] = int(self.ECDFXdim.LineEdit.text())

		configPlot["ECDF"]["YDim"] = int(self.ECDFYdim.LineEdit.text())

		configPlot["ECDF"]["ColorScatter"] = self.ECDFColorScatter.LineEdit.text()

		configPlot["ECDF"]["ColorFit"] = self.ECDFColorFit.LineEdit.text()

		configPlot["ECDF"]["AlphaFit"] = float(self.ECDFAlphaFit.LineEdit.text())

		configPlot["ECDF"]["ScaleLine"] = float(self.ECDFScaleLine.LineEdit.text())

		configPlot["ECDF"]["ScaleScatter"] = float(self.ECDFScaleScatter.LineEdit.text())

		configPlot["ECDF"]["LabelFontSize"] = float(self.ECDFLabelFontSize.LineEdit.text())

		configPlot["ECDF"]["TickFontSize"] = float(self.ECDFTickFontSize.LineEdit.text())

		configPlot["ECDF"]["OutputType"] = self.ECDFFileType.ComboBox.currentText()

		configPlot["ECDF"]["DPI"] = int(self.ECDFDPI.LineEdit.text())

		return configPlot

class DataAnalysis(QWidget):
	def __init__(self,parent,*args,**kwargs):
		super().__init__(parent,*args,**kwargs)
		self.parent = parent

		mainLayout = QVBoxLayout(self)

		# FILEPARAM
		fileParamLayout = QVBoxLayout()
		fileParamLayout.setAlignment(Qt.AlignTop)
		fileParamBox = QGroupBox("File Parameters")
		fileParamBox.setLayout(fileParamLayout)
		mainLayout.addWidget(fileParamBox)


		# Root data folder
		dataFolderLayout = QFormLayout()

		# Label
		dataFolderLabel = QLabel("Data Folder:")

		# Line edit
		self.dataFolderLine = QLineEdit()
		self.dataFolderLine.setMaximumWidth(500)
		dataFolderLineAction = self.dataFolderLine.addAction(QIcon("folder.png"), QLineEdit.TrailingPosition)
		dataFolderLineAction.triggered.connect(self.chooseDataFolder)

		# Add widgets to layouts
		dataFolderLayout.insertRow(0,dataFolderLabel,self.dataFolderLine)
		fileParamLayout.addLayout(dataFolderLayout)


		# Blacklist folder
		blacklistFolder_Layout = QVBoxLayout()
		blacklistFolder_Top_Layout = QFormLayout()
		blacklistFolder_Button_Layout = QHBoxLayout()

		# List
		self.blacklistFolder_List = QListWidget()
		self.blacklistFolder_List.setVisible(False)

		# List button
		self.blacklistFolder_ListButton = QToolButton()
		self.blacklistFolder_ListButton.clicked.connect(lambda: self.blacklistFolder_List.setVisible(not self.blacklistFolder_List.isVisible()))
		self.blacklistFolder_ListButton.setIcon(QIcon("list.png"))

		# Add button
		self.blacklistFolder_AddButton = QToolButton()
		self.blacklistFolder_AddButton.clicked.connect(self.choose_blacklist_directory)
		self.blacklistFolder_AddButton.setIcon(QIcon("add.png"))

		# Remove button
		self.blacklistFolder_RemoveButton = QToolButton()
		self.blacklistFolder_RemoveButton.clicked.connect(self.blacklistFolder_List_RemoveItems)
		self.blacklistFolder_RemoveButton.setIcon(QIcon("remove.png"))

		# Label
		blacklistFolder_Label = QLabel("Blacklist:")

		# Add widgets to layouts
		blacklistFolder_Button_Layout.addWidget(self.blacklistFolder_ListButton)
		blacklistFolder_Button_Layout.addWidget(self.blacklistFolder_AddButton)
		blacklistFolder_Button_Layout.addWidget(self.blacklistFolder_RemoveButton)
		blacklistFolder_Top_Layout.insertRow(0,blacklistFolder_Label,blacklistFolder_Button_Layout)
		blacklistFolder_Layout.addLayout(blacklistFolder_Top_Layout)
		blacklistFolder_Layout.addWidget(self.blacklistFolder_List)
		fileParamLayout.addLayout(blacklistFolder_Layout)


		# Blacklist concentrations
		blacklistConc_Layout = QVBoxLayout()
		blacklistConc_Top_Layout = QFormLayout()
		blacklistConc_Button_Layout = QHBoxLayout()

		# List
		self.blacklistConc_List = QListWidget()
		self.blacklistConc_List.setVisible(False)

		# List button
		self.blacklistConc_ListButton = QToolButton()		
		self.blacklistConc_ListButton.clicked.connect(lambda: self.blacklistConc_List.setVisible(not self.blacklistConc_List.isVisible()))
		self.blacklistConc_ListButton.setIcon(QIcon("list.png"))

		# Line edit
		self.blacklistConc_LineEdit = QLineEdit()
		self.blacklistConc_LineEdit.setMaximumWidth(60)
		self.blacklistConc_LineEdit_Action = self.blacklistConc_LineEdit.addAction(QIcon("add.png"), QLineEdit.TrailingPosition)		
		self.blacklistConc_LineEdit_Action.triggered.connect(self.blacklistConc_LineEdit_Add)

		# Remove button
		self.blacklistConc_RemoveButton = QToolButton()
		self.blacklistConc_RemoveButton.clicked.connect(self.blacklistConc_List_RemoveItems)
		self.blacklistConc_RemoveButton.setIcon(QIcon("remove.png"))

		# Label
		blacklistConc_Label = QLabel("Blacklist Concentrations:")

		# Add widgets to layouts
		blacklistConc_Button_Layout.addWidget(self.blacklistConc_ListButton)
		blacklistConc_Button_Layout.addWidget(self.blacklistConc_LineEdit)
		blacklistConc_Button_Layout.addWidget(self.blacklistConc_RemoveButton)
		blacklistConc_Top_Layout.insertRow(0,blacklistConc_Label,blacklistConc_Button_Layout)
		blacklistConc_Layout.addLayout(blacklistConc_Top_Layout)
		blacklistConc_Layout.addWidget(self.blacklistConc_List)
		fileParamLayout.addLayout(blacklistConc_Layout)



		# DATAPARAM
		dataParamLayout = QVBoxLayout()
		dataParamLayout.setAlignment(Qt.AlignTop)
		dataParamBox = QGroupBox("Data Parameters")
		dataParamBox.setLayout(dataParamLayout)
		mainLayout.addWidget(dataParamBox)


		# Minimum RMS
		minRMS_Layout = QFormLayout()
		minRMS_Button_Layout = QHBoxLayout()

		# Label
		minRMS_Label = QLabel("Minimum RMS:")

		# Line edit
		self.minRMS_LineEdit = QLineEdit()
		self.minRMS_LineEdit.setMaximumWidth(50)

		# Add widgets to layouts
		minRMS_Button_Layout.addWidget(self.minRMS_LineEdit)
		minRMS_Layout.insertRow(0,minRMS_Label,minRMS_Button_Layout)
		dataParamLayout.addLayout(minRMS_Layout)


		# Maximum RMS
		maxRMS_Layout = QFormLayout()
		maxRMS_Button_Layout = QHBoxLayout()

		# Label
		maxRMS_Label = QLabel("Maximum RMS:")

		# Line edit
		self.maxRMS_LineEdit = QLineEdit()
		self.maxRMS_LineEdit.setMaximumWidth(50)

		# Add widgets to layouts
		maxRMS_Button_Layout.addWidget(self.maxRMS_LineEdit)
		maxRMS_Layout.insertRow(0,maxRMS_Label,maxRMS_Button_Layout)
		dataParamLayout.addLayout(maxRMS_Layout)


		# Bin method
		bin_Layout = QFormLayout()
		bin_Button_Layout = QHBoxLayout()

		# Label
		bin_Label = QLabel("Bin Method:")

		# Combo box
		self.bin_ComboBox = QComboBox()
		self.bin_ComboBox.setMaximumWidth(60)
		self.bin_ComboBox.addItems(["ss", "auto", "fd", "doane", "scott", "stone", "rice", "sturges", "sqrt"])
		self.bin_ComboBox.setCurrentIndex(0)

		# Add widgets to layouts
		bin_Button_Layout.addWidget(self.bin_ComboBox)
		bin_Layout.insertRow(0,bin_Label,bin_Button_Layout)
		dataParamLayout.addLayout(bin_Layout)

		#kde_method
		dataBinningKDE_Layout = QFormLayout()
		dataBinningKDE_Button_Layout = QHBoxLayout()

		# Label
		dataBinningKDE_Label = QLabel("KDE Method:")

		# Combo box
		self.dataBinningKDE_ComboBox = QComboBox()
		self.dataBinningKDE_ComboBox.setMaximumWidth(60)
		self.dataBinningKDE_ComboBox.addItems(["ssv", "ss", "scott", "silverman"])
		self.dataBinningKDE_ComboBox.setCurrentIndex(0)

		# Add widgets to layouts
		dataBinningKDE_Button_Layout.addWidget(self.dataBinningKDE_ComboBox)
		dataBinningKDE_Layout.insertRow(0,dataBinningKDE_Label,dataBinningKDE_Button_Layout)
		dataParamLayout.addLayout(dataBinningKDE_Layout)



		# FITTINGPARAM
		fitParamLayout = QVBoxLayout()
		fitParamLayout.setAlignment(Qt.AlignTop)
		fitParamBox = QGroupBox("Fit Parameters")
		fitParamBox.setLayout(fitParamLayout)
		mainLayout.addWidget(fitParamBox)


		# Initial a parameter 
		p0a_Layout = QFormLayout()

		# Line edit
		self.p0a_LineEdit = QLineEdit()
		self.p0a_LineEdit.setMaximumWidth(50)
		self.p0a_LineEdit.setText("30")

		# Label
		p0a_Label = QLabel("p0 a:")

		# Add widgets to layouts
		p0a_Layout.insertRow(0,p0a_Label,self.p0a_LineEdit)
		fitParamLayout.addLayout(p0a_Layout)


		# Initial b parameter
		p0b_Layout = QFormLayout()

		# Label
		p0b_Label = QLabel("p0 b:")
		p0b_LabelPlaceholder = QLabel("Placeholder. Needs to be implemented.")

		# Add widgets to layouts
		p0b_Layout.insertRow(0,p0b_Label,p0b_LabelPlaceholder)
		fitParamLayout.addLayout(p0b_Layout)

		# Initial c parameter
		p0c_Layout = QFormLayout()

		# Line edit
		self.p0c_LineEdit = QLineEdit()
		self.p0c_LineEdit.setMaximumWidth(50)
		self.p0c_LineEdit.setText("6")

		# Label
		p0c_Label = QLabel("p0 c:")

		# Add widgets to layouts
		p0c_Layout.insertRow(0,p0c_Label,self.p0c_LineEdit)
		fitParamLayout.addLayout(p0c_Layout)



		# MODE DETECTION
		modeDetection_Layout = QVBoxLayout()
		modeDetection_Box = QGroupBox("Mode Detection")
		fitParamLayout.addWidget(modeDetection_Box)
		modeDetection_Box.setLayout(modeDetection_Layout)


		# Check box
		self.modeDetectionBoolean_CheckBox = QCheckBox()
		self.modeDetectionBoolean_CheckBox.setText("Enabled")
		self.modeDetectionBoolean_CheckBox.stateChanged.connect(self.modeDetectionBoolean_Enable)
		modeDetection_Layout.addWidget(self.modeDetectionBoolean_CheckBox)


		# Height
		Height_Layout = QFormLayout()

		# Line edit
		self.Height_LineEdit = QLineEdit()
		self.Height_LineEdit.setMaximumWidth(50)
		self.Height_LineEdit.setText("0.01")

		# Label
		Height_Label = QLabel("Minimal Height:")

		# Add widgets to layouts
		Height_Layout.insertRow(0,Height_Label,self.Height_LineEdit)
		modeDetection_Layout.addLayout(Height_Layout)


		# Prominence
		Prominence_Layout = QFormLayout()

		# Line edit
		self.Prominence_LineEdit = QLineEdit()
		self.Prominence_LineEdit.setMaximumWidth(50)
		self.Prominence_LineEdit.setText("0.01")

		# Label
		Prominence_Label = QLabel("Minimal Prominence:")

		# Add widgets to layout
		Prominence_Layout.insertRow(0,Prominence_Label,self.Prominence_LineEdit)
		modeDetection_Layout.addLayout(Prominence_Layout)


		# Distance
		Distance_Layout = QFormLayout()
		Distance_Button_Layout = QHBoxLayout()

		# Line edit
		self.Distance_LineEdit = QLineEdit()
		self.Distance_LineEdit.setMaximumWidth(50)
		self.Distance_LineEdit.setText("20")

		# Label
		Distance_Label = QLabel("Minimum Distance:")

		# Add widgets to layout
		Distance_Button_Layout.addWidget(self.Distance_LineEdit)
		Distance_Layout.insertRow(0,Distance_Label,Distance_Button_Layout)
		modeDetection_Layout.addLayout(Distance_Layout)


		# Start with Mode Detection disabled
		self.modeDetectionBoolean_CheckBox.setCheckState(Qt.Unchecked)
		self.Distance_LineEdit.setEnabled(False)
		self.Height_LineEdit.setEnabled(False)
		self.Prominence_LineEdit.setEnabled(False)


		#PROGRESSBAR
		progressBar_Layout = QHBoxLayout()
		self.progressBar = QProgressBar()
		self.progressBar.setValue(0)

		# Start button
		self.startButton = QPushButton()
		self.startButton.setText("Start")
		self.startButton.clicked.connect(self.startAnalysis)

		# Progress bar
		progressBar_Layout.addWidget(self.progressBar)
		progressBar_Layout.addWidget(self.startButton)
		mainLayout.addLayout(progressBar_Layout)

	def chooseDataFolder(self):
		self.data_dir = QFileDialog.getExistingDirectory(None, "Select Folder")
		try:
			self.dataFolderLine.setText(self.data_dir)
		except NameError:
			None

	def choose_blacklist_directory(self):
		curr_blacklist_List = QFileDialog.getExistingDirectory(None, "Select Folder")
		try:
			if len(self.blacklistFolder_List.findItems(curr_blacklist_List, Qt.MatchExactly)) == 0 and curr_blacklist_List != "":
				self.blacklistFolder_List.addItem(curr_blacklist_List)
		except NameError:
			None
		except TypeError:
			None

	def blacklistFolder_List_RemoveItems(self):
		for item in self.blacklistFolder_List.selectedItems():
			self.blacklistFolder_List.takeItem(self.blacklistFolder_List.row(item))

	def choose_blacklistConc_directory(self):
		curr_blacklistConc_List = QFileDialog.getExistingDirectory(None, "Select Folder")
		try:
			if len(self.blacklistConc_List.findItems(curr_blacklistConc_List, Qt.MatchExactly)) == 0:
				self.blacklistConc_List.addItem(curr_blacklistConc_List)
		except NameError:
			None
		except TypeError:
			None

	def blacklistConc_List_RemoveItems(self):
		for item in self.blacklistConc_List.selectedItems():
			self.blacklistConc_List.takeItem(self.blacklistConc_List.row(item))

	def blacklistConc_LineEdit_Add(self):
		if self.blacklistConc_LineEdit.text() != "":
			self.blacklistConc_List.addItem(self.blacklistConc_LineEdit.text())
		self.blacklistConc_LineEdit.clear()

	def modeDetectionBoolean_Enable(self):
		if self.modeDetectionBoolean_CheckBox.checkState() == Qt.Unchecked:
			self.Distance_LineEdit.setEnabled(False)
			self.Height_LineEdit.setEnabled(False)
			self.Prominence_LineEdit.setEnabled(False)
		else:
			self.Distance_LineEdit.setEnabled(True)
			self.Height_LineEdit.setEnabled(True)
			self.Prominence_LineEdit.setEnabled(True)

	def construct_yaml(self):
		export_dict = defaultdict(dict)
		
		# FILEPARAM
		export_dict["FileParam"]["RootDir"] = self.data_dir

		blacklist_list = []
		for k in range(self.blacklistFolder_List.count()):
			blacklist_list.append(self.blacklistFolder_List.item(k).text())
		export_dict["FileParam"]["Blacklist"] = blacklist_list

		blacklistConc_list = []
		for k in range(self.blacklistConc_List.count()):
			blacklistConc_list.append(float(self.blacklistConc_List.item(k).text()))
		export_dict["FileParam"]["BlacklistConc"] = blacklistConc_list


		# DATAPARAM
		export_dict["DataParam"]["MinRMS"] = float(self.minRMS_LineEdit.text())
		export_dict["DataParam"]["MaxRMS"] = float(self.maxRMS_LineEdit.text())

		export_dict["DataParam"]["Bin"] = self.bin_ComboBox.currentText()
		export_dict["DataParam"]["KDE"] = self.dataBinningKDE_ComboBox.currentText()

		# FITTINGPARAM
		export_dict["FittingParam"]["p0a"] = float(self.p0a_LineEdit.text())
		export_dict["FittingParam"]["p0b"] = None # Needs to be implemented
		export_dict["FittingParam"]["p0c"] = float(self.p0c_LineEdit.text())

		if self.modeDetectionBoolean_CheckBox.checkState() == Qt.Checked:
			export_dict["FittingParam"]["ModeDetection"] = True
		else:
			export_dict["FittingParam"]["ModeDetection"] = False

		export_dict["FittingParam"]["ModeDetectionHeight"] = float(self.Height_LineEdit.text())
		export_dict["FittingParam"]["ModeDetectionProminence"] = float(self.Prominence_LineEdit.text())
		export_dict["FittingParam"]["ModeDetectionDistance"] = float(self.Distance_LineEdit.text())

		return export_dict

	def startAnalysis(self):
		config = self.construct_yaml()
		self.parent.tabs.setTabEnabled(1, False)
		self.progressBar.setValue(0)
		self.RunDataAnalysisThread(config)

	def RunDataAnalysisThread(self, config):
		self.thread = QThread()
		self.worker = DataAnalysisWorker(config)
		self.worker.moveToThread(self.thread)

		self.thread.started.connect(self.worker.run)
		self.worker.finished.connect(self.thread.quit)
		self.worker.finished.connect(self.worker.deleteLater)
		self.thread.finished.connect(self.thread.deleteLater)
		self.worker.progress.connect(self.reportProgress)

		self.thread.start()

		self.startButton.setEnabled(False)
		self.thread.finished.connect(
			lambda: self.startButton.setEnabled(True)
		)
		self.thread.finished.connect(lambda: self.parent.tabs.setTabEnabled(1, True))

	def reportProgress(self, i):
		self.progressBar.setValue(i)


class MainWindow(QMainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.title = 'TPM Data Analysis'
		self.setWindowTitle(self.title)
		self.main = QWidget()
		self.setCentralWidget(self.main)
		mainLayout = QVBoxLayout(self.main)

		self.tabs = QTabWidget()
		self.tabDataAnalysis = DataAnalysis(self)
		self.tabPlot = Plot(self)

		self.tabs.addTab(self.tabDataAnalysis, "Data Analysis")
		self.tabs.addTab(self.tabPlot, "Plot")

		mainLayout.addWidget(self.tabs)

	def disablePlotTab():
		self.tabs.setTabEnabled(1, False)

def main():
	app = QApplication(sys.argv)
	ex = MainWindow()
	ex.setGeometry(100,100,1100,720)
	ex.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()