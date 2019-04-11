import os
import json
from ...utils import jsondump
def eval(module, corpus_dir):
	eval_target = []
	for item in os.listdir(corpus_dir):
		with open(corpus_dir+item, encoding="UTF8") as f:
			j = json.load(f)
			j["fileName"] = item.split(".")[0]
			eval_target.append(j)

	prediction = []
	for item in module.predict(eval_target, form="CROWDSOURCING"):
		prediction += item
	print(len(prediction), len(eval_target))
	jsondump(prediction, "debug/debug_prediction.json")
	correct_count = 0
	dark_entity_correct_count = 0
	dark_entity_count = 0
	dark_entity_wrong_list = {}
	error_count = 0
	r_target = 0
	p_target = 0
	wrong_count = [0, 0, 0, 0]
	wrong_list = [[],[],[],[]]
	for doc in prediction:
		fname = doc["fileName"]
		for entity in doc["entities"]:
			if "entity" not in entity:
				error_count += 1
				continue
			predict_entity = entity["entity"]
			answer = entity["answer"]

			if answer == "DARK_ENTITY":
				dark_entity_count += 1

			entity["fileName"] = fname
			if predict_entity not in ["NOT_AN_ENTITY", "NOT_IN_CANDIDATE", "EMPTY_CANDIDATES", "DARK_ENTITY"]:
				p_target += 1
			if answer not in ["NOT_AN_ENTITY", "NOT_IN_CANDIDATE", "EMPTY_CANDIDATES", "DARK_ENTITY"]:
				r_target += 1

			if predict_entity == answer:
				correct_count += 1
			elif predict_entity == "NOT_IN_CANDIDATE" and answer == "DARK_ENTITY":
				correct_count += 1
				dark_entity_correct_count += 1
			else:
				if answer not in ["NOT_AN_ENTITY", "NOT_IN_CANDIDATE", "EMPTY_CANDIDATES", "DARK_ENTITY"]:
					if answer in [x[0] for x in entity["candidates"]]:
						wrong_count[0] += 1
						del entity["candidates"]
						wrong_list[0].append(entity)
					else:
						wrong_count[1] += 1
						del entity["candidates"]
						wrong_list[1].append(entity)
				elif answer == "DARK_ENTITY" and predict_entity not in ["NOT_AN_ENTITY", "NOT_IN_CANDIDATE"]:
					wrong_count[2] += 1
					del entity["candidates"]
					wrong_list[2].append(entity)
				elif answer == "NOT_AN_ENTITY" and predict_entity != "NOT_IN_CANDIDATE":
					wrong_count[3] += 1
					del entity["candidates"]
					wrong_list[3].append(entity)

	entity_count = sum(map(lambda x: len(x["entities"]), eval_target))
	result = {
		"Total": entity_count,
		"Correct": correct_count,
		"Error": error_count,
		"Wrong": {"Type %d" % (i+1): len(wrong_list[i]) for i in range(len(wrong_list))},
		"Wrong Result": {"Type %d" % (i+1): wrong_list[i] for i in range(len(wrong_list))},
		"Dark entity": "%d / %d" % (dark_entity_correct_count, dark_entity_count),
	}
	with open("debug/%s_eval_result.json" % module.model_name, "w", encoding="UTF8") as f:
		json.dump(result, f, ensure_ascii=False, indent="\t")
	p = correct_count / p_target
	r = correct_count / r_target
	f = 2 * p * r / (p + r)
	print("P: %.2f, R: %.2f, F1: %.2f" % (p,r,f))
	print("Acc: %.2f%%" % (correct_count / entity_count * 100))
	for i in range(len(wrong_list)):
		print("Type %d Error: %d" % (i+1, len(wrong_list[i])))
	print("Dark entity detection rate: %.2f" % (dark_entity_correct_count / dark_entity_count * 100))
