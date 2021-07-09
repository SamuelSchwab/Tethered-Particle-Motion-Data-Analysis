import numpy as np
import config as c
import fit
from adaptivekde.sshist import sshist
from os import getcwd, makedirs
from os.path import exists
import matplotlib.pyplot as plt
from matplotlib import rc, rcParams
from statsmodels.distributions.empirical_distribution import ECDF as smECDF
from scipy.stats import norm
from matplotlib.cbook import violin_stats

# All plot are generated in ggplot's style
plt.style.use('ggplot')

# Sets font for the text in plots
def setFont():
	if c.PlotConfig.get("General.LaTeX"):
		rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
		rc('text', usetex=True)
	else:
		rc('font', **{'family': 'sans-serif', 'sans-serif': ['DejaVu Sans']})
		rc('text', usetex=False)


#Find ideal binwidth on x axis so that we don't have overlap elements/elements touching each other.
def x_binwidth(x):
	if len(x) > 1 :
		delta_concentration = []
		x = -np.sort(-x)
		for ind_concentration in range(0,(len(x) - 1)):
			delta_concentration.append(x[ind_concentration] - x[ind_concentration + 1])
		delta_concentration = np.asarray(delta_concentration)
		max_binwidth = np.amin(delta_concentration)
	else:
		max_binwidth = np.asarray([50])
	return max_binwidth



class Histogram2D():

	def __init__(self, dataList):

		self.dataList = dataList
		self.data = []
		self.concentration = []
		for d in self.dataList:
			self.data.append(d.filterData())
			self.concentration.append(d.concentration)

		self.calculation()


	def calculation(self):

		def bin(method, y):
			if type(method) == str:
				if method == "ss":
					numberBins,_,_,_,_ = sshist(y, N=np.arange(20, 201, 1))
					_, yBinEdges = np.histogram(y, bins=numberBins)
				else:
					_, yBinEdges = np.histogram(y, bins=method)
			elif type(method) == int:
				numberBins = method
				_, yBinEdges = np.histogram(y, bins=numberBins)
			return yBinEdges

		#Make 1 dimensional arrays for both x and y.
		x = []
		for index in range(0, len(self.data)):
			x.append(np.full(self.data[index].shape, self.concentration[index]))
		xNotFlat = np.asarray(x, dtype = object)
		x = np.concatenate(xNotFlat).ravel()
		y = np.concatenate(self.data).ravel()

		#Load/calculate # bins in x and y direction. For x we minimise # bins while preventing bins from touching other bins directly on the horizontal axis. For y i recommend taking the square root of # data points in y dimension. Normally that would overestimate # bins but we are not plotting a normal histogram.
		self.yBinEdges = bin(c.PlotConfig.get("Histogram2D.Bin"), y)

		indexes = np.unique(self.concentration, return_index=True)[1]
		concentrationUnique = [self.concentration[index] for index in sorted(indexes)]
		xBinWidth = (x_binwidth(np.asarray(concentrationUnique))/2)

		#Make lists of bin edges of the x axis
		self.xBinEdges = []
		for currentConc in sorted(concentrationUnique):
			self.xBinEdges.append(currentConc - xBinWidth*0.5)
			self.xBinEdges.append(currentConc + xBinWidth*0.5)
		
		#Normalize each datagroup either by area or amplitude
		numberDuplicates = []
		individualHistograms = []
		for i in range(0, len(self.data)):
			ind = np.where(self.concentration == xNotFlat[i][0])
			numberDuplicates.append(len(ind[0]))
			if c.PlotConfig.get("Histogram2D.Normalisation") == "area":
				hist, self.xBinEdges, self.yBinEdges = np.histogram2d(xNotFlat[i], self.data[i], bins=(self.xBinEdges,self.yBinEdges), density = True)
				hist = hist / numberDuplicates[i]
			elif c.PlotConfig.get("Histogram2D.Normalisation") == "amplitude":
				hist, self.xBinEdges, self.yBinEdges = np.histogram2d(xNotFlat[i], self.data[i], bins=[self.xBinEdges,self.yBinEdges])
				with np.errstate(divide='ignore',invalid='ignore'):
					hist = hist / hist.max(axis=1, keepdims=True)
			individualHistograms.append(hist.T)

		#Make an index list of concentrations for each unique concentration
		indexList = []
		for currentConc in concentrationUnique:
			ind = np.where(self.concentration == currentConc)
			indexList.append(ind[0])

		#Add histograms of the same concentration to each other
		self.histogramList = []
		for i in indexList:
			if len(i) > 1:
				currentHistogram = individualHistograms[i[0]]
				for k in range(1, len(i)):
					currentHistogram = currentHistogram + individualHistograms[i[k]]
				currentHistogram[currentHistogram == 0] = np.nan
				self.histogramList.append(currentHistogram)
			else:
				currentHistogram = individualHistograms[i[0]]
				currentHistogram[currentHistogram == 0] = np.nan
				self.histogramList.append(currentHistogram)

		#If we normalised by amplitude we need to again normalise since we did an addition. We don't need to normalize by area again because we divided the histogram by # experiments.
		if c.PlotConfig.get("Histogram2D.Normalisation") == "amplitude":
			for i in range(0, len(self.histogramList)):
				with np.errstate(divide='ignore',invalid='ignore'):
					self.histogramList[i] = self.histogramList[i] / np.nanmax(self.histogramList[i])

		#Find our maximum color for the color scale
		maxList = []
		for i in self.histogramList:
			maxList.append(np.nanmax(i))
		self.maxDensity = max(maxList)

def Histogram2DPlot(histogram2D):
	# Plot parameters
	xDim = c.PlotConfig.get("Histogram2D.XDim")
	yDim = c.PlotConfig.get("Histogram2D.YDim")
	error = c.PlotConfig.get("Histogram2D.Error")
	colorUnimodalScatter = c.PlotConfig.get("Histogram2D.ColorUnimodalScatter")
	colorBimodalScatter = c.PlotConfig.get("Histogram2D.ColorBimodalScatter")
	colorError = c.PlotConfig.get("Histogram2D.ColorError")
	scaleScatter = c.PlotConfig.get("Histogram2D.ScaleScatter")
	scaleError = c.PlotConfig.get("Histogram2D.ScaleError")
	labelFontSize = c.PlotConfig.get("Histogram2D.LabelFontSize")
	tickFontSize = 	c.PlotConfig.get("Histogram2D.TickFontSize")
	dpi = c.PlotConfig.get("Histogram2D.DPI")
	outputType = c.PlotConfig.get("Histogram2D.OutputType")

	# Find the bin width in the x dimension. This is used as a scaling factor.
	xBinWidth = histogram2D.xBinEdges[1] - histogram2D.xBinEdges[0]

	# Plot our 2 dimensional histogram
	fig, ax = plt.subplots(figsize=(xDim, yDim))
	for histogram in histogram2D.histogramList:
		pc = plt.pcolormesh(histogram2D.xBinEdges, histogram2D.yBinEdges, histogram, cmap="binary", vmax = histogram2D.maxDensity, vmin = 0, zorder = 1)
	cb = plt.colorbar()
	ax.set_xlabel("Concentration (nM)", fontsize = labelFontSize)
	ax.set_ylabel("RMS (nm)", fontsize = labelFontSize)
	if c.PlotConfig.get("Histogram2D.Normalisation") == "amplitude":
		cb.set_label('Relative amplitude', fontsize = labelFontSize)
	elif c.PlotConfig.get("Histogram2D.Normalisation") == "area":
		cb.set_label('Density', fontsize = labelFontSize)
	for d in histogram2D.dataList:
		if d.mode == "unimodal":
			plt.scatter(d.concentration, d.pOpt[1], s = (xBinWidth*xDim*scaleScatter), marker='.', linewidth = 0, edgecolors='None', facecolors=colorUnimodalScatter, zorder = 3)
			if error:
				plt.errorbar(d.concentration, d.pOpt[1], yerr = (d.pVar[1] * len(d.filterData()))**0.5, fmt = "none", 
					markersize = (np.sqrt(xBinWidth*xDim*scaleScatter)/4), capsize = (np.sqrt(xBinWidth*xDim*scaleScatter)/4), 
					elinewidth = (np.sqrt(xBinWidth*xDim*scaleError)/4), capthick = (np.sqrt(xBinWidth*xDim*scaleError)/4), ecolor = colorError, zorder = 2)
		if d.mode == "bimodal":
			plt.scatter(d.concentration, d.pOpt[1], s = (xBinWidth*xDim*scaleScatter), marker='.', linewidth = 0, edgecolors='None', facecolors=colorBimodalScatter)
			plt.scatter(d.concentration, d.pOpt[4], s = (xBinWidth*xDim*scaleScatter), marker='.', linewidth = 0, edgecolors='None', facecolors=colorBimodalScatter)
	ax.grid(color="#E5E5E5")
	ax.set_facecolor(color = "#FFFFFF")
	ax.spines['bottom'].set_color('0.5')
	ax.spines['top'].set_color('0.5')
	ax.spines['right'].set_color('0.5')
	ax.spines['left'].set_color('0.5')
	ax.tick_params(axis='x', labelsize=tickFontSize)
	ax.tick_params(axis='y', labelsize=tickFontSize)
	cb.ax.tick_params(labelsize=tickFontSize) 
	ax.set_xlim(left=np.min(histogram2D.concentration) - xBinWidth, right=np.max(histogram2D.concentration) + xBinWidth)
	fig.tight_layout()
	return fig


def ErrorBars(dataList):

	# Get necessary data from the data classes
	data, concentration, varianceOfMean, pOpt, mode = [], [], [], [], []
	for d in dataList:
		data.append(d.filterData()) 
		concentration.append(d.concentration)
		varianceOfMean.append(d.pVar[1])	
		pOpt.append(d.pOpt)
		mode.append(d.mode)

	concentration, varianceOfMean, pOpt, mode = np.asarray(concentration), np.asarray(varianceOfMean), np.asarray(pOpt), np.asarray(mode)

	indexes = np.unique(concentration, return_index=True)[1]
	concentrationUnique = [concentration[index] for index in sorted(indexes)]

	# Calculate variance of distribution from variance of the mean
	variance = []
	for i in range(0, len(varianceOfMean)):
		variance.append(varianceOfMean[i] * len(data[i]))
	variance = np.asarray(variance)

	# Calculate means and errors
	error = []
	mean = []
	for currentConc in concentrationUnique:
		ind = np.where(concentration == currentConc)
		if "bimodal" in set(mode[ind[0]]):
			print("foo") # Unfinished.
		else:
			mean.append(np.mean(pOpt[ind[0]][:,1]))
			error.append((np.sum(variance[ind[0]]) / len(variance[ind[0]])**2)**0.5)

	return concentrationUnique, mean, error


def SimplePlot(dataList):

	# Plot parameters
	xDim = c.PlotConfig.get("Simpleplot.XDim")
	yDim = c.PlotConfig.get("Simpleplot.YDim")
	colorScatter = c.PlotConfig.get("Simpleplot.ColorScatter")
	colorError = c.PlotConfig.get("Simpleplot.ColorError")
	scaleScatter = c.PlotConfig.get("Simpleplot.ScaleScatter")
	scaleError = c.PlotConfig.get("Simpleplot.ScaleError")
	labelFontSize = c.PlotConfig.get("Simpleplot.LabelFontSize")
	tickFontSize = c.PlotConfig.get("Simpleplot.TickFontSize")
	dpi = c.PlotConfig.get("Simpleplot.DPI")
	outputType = c.PlotConfig.get("Simpleplot.OutputType")

	# Calculate the error bars. Returns concentrations (=x), means (=y) and errors of the means. If mode detection was enabled we don't generate a real plot since I haven't added bimodal error bar calculation yet
	if not c.Config.get("FittingParam.ModeDetection"):
		x, y, error = ErrorBars(dataList)

		# Find the bin width in the x dimension. This is used as a scaling factor.
		xBinWidth = x_binwidth(np.asarray(x))/2

		# Plot the error bars and the mean values.
		fig, ax = plt.subplots(figsize=(xDim, yDim))
		ax.set_xlabel("Concentration (nM)", fontsize = labelFontSize)
		ax.set_ylabel("RMS (nm)", fontsize = labelFontSize)
		ax.tick_params(axis='x', labelsize=tickFontSize)
		ax.tick_params(axis='y', labelsize=tickFontSize)

		plt.scatter(x, y, s = (xBinWidth*xDim*scaleScatter), marker='.', linewidth = 0, edgecolors='None', facecolors=colorScatter, zorder = 2)
		plt.errorbar(x, y, yerr = error, fmt = "none", markersize = (np.sqrt(xBinWidth*xDim*scaleScatter)/6.2831), 
			capsize = (np.sqrt(xBinWidth*xDim*scaleScatter)/6.2831), elinewidth = (np.sqrt(xBinWidth*xDim*scaleError)/6.2831), 
			capthick = (np.sqrt(xBinWidth*xDim*scaleError)/6.2831), ecolor = colorError, zorder = 1)

		ax.set_ylim(bottom = dataList[0].minRMS, top = dataList[0].maxRMS)
		fig.tight_layout()
	else:
		fig, ax = plt.subplots(figsize=(xDim, yDim))
		plt.scatter(1,1)
		ax.set_xlabel("Dummy Figure (disable mode detection)")
		ax.set_ylabel("Dummy Figure")
	return fig

def HistogramPlot(d):

	def fitLine():
		x = np.arange(d.minRMS, d.maxRMS, 1)
		if d.mode == "unimodal":
			y = fit.unimodal(x, d.pOpt[0], d.pOpt[1], d.pOpt[2]) / 2
		elif d.mode == "bimodal":
			y = fit.bimodal(x, d.pOpt[0], d.pOpt[1], d.pOpt[2], d.pOpt[3], d.pOpt[4], d.pOpt[5]) / 2
		y = y / np.sum(y)
		return x, y

	# Plot parameters
	xDim = c.PlotConfig.get("Histogram.XDim")
	yDim = c.PlotConfig.get("Histogram.YDim")
	colorHistogram = c.PlotConfig.get("Histogram.ColorHistogram")
	colorFit = c.PlotConfig.get("Histogram.ColorFit")
	colorKDE = c.PlotConfig.get("Histogram.ColorKDE")
	alphaHistogram = c.PlotConfig.get("Histogram.AlphaHistogram")
	scaleLine = c.PlotConfig.get("Histogram.ScaleLine")
	labelFontSize = c.PlotConfig.get("Histogram.LabelFontSize")
	tickFontSize = c.PlotConfig.get("Histogram.TickFontSize")
	dpi = c.PlotConfig.get("Histogram.DPI")
	outputType = c.PlotConfig.get("Histogram.OutputType")

	x, y = fitLine()
	dataFiltered = d.filterData()

	fig, ax1 = plt.subplots(figsize=(xDim, yDim))
	ax1.hist(dataFiltered, bins = d.binEdges, label='Histogram', alpha=alphaHistogram, color=colorHistogram, histtype="stepfilled")
	ax1.set_xlabel("RMS (nm)", fontsize=labelFontSize)
	ax1.set_ylabel("Counts", fontsize=labelFontSize)
	ax1.tick_params(axis='x', labelsize=tickFontSize)
	ax1.tick_params(axis='y', labelsize=tickFontSize)

	ax2 = ax1.twinx()
	ax2.plot(d.xKDE, d.yKDE, color=colorKDE, zorder = 1, label='KDE', linewidth = 2.8 * scaleLine)
	ax2.plot(x, y, '--', color=colorFit, zorder = 2, label='Fit', linewidth = 2.8 * scaleLine)
	ax2.set_ylabel("Density", fontsize=labelFontSize)
	ax2.tick_params(axis='y', labelsize=tickFontSize)
	ax2.grid(b=False, axis = "y")
	ax2.set_ylim(bottom=0)
	fig.legend(loc="upper left", bbox_to_anchor=(0,1), bbox_transform=ax1.transAxes, frameon = False, fontsize = tickFontSize)
	fig.tight_layout()
	return fig

def ECDF(d):

	def mystep(x,y, ax=None, where='post', **kwargs):
		assert where in ['post', 'pre']
		x = np.array(x)
		y = np.array(y)
		if where=='post': y_slice = y[:-1]
		if where=='pre': y_slice = y[1:]
		X = np.c_[x[:-1],x[1:],x[1:]]
		Y = np.c_[y_slice, y_slice, np.zeros_like(x[:-1])*np.nan]
		if not ax: ax=plt.gca()
		return ax.plot(X.flatten(), Y.flatten(), **kwargs)

	xDim = c.PlotConfig.get("ECDF.XDim")
	yDim = c.PlotConfig.get("ECDF.YDim")
	colorScatter = c.PlotConfig.get("ECDF.ColorScatter")
	colorFit = c.PlotConfig.get("ECDF.ColorFit")
	alphaFit = c.PlotConfig.get("ECDF.AlphaFit")
	scaleLine = c.PlotConfig.get("ECDF.ScaleLine")
	scaleScatter = c.PlotConfig.get("ECDF.ScaleScatter")
	labelFontSize = c.PlotConfig.get("ECDF.LabelFontSize")
	tickFontSize = c.PlotConfig.get("ECDF.TickFontSize")
	dpi = c.PlotConfig.get("ECDF.DPI")
	outputType = c.PlotConfig.get("ECDF.OutputType")

	dataFiltered = d.filterData()

	ecdf = smECDF(dataFiltered)

	theory_x = np.arange(d.minRMS, d.maxRMS, 0.5)
	pdf = norm.pdf(theory_x, loc=d.pOpt[1], scale=d.pOpt[2])
	cdf = np.cumsum(pdf * 0.5)

	fig, ax = plt.subplots(figsize=(xDim, yDim))
	mystep(ecdf.x, ecdf.y, lw = scaleScatter/20, color = colorScatter)
	plt.plot(theory_x, cdf, "--", color=colorFit, lw = scaleLine, alpha = alphaFit, label = "Theoretical CDF")
	plt.scatter(ecdf.x, ecdf.y, marker='.', linewidths = 0, color=colorScatter, s = scaleScatter, label = "Empirical CDF")
	ax.set_xlabel("RMS (nm)", fontsize = labelFontSize)
	ax.set_ylabel("Cumulative probability", fontsize = labelFontSize)
	ax.tick_params(axis="x", labelsize=tickFontSize)
	ax.tick_params(axis="y", labelsize=tickFontSize)
	ax.set_xlim(left=d.minRMS, right=d.maxRMS)
	fig.legend(loc="upper left", bbox_to_anchor=(0,1), bbox_transform=ax.transAxes, frameon = False, fontsize = tickFontSize)
	return fig

def ViolinPlot(dataList):

	#Callable functions for matplotlib's Violin() function. Allows us to manually feed it the KDE.
	def violinplot_kde():
		def vdensity(data, coords):
			nonlocal p
			y_kernel = y_kernel_list_merged[p]
			return y_kernel
		return vdensity

	def custom_violin_stats(data):
		results = violin_stats(data, violinplot_kde(), points = int(1e3))

		return results

	xDim = c.PlotConfig.get("Violinplot.XDim")
	yDim = c.PlotConfig.get("Violinplot.YDim")
	normalisation = c.PlotConfig.get("Violinplot.Normalisation")
	error = c.PlotConfig.get("Violinplot.Error")
	colorUnimodalScatter = c.PlotConfig.get("Violinplot.ColorUnimodalScatter")
	colorBimodalScatter = c.PlotConfig.get("Violinplot.ColorBimodalScatter")
	colorError = c.PlotConfig.get("Violinplot.ColorError")
	colorViolin = c.PlotConfig.get("Violinplot.ColorViolin")
	scaleScatter = c.PlotConfig.get("Violinplot.ScaleScatter")
	scaleError = c.PlotConfig.get("Violinplot.ScaleError")
	labelFontSize = c.PlotConfig.get("Violinplot.LabelFontSize")
	tickFontSize = 	c.PlotConfig.get("Violinplot.TickFontSize")
	dpi = c.PlotConfig.get("Violinplot.DPI")
	outputType = c.PlotConfig.get("Violinplot.OutputType")

	data = []
	concentration = []
	yKDE = []
	for d in dataList:
		data.append(d.filterData())
		concentration.append(d.concentration)
		yKDE.append(d.yKDE)

	vpstats1_list = []
	y_kernel_list_merged = []

	indexes = np.unique(concentration, return_index=True)[1]
	x_unique = [concentration[index] for index in sorted(indexes)]

	#Merge KDE's from the same concentration and renormalize them. 
	p = -1
	for item in x_unique:
		p = p + 1
		ind = np.where(concentration == item)
		temp = yKDE[ind[0][0]]
		if len(ind[0]) > 1:
			for i in range(1,len(ind[0])):
				temp = temp + yKDE[ind[0][i]]
		temp = temp / len(ind[0])

		y_kernel_list_merged.append(temp)
		vpstats1 = custom_violin_stats([dataList[0].minRMS, dataList[0].maxRMS])
		vpstats1_list.append(vpstats1[0])

	#Calculate our width
	y_kernel_max_list = []
	for array in y_kernel_list_merged:
		y_kernel_max_list.append(max(array))
	max_density = max(y_kernel_max_list)
	y_kernel_max_list = y_kernel_max_list / max_density

	width_temp = x_binwidth(np.asarray(x_unique))
	width = []
	if normalisation:
		for index in range(0, len(y_kernel_max_list)):
			width.append(width_temp * y_kernel_max_list[index])
	else:
		for index in range(0, len(y_kernel_max_list)):
			width.append(width_temp)
	width = np.asarray(width)

	fig, ax = plt.subplots(figsize=(xDim,yDim))

	vplot = ax.violin(vpstats1_list, vert=True, showmeans=False, showextrema=False, showmedians=False, positions = x_unique, widths = width)

	for pc in vplot['bodies']:
		pc.set_facecolor(colorViolin)
		pc.set_alpha(1)

	for d in dataList:
		if d.mode == "unimodal":
			plt.scatter(d.concentration, d.pOpt[1], s = (width.max()*xDim*scaleScatter), marker='.', linewidth = 0, edgecolors='None', facecolors=colorUnimodalScatter, zorder = 3)
			if error:
				plt.errorbar(d.concentration, d.pOpt[1], yerr = (d.pVar[1] * len(d.filterData()))**0.5, 
					fmt = "none", markersize = (np.sqrt(width.max()*xDim*scaleScatter)/4), 
					capsize = (np.sqrt(width.max()*xDim*scaleScatter)/4), elinewidth = (np.sqrt(width.max()*xDim*scaleError)/4), 
					capthick = (np.sqrt(width.max()*xDim*scaleError)/4), ecolor = colorError, zorder = 2)
		if d.mode == "bimodal":
			plt.scatter(d.concentration, d.pOpt[1], s = (width.max()*xDim*scaleScatter), marker='.', linewidth = 0, edgecolors='None', facecolors=colorBimodalScatter, zorder = 3)
			plt.scatter(d.concentration, d.pOpt[4], s = (width.max()*xDim*scaleScatter), marker='.', linewidth = 0, edgecolors='None', facecolors=colorBimodalScatter, zorder = 3)
	ax.set_xlabel("Concentration (nM)", fontsize = labelFontSize)
	ax.set_ylabel("RMS (nm)", fontsize = labelFontSize)
	ax.tick_params(axis='x', labelsize=tickFontSize)
	ax.tick_params(axis='y', labelsize=tickFontSize)
	ax.set_xlim(left=np.min(concentration) - width.max(), right= np.max(concentration) + width.max())
	fig.tight_layout()
	return fig