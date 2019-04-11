from src.el.ELMain import EL
from src.utils import jsonload
import json
import os
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = "1"
module = EL("train", sys.argv[1])
train_data_dir = ["corpus/crowdsourcing_formatted/", "corpus/mta2_formatted/"]

train_set = []
dev_set = []
c = 0
for d in train_data_dir:
	for item in os.listdir(d):
		with open(d+item, encoding="UTF8") as f:
			if c % 10 != 0:
				train_set.append(json.load(f))
			else:
				dev_set.append(json.load(f))
				# break # TEMP
		c += 1

module.train(train_set, dev_set)