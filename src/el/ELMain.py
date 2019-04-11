from .utils import data as data
from .utils.args import EL_Args
from .utils.postprocess import merge_item, postprocess
from .mulrel_nel.ed_ranker import EDRanker
from .mulrel_nel import dataset as D
from .mulrel_nel import utils as U
from .. import GlobalValues as gl
from ..utils import TimeUtil
from ..utils import *

gl.entity_voca, gl.entity_embeddings = U.load_voca_embs('data/el/embeddings/dict.entity', 'data/el/embeddings/entity_embeddings.npy')
gl.word_voca, gl.word_embeddings = U.load_voca_embs('data/el/embeddings/dict.word', 'data/el/embeddings/word_embeddings.npy')
class EL():
	def __init__(self, mode, model_name):
		with TimeUtil.TimeChecker("EL_init"):
			self.arg = EL_Args()
			self.model_name = model_name
			self.arg.mode = mode
			self.arg.model_path = "data/el/%s" % model_name
			self.model_name = model_name
			self.debug = False
			arg = self.arg
			voca_emb_dir = 'data/el/embeddings/'

			
			snd_word_voca, snd_word_embeddings = U.load_voca_embs(voca_emb_dir + '/glove/dict.word',
															  voca_emb_dir + '/glove/word_embeddings.npy')
			
			config={
				'hid_dims': arg.hid_dims,
				'emb_dims': gl.entity_embeddings.shape[1],
				'freeze_embs': True,
				'tok_top_n': arg.tok_top_n,
				'margin': arg.margin,
				'word_voca': gl.word_voca,
				'entity_voca': gl.entity_voca,
				'word_embeddings': gl.word_embeddings,
				'entity_embeddings': gl.entity_embeddings,
				'snd_word_voca': snd_word_voca,
				'snd_word_embeddings': snd_word_embeddings,
				'dr': arg.dropout_rate,
				'args': arg
			}
			config['df'] = arg.df
			config['n_loops'] = arg.n_loops
			config['n_rels'] = arg.n_rels
			config['mulrel_type'] = arg.mulrel_type
		
			self.ranker = EDRanker(config=config)
		

	def train(self, train_items, dev_items, load_from_debug=False):
		"""
		Train EL Module
		Input:
			train_items: List of dictionary
			dev_items: List of dictionary
		Output: None
		"""
		print(len(train_items), len(dev_items))
		if load_from_debug:
			tj = jsonload("debug/train.json")
			tc = readfile("debug/train.conll")
			tt = readfile("debug/train.tsv")
			dj = jsonload("debug/dev.json")
			dc = readfile("debug/dev.conll")
			dt = readfile("debug/dev.tsv")
		else:
			tj, tc, tt = data.prepare(*train_items, form="CROWDSOURCING", filter_rate=self.arg.train_filter_rate)
			dj, dc, dt = data.prepare(*dev_items, form="CROWDSOURCING")
			if self.debug:
				jsondump(tj, "debug/train.json")
				writefile(tc, "debug/train.conll")
				writefile(tt, "debug/train.tsv")
				jsondump(dj, "debug/dev.json")
				writefile(dc, "debug/dev.conll")
				writefile(dt, "debug/dev.tsv")
		train_data = D.generate_dataset_from_str(tc, tt)
		dev_data = D.generate_dataset_from_str(dc, dt)
		self.ranker.train(train_data, [("dev", dev_data)], config = {'lr': self.arg.learning_rate, 'n_epochs': self.arg.n_epochs})


	def predict(self, sentences, form):
		if type(sentences) in [str, dict]:
			sentences = [sentences]
		batches = split_to_batch(sentences, 100)
		it = 0
		for batch in batches:
			j, conll_str, tsv_str = data.prepare(*batch, form=form)
			if self.debug:
				jsondump(j, "debug/prepare.json")
				writefile(conll_str, "debug/debug.conll")
				writefile(tsv_str, "debug/debug.tsv")
				# with open("debug/debug.json", "w", encoding="UTF8") as f:
				# 	json.dump(j, f, ensure_ascii=False, indent="\t")
				# with open("debug/debug.conll", "w", encoding="UTF8") as f:
				# 	for item in conll_str:
				# 		f.write(item+"\n")
				# with open("debug/debug.tsv", "w", encoding="UTF8") as f:
				# 	for item in tsv_str:
				# 		f.write(item+"\n")
			dataset = D.generate_dataset_from_str(conll_str, tsv_str)
			data_items = self.ranker.get_data_items(dataset, predict=True)

			self.ranker.model._coh_ctx_vecs = []
			predictions = self.ranker.predict(data_items)
			if self.debug:
				jsondump(predictions, "debug/debug_prediction_raw.json")
				jsondump(dataset, "debug/dataset.json")
				jsondump(data_items, "debug/data.json")
			e = D.make_result_dict(dataset, predictions)
			# if self.debug:
			# 	jsondump(e, "debug/debug_prediction.json")
			yield merge_item(j, e)
			it += 1
			# printfunc("EL Progress: %d/%d" % (it, len(batches)))

	def __call__(self, sentences):
		result = []
		for batch in self.predict(sentences, "ETRI"):
			result += [postprocess(j) for j in batch]
		return result