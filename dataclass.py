from scipy.optimize import curve_fit
from scipy.signal import find_peaks
from typing import List
from adaptivekde.sshist import sshist
from adaptivekde.sskernel import sskernel
from adaptivekde.ssvkernel import ssvkernel
from dataclasses import dataclass, field, asdict

import numpy as np
import config as c
import fit

# Our data class that holds all information of a dataset.
# When initializing, provide path, data and concentration.
@dataclass
class Data:
	path: list
	data: list
	concentration: float
	minRMS: float
	maxRMS: float

	xKDE: List[float] = field(default_factory=list)
	yKDE: List[float] = field(default_factory=list)

	binEdges: List[float] = field(default_factory=list)

	pOpt: List[float] = field(default_factory=list)
	pVar: List[float] = field(default_factory=list)
	mode: str = "placeholder"


	def filterData(self):
		return self.data[np.where(np.logical_and(self.data>=self.minRMS, self.data<=self.maxRMS))]		

	def generateKDE(self, KDE):
		dataFiltered = self.filterData()
		tin = np.linspace(self.minRMS, self.maxRMS, int(1e3))

		if KDE == "ssv":
			self.yKDE, self.xKDE, _, _, _, _, _ = ssvkernel(dataFiltered, tin = tin)
		elif KDE == "ss":
			self.yKDE, self.xKDE, _, _, _, _, _ = sskernel(dataFiltered, tin = tin)
		else:
			kde = gaussian_kde(dataFiltered, bw_method = KDE)
			self.yKDE = kde.evaluate(points = tin)
			self.xKDE = tin

	def generateBinEdges(self):
		def bin(method):
			# If config setting DataParam.Bin is a string, user specified a method to determine bins automatically
			if type(method) == str:
				if method == "ss":
					numberBins,_,_,_,_ = sshist(dataFiltered, N=np.arange(20,100, 1))
					_, binEdges = np.histogram(dataFiltered, bins=numberBins)
				else:
					_, binEdges = np.histogram(dataFiltered, bins=method)

			# If config setting DataParam.Bin is a dictionary, user specified bins for certain data sets
			# Check if this is one of such datasets 
			elif type(method) == dict and (self.path[1] + "/" + self.path[2]) in method:
				_, binEdges = np.histogram(dataFiltered, bins=method)
			return binEdges

		dataFiltered = self.filterData()
		self.binEdges = bin(c.Config.get("DataParam.Bin"))

	def fitData(self):

		def defaultUnimodalFitting():
			max_value = np.amax(histogram)
			max_index = np.where(histogram == max_value)[0]
			p0b = binCenters[max_index]
			print(p0b)
			print(self.path)
			popt, pcov = curve_fit(fit.unimodal,binCenters,histogram, p0=[c.Config.get("FittingParam.p0a"),p0b[0],c.Config.get("FittingParam.p0c")])
			return popt, pcov

		def calculateVar(pcov):
			return np.diag(pcov)

		dataFiltered = self.filterData()
		histogram, _ = np.histogram(dataFiltered, bins=self.binEdges)
		binCenters = (self.binEdges[:-1] + self.binEdges[1:]) / 2

		# Check if user specified specific b parameters. If they did, check if the parameters are for this dataset
		if type(c.Config.get("FittingParam.p0b")) == dict and (self.path[1] + "/" + self.path[2]) in c.Config.get("FittingParam.p0b"):
			print("Placeholder")

		# If user has not specified specific b parameters, check if user wants automatic modal detection.
		else:
			if c.Config.get("FittingParam.ModeDetection") == True:
				# The KDE is used for modal detection. We find peaks based on the peak parameters (minimum height, prominence, and distance) specified by user.
				
				# The minimum distance given by the user is the distance between two peaks in RMS value. 
				# self.yKDE is a 1D array with 1000 entries but spans over the self.maxRMS self.minRMS distance.
				# So we need to convert the RMS distance the user has given into the distance in the 1D self.yKDE array.
				distance = c.Config.get("FittingParam.ModeDetectionDistance") / (self.maxRMS - self.minRMS) * len(self.yKDE)
				foundPeaks, _ = find_peaks(self.yKDE, height = c.Config.get("FittingParam.ModeDetectionHeight"), 
					prominence = c.Config.get("FittingParam.ModeDetectionProminence"), distance = distance)
				print(foundPeaks)
				peaks = self.xKDE[foundPeaks]
				print(peaks)
								
				# If more than 2 peaks are found, pick the two largest peaks and perform bimodal fitting (currently no fitting for trimodal)
				if len(peaks) > 2:
					peakHeight = [yKDE[peak] for peak in peaks]
					p0b = peaks[peakHeight.argsort()[::-1]]
					p0b = p0b[:2]
					try:
						self.pOpt, pcov = curve_fit(fit.bimodal,binCenters,histogram, p0=[c.Config.get("FittingParam.p0a"),p0b[0],c.Config.get("FittingParam.p0c"),
							c.Config.get("FittingParam.p0a"),p0b[1],c.Config.get("FittingParam.p0c")])
						self.pVar = calculateVar(pcov)
						self.mode = "bimodal"
					except OptimizeWarning:
						self.pOpt, pcov = defaultUnimodalFitting()
						self.pVar = calculateVar(pcov)
						self.mode = "unimodal"

				# Two peaks found, perform bimodal fitting
				elif len(peaks) == 2:
					p0b = peaks
					try:
						self.pOpt, pcov = curve_fit(fit.bimodal,binCenters,histogram, p0=[c.Config.get("FittingParam.p0a"),p0b[0],c.Config.get("FittingParam.p0c"),
							c.Config.get("FittingParam.p0a"),p0b[1],c.Config.get("FittingParam.p0c")])
						self.pVar = calculateVar(pcov)
						self.mode = "bimodal"
					except OptimizeWarning:
						self.pOpt, pcov = defaultUnimodalFitting()
						self.pVar = calculateVar(pcov)
						self.mode = "unimodal"

				# One peak found, unimodal fitting
				elif len(peaks) < 2:
					p0b = peaks
					try:
						self.pOpt, pcov = curve_fit(fit.unimodal,binCenters,histogram, p0=[c.Config.get("FittingParam.p0a"),p0b[0],c.Config.get("FittingParam.p0c")])
						self.pVar = calculateVar(pcov)
						self.mode = "unimodal"
					except OptimizeWarning:
						self.pOpt, pcov = defaultUnimodalFitting()
						self.pVar = calculateVar(pcov)
						self.mode = "unimodal"


			# If user doesn't want automatic modal detection, find the most populated bin and set the center of that bin as our b parameter
			# and perform unimodal fitting
			else:
				self.pOpt, pcov = defaultUnimodalFitting()
				self.pVar = calculateVar(pcov)
				self.mode = "unimodal"