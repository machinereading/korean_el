from src.el.ELMain import EL
from src.utils import TimeUtil
from src.el.utils.eval import eval
import os
import random
import json
import sys
train_data_dir = ["corpus/crowdsourcing_processed/", "corpus/mta2_postprocessed/"]
# train_data_dir = ["corpus/mta2_postprocessed/"]
test_data_dir = "corpus/el_golden_postprocessed_marked/"


# os.environ["CUDA_VISIBLE_DEVICES"]="1"

model_name = sys.argv[1]
module = EL("test", model_name)
train_set = []
dev_set = []
test_set = []
c = 1

# for d in train_data_dir:
# 	for item in os.listdir(d):
# 		with open(d+item, encoding="UTF8") as f:
# 			if c % 10 != 0:
# 				train_set.append(json.load(f))
# 			else:
# 				dev_set.append(json.load(f))
# 				# break # TEMP
# 		c += 1

# for item in os.listdir(test_data_dir):
# 	with open(test_data_dir+item, encoding="UTF8") as f:
# 		j = json.load(f)
# 		test_set.append(j)
# try:
# 	module.train(train_set, dev_set)
# except:
# 	import traceback
# 	traceback.print_exc()
eval(module, test_data_dir)
TimeUtil.time_analysis()