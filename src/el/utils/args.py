
import argparse
class EL_Args():
	def __init__(self):
		self.mode = "train"
		self.model_path = ""
		self.n_cands_before_rank = 30
		self.prerank_ctx_window = 50
		self.keep_p_e_m = 4
		self.keep_ctx_ent = 4
		self.ctx_window = 100
		self.tok_top_n = 25
		self.mulrel_type = "ment-norm"
		self.n_rels = 5
		self.hid_dims = 100
		self.snd_local_ctx_window = 6
		self.dropout_rate = 0.3
		self.n_epochs = 100
		self.dev_f1_change_lr = 0.68
		self.n_not_inc = 10
		self.eval_after_n_epochs = 5
		self.learning_rate = 1e-4
		self.margin = 0.01
		self.df = 0.5
		self.n_loops = 10
		self.train_filter_rate = 0.9


def get_args():
	return EL_Args()
def get_args_old():
	parser = argparse.ArgumentParser()

	# general args
	parser.add_argument("--mode", type=str,
	                    help="train or eval",
	                    default='train')
	parser.add_argument("--model_path", type=str,
	                    help="model path to save/load",
	                    default='')

	# args for preranking (i.e. 2-step candidate selection)
	parser.add_argument("--n_cands_before_rank", type=int,
	                    help="number of candidates",
	                    default=30)
	parser.add_argument("--prerank_ctx_window", type=int,
	                    help="size of context window for the preranking model",
	                    default=50)
	parser.add_argument("--keep_p_e_m", type=int,
	                    help="number of top candidates to keep w.r.t p(e|m)",
	                    default=4)
	parser.add_argument("--keep_ctx_ent", type=int,
	                    help="number of top candidates to keep w.r.t using context",
	                    default=4)

	# args for local model
	parser.add_argument("--ctx_window", type=int,
	                    help="size of context window for the local model",
	                    default=100)
	parser.add_argument("--tok_top_n", type=int,
	                    help="number of top contextual words for the local model",
	                    default=25)


	# args for global model
	parser.add_argument("--mulrel_type", type=str,
	                    help="type for multi relation (rel-norm or ment-norm)",
	                    default='ment-norm')
	parser.add_argument("--n_rels", type=int,
	                    help="number of relations",
	                    default=5)
	parser.add_argument("--hid_dims", type=int,
	                    help="number of hidden neurons",
	                    default=100)
	parser.add_argument("--snd_local_ctx_window", type=int,
	                    help="local ctx window size for relation scores",
	                    default=6)
	parser.add_argument("--dropout_rate", type=float,
	                    help="dropout rate for relation scores",
	                    default=0.3)


	# args for training
	parser.add_argument("--n_epochs", type=int,
	                    help="max number of epochs",
	                    default=100)
	parser.add_argument("--dev_f1_change_lr", type=float,
	                    help="dev f1 to change learning rate",
	                    default=0.725)
	parser.add_argument("--n_not_inc", type=int,
	                    help="number of evals after dev f1 not increase",
	                    default=10)
	parser.add_argument("--eval_after_n_epochs", type=int,
	                    help="number of epochs to eval",
	                    default=5)
	parser.add_argument("--learning_rate", type=float,
	                    help="learning rate",
	                    default=1e-4)
	parser.add_argument("--margin", type=float,
	                    help="margin",
	                    default=0.01)

	# args for LBP
	parser.add_argument("--df", type=float,
	                    help="dumpling factor (for LBP)",
	                    default=0.5)
	parser.add_argument("--n_loops", type=int,
	                    help="number of LBP loops",
	                    default=10)

	# args for debugging
	parser.add_argument("--print_rel", action='store_true')
	parser.add_argument("--print_incorrect", action='store_true')


	args = parser.parse_args()
	# args.mode = "test"
	
	return args
