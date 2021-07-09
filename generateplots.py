import config as c
import plots
from matplotlib.pyplot import savefig
from matplotlib.pyplot import close as closeFigure
from os.path import exists
from os import makedirs

def generateplots(dataList, path):

	plots.setFont()

	if c.PlotConfig.get("Histogram2D.Generate") == True:
		Histogram2D = plots.Histogram2D(dataList)
		fig = plots.Histogram2DPlot(Histogram2D)
		outputType = c.PlotConfig.get("Histogram2D.OutputType")
		if outputType == "svg" or outputType == "pdf":
			savefig(path + "/histogram2D." + outputType)
		else:
			savefig(path + "/histogram2D." + outputType, dpi=dpi)
		closeFigure("all")

	if c.PlotConfig.get("Violinplot.Generate") == True:
		fig = plots.ViolinPlot(dataList)
		outputType = c.PlotConfig.get("Violinplot.OutputType")
		if outputType == "svg" or outputType == "pdf":
			savefig(path + "/violinplot." + outputType)
		else:
			savefig(path + "/violinplot." + outputType, dpi=dpi)
		closeFigure("all")

	if c.PlotConfig.get("Simpleplot.Generate") == True:
		fig = plots.SimplePlot(dataList)
		outputType = c.PlotConfig.get("Simpleplot.OutputType")
		if outputType == "svg" or outputType == "pdf":
			savefig(path + "/simpleplot." + outputType)
		else:
			savefig(path + "/simpleplot." + outputType, dpi=dpi)
		closeFigure("all")

	if c.PlotConfig.get("Histogram.Generate"):
		for d in dataList:
			fig = plots.HistogramPlot(d)
			outputType = c.PlotConfig.get("Histogram.OutputType")
			if not exists(path + "/" + d.path[1]):
				makedirs(path + "/" + d.path[1])
			if outputType == "svg" or outputType == "pdf":
				savefig(path + "/" + d.path[1] + "/" + d.path[2] + "." + outputType)
			else:
				savefig(path + "/" + d.path[1] + "/" + d.path[2] + "." + outputType, dpi=dpi)
			closeFigure("all")

	if c.PlotConfig.get("ECDF.Generate"):
		for d in dataList:
			fig = plots.ECDF(d)
			outputType = c.PlotConfig.get("ECDF.OutputType")
			if not exists(path + "/" + d.path[1]):
				makedirs(path + "/" + d.path[1])
			if outputType == "svg" or outputType == "pdf":
				savefig(path + "/" + d.path[1] + "/" + d.path[2] + "-ECDF" + "." + outputType)
			else:
				savefig(path + "/" + d.path[1] + "/" + d.path[2] + "-ECDF" + "." + outputType, dpi=dpi)
			closeFigure("all")