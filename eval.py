from src.el.utils.eval import eval
from src.el.ELMain import EL
import os
import sys
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
module = EL("test", sys.argv[1])
test_data_dir = "corpus/golden/"
eval(module, test_data_dir)