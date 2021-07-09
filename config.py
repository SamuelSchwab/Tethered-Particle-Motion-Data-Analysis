import yaml
import collections.abc

from functools import reduce
from collections import defaultdict
from yaml.representer import Representer

yaml.add_representer(collections.defaultdict, Representer.represent_dict)

class ExportConfig():

	def __init__(self):
		ExportConfig.config = defaultdict(dict)

	def update(d):
		ExportConfig.config.update(d)

	def save(path):
		savePath = path + "/config_export.yaml"
		with open(savePath, "w") as file:
			yaml.dump(ExportConfig.config, file)



class Config():

	def __init__(self, c):
		if isinstance(c, str):
			with open(c) as file:
				Config.config = yaml.load(file, Loader = yaml.FullLoader)
		if isinstance(c, dict):
			Config.config = c

	def get(keys, default=None):
		return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), Config.config)

	def save(path):
		savePath = path + "/config.yaml"
		with open(savePath, "w") as file:
			yaml.dump(Config.config, file)



class PlotConfig():

	def __init__(self, c):
		if isinstance(c, str):
			with open(c) as file:
				PlotConfig.config = yaml.load(file, Loader = yaml.FullLoader)
		if isinstance(c, dict):
			PlotConfig.config = c

	def get(keys, default=None):
		return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), PlotConfig.config)

	def save(path):
		savePath = path + "/config_plot.yaml"
		with open(savePath, "w") as file:
			yaml.dump(PlotConfig.config, file)