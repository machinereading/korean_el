# import endpoint.
# stores only global values
# set attributes by calling setattr in main module
from .utils import readfile
import logging
from datetime import datetime

# logging.basicConfig(filename= "elrun_%s.log" % str(datetime.now())[:-7].replace(" ", "_"), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S')
# logging.info("[START]")

boolmap = {"True": True, "False": False}
corpus_home = "corpus/"
entity_id_map = {}
for i, k in enumerate(readfile("data/el/embeddings/dict.entity")):
	entity_id_map[k.split("\t")[0].replace("ko.dbpedia.org/resource/", "")] = i
# entity_id_map = {k.split("\t")[0].replace("ko.dbpedia.org/resource/", ""): i for i, k in enumerate([x for x in readfile("data/el/embeddings/dict.entity")])}
id_entity_map = {v: k for k, v in entity_id_map.items()}