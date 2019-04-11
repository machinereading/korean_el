from .CandidateDict import CandidateDict
from ...utils import TimeUtil

with TimeUtil.TimeChecker("Entity dict load"):
	with open("data/el/wiki_entity_dict.json", encoding="UTF8") as f:
		candidate_dict = CandidateDict.from_file(f)
	with open("data/el/embeddings/dict.entity", encoding="UTF8") as f:
		candidate_dict = CandidateDict.load_entity_from_file(f, candidate_dict)
