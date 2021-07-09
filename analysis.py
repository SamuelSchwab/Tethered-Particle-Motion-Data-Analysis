import re
import sys
import numpy as np
import config as c
import plots
import os.path

from pandas import read_csv
from os import getcwd
from collections import defaultdict
from dataclass import Data
from dataclasses import asdict
from datetime import date, datetime


# Function to load data from data_good.txt files.
def FileLoader(rootDir, blacklist, blacklistConc):

	# Regex function to find concentrations from the directory name
	def concentrationRegex(subdir):
		regexConcentration = re.findall(r"(\d+[.,]?\d*)(?:[\s_-]*)(?:nM)", os.path.basename(os.path.normpath(subdir)), flags = re.I)

		# If nothing was found, check milli Molar
		if not regexConcentration:
			regexConcentration = re.findall(r"(\d+[.,]?\d*)(?:[\s_-]*)(?:mM)", os.path.basename(os.path.normpath(subdir)), flags = re.I)

			# If nothing was found, ask the user to specify concentration
			if not regexConcentration:
				print("Couldn't find matching expression for " + subdir)
				print("Enter the concentration in nM:")
				regexConcentration = []
				input_concentration = input()
				regexConcentration.append(input_concentration)
			else:
				print("Found concentration in " + subdir + ": " + regexConcentration[0] + "mM")
				regexConcentration = regexConcentration * 1000
		else:
			print("Found concentration in " + subdir + ": " + regexConcentration[0] + "nM")
		return float(regexConcentration[0])


	skipBoolean = False
	concList, dataList, pathList = [], [], []
	rootDirName = os.path.basename(os.path.normpath(rootDir))
	
	# Iterate over all sub-directories; directories; and files of the root-directory, find data_good.txt files and determine concentrations.
	for subdir, dirs, files in os.walk(rootDir):
		filesSet = set(files)
		if "data_good.txt" in filesSet:
			
			# If user specified blacklist, check if current data_good.txt is located in a blacklisted folder
			if blacklist != None:	
				for blacklistPath in blacklist:
					if os.path.commonpath([subdir, blacklistPath]) == os.path.normpath(blacklistPath):
						skipBoolean = True
						print("  " + subdir + " ignored because it is in blacklistPath")
				if skipBoolean == True:
					skipBoolean = False
					continue

			concentration = concentrationRegex(subdir)

			# If user specified blacklisted concentrations, check if current concentration is blacklisted
			if blacklistConc != None and (concentration in set(blacklistConc)):
				print("  " + subdir + " ignored because" + str(concentration) + "nM is in blacklistConc")
				continue

			dataLocation = subdir + "/data_good.txt"
			fileName = os.path.basename(os.path.normpath(subdir))
			dirName = os.path.dirname(os.path.relpath(subdir, rootDir))
			df = read_csv(dataLocation, delimiter=r"\s+\s+", index_col=None, header = None, engine="python")

			concList.append(concentration)
			dataList.append(df[0].to_numpy())
			pathList.append([rootDirName,dirName,fileName])

	data = np.asarray(dataList, dtype = object)
	conc = np.asarray(concList)
	path = np.asarray(pathList)

	return data, conc, path


def SaveConfigs(dataList, path):

	# Add the config to the export config
	c.ExportConfig.update({"Config": c.Config.config})

	# Add the dataClasses as dictionaries to the export config
	dataDict = defaultdict(dict)
	for dataClass in dataList:
		name = dataClass.path[1] + "/" + dataClass.path[2]
		dataDict["Data"][name] = asdict(dataClass)
	c.ExportConfig.update(dataDict)

	# Save the export config
	c.ExportConfig.save(path)
	c.Config.save(path)



def DataAnalysis(config, progress):
	# Initialize classes for our config and export config
	c.Config(config)
	c.ExportConfig()

	# Import TPM data and construct data class instances
	RawDataList, ConcentrationList, PathList = FileLoader(c.Config.get("FileParam.RootDir"), 
		c.Config.get("FileParam.Blacklist"), c.Config.get("FileParam.BlacklistConc"))
	DataList = []

	percentage_step = 100/len(RawDataList)

	for i in range(0,len(RawDataList)):
		DataList.append(Data(PathList[i], RawDataList[i], ConcentrationList[i], c.Config.get("DataParam.MinRMS"), c.Config.get("DataParam.MaxRMS")))
		DataList[i].generateKDE(c.Config.get("DataParam.KDE"))
		DataList[i].generateBinEdges()
		DataList[i].fitData()
		progress.emit(int(percentage_step * (i+1)))

	#Find and create a new output folder
	cwd = getcwd()
	i = 0
	while True:
		outputDir = cwd + "/output/" + DataList[0].path[0] + "/" + datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
		if os.path.exists(outputDir):
			continue
		else:
			os.makedirs(outputDir)
			break

	SaveConfigs(DataList, outputDir)