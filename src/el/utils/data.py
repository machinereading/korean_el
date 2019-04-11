import json
import os
import pickle
from konlpy.tag import Okt
import socket
from functools import reduce
from ...utils import TimeUtil, progress, printfunc
from . import candidate_dict
import re
import random
import string
import traceback

RE_EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
okt = Okt()
dbpedia_prefix = "ko.dbpedia.org/resource/"
lock = False
error_file = open("error.txt", "w", encoding="UTF8")
with open("data/el/wiki_entity_calc.pickle", "rb") as f:
	ent_dict = pickle.load(f)
with open("data/el/wiki_entity_cooccur.pickle", "rb") as f:
	ent_form = pickle.load(f)
ent_form = ent_form.keys()
with open("data/el/redirects.pickle", "rb") as f:
	redirects = pickle.load(f)

@TimeUtil.measure_time
def candidates(word):
	candidates = candidate_dict[word]
	return candidates

def candidates_old(word):
	candidates = ent_dict[word] if word in ent_dict else {}
	cand_list = []
	for cand_name, cand_score in sorted(candidates.items(), key=lambda x: -x[1][0]):
		cand_name = redirects[cand_name] if cand_name in redirects else cand_name
		if (cand_name in cand_list and cand_list[cand_name] < cand_score) or cand_name not in cand_list:
			score, id = cand_score
			cand_list.append((cand_name, id, score))
	return cand_list

@TimeUtil.measure_time
def getETRI(text):
	host = '143.248.135.146'
	port = 33333
	
	ADDR = (host, port)
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try: 
		clientSocket.connect(ADDR)
	except Exception as e:
		traceback.print_exc()
		return None
	try:
		clientSocket.sendall(str.encode(text))
		buffer = bytearray()
		while True:
			data = clientSocket.recv(1024)
			if not data:
				break
			buffer.extend(data)
		result = json.loads(buffer.decode(encoding='utf-8'))

		return result
	except Exception as e:
		traceback.print_exc()
		return None


def find_ne_pos(j):
	def find_in_wsd(wsd, ind):
		for item in wsd:
			if item["id"] == ind:
				return item
		print(wsd, ind)
		raise IndexError(ind)
	if j is None:
		return None
	original_text = reduce(lambda x, y: x+y, list(map(lambda z: z["text"], j["sentence"])))
	# original_text = j["sentence"]
	# print(original_text)
	# print(j)
	j["NE"] = []
	try:
		for v in j["sentence"]:
			sentence = v["text"]
			for ne in v["NE"]:
				morph_start = find_in_wsd(v["morp"],ne["begin"])
				# morph_end = find_in_wsd(v["WSD"],ne["end"])
				byte_start = morph_start["position"]
				# print(ne["text"], byte_start)
				# byte_end = morph_end["position"]+sum(list(map(lambda char: len(char.encode()), morph_end["text"])))
				byteind = 0
				charind = 0
				for char in original_text:
					if byteind == byte_start:
						ne["char_start"] = charind
						ne["char_end"] = charind + len(ne["text"])
						j["NE"].append(ne)
						break
					byteind += len(char.encode())
					charind += 1
				else:
					raise Exception("No char pos found: %s" % ne["text"])
			j["original_text"] = original_text
	except Exception as e:
		print(e)
		return None
	# print(len(j["NE"]))
	return j

def is_not_korean(char):
	return not (0xAC00 <= ord(char) <= 0xD7A3)

def mark_ne(text):
	return find_ne_pos(getETRI(text))

def make_json(ne_marked_dict, predict=False):
	cs_form = {}
	cs_form["text"] = ne_marked_dict["original_text"] if "original_text" in ne_marked_dict else ne_marked_dict["text"]
	cs_form["entities"] = []
	cs_form["fileName"] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7)) if "fileName" not in ne_marked_dict or ne_marked_dict["fileName"] == "" else ne_marked_dict["fileName"]
	entities = ne_marked_dict["NE"] if "NE" in ne_marked_dict else ne_marked_dict["entities"]
	for item in entities:
		skip_flag = False
		if "type" in item:
			for prefix in ["QT", "DT"]: # HARD-CODED: ONLY WORKS FOR ETRI TYPES
				if item["type"].startswith(prefix): skip_flag = True
			if item["type"] in ["CV_RELATION", "TM_DIRECTION"] or skip_flag: continue
		surface = item["text"] if "text" in item else item["surface"]
		if "keyword" in item or "entity" in item:
			keyword = "NOT_IN_CANDIDATE" if predict else (item["keyword"] if "keyword" in item else item["entity"])
		else:
			keyword = "NOT_IN_CANDIDATE"
		# if keyword == "NOT_AN_ENTITY":
		# 	keyword = "NOT_IN_CANDIDATE"
		if "dark_entity" in item:
			keyword = "DARK_ENTITY"
		start = item["char_start"] if "char_start" in item else item["start"]
		end = item["char_end"] if "char_end" in item else item["end"]
		if all(list(map(is_not_korean, surface))): continue
		
		cs_form["entities"].append({
			"surface": surface,
			"candidates": candidates_old(surface),
			"answer": keyword,
			"start": start,
			"end": end,
			"ne_type": item["type"] if "type" in item else ""
			})
	return cs_form


def add_candidates(j):
	for entity in j["entities"]:
		if "candidates" in entity: continue
		entity["candidates"] = candidates(entity["surface"])

def overlap(ent1, ent2):
	s1 = ent1["start"]
	e1 = ent1["end"]
	s2 = ent2["start"]
	e2 = ent2["end"]
	return s1 <= s2 < e1 or s1 < e2 <= e1

def morph_split(morph_pos, links):
	result = []
	morph, pos = morph_pos
	for link in links:
		ne, en, sp, ep, _ = link
		if sp <= pos < ep or pos <= sp < pos+len(morph):
			if pos < sp:
				m1 = morph[:sp-pos]
				m2 = morph[sp-pos:min(len(morph), ep-pos)] # 반[중국]적 과 같은 경우
				m3 = morph[ep-pos:] if ep < pos+len(morph) else None
				result.append([m1, None])
				result.append([m2, link])
				if m3 is not None:
					result += morph_split((m3, pos+len(m1)+len(m2)), links)
				break
			elif pos + len(morph) > ep:
				# print(morph, "/", en)
				m1 = morph[:ep-pos]
				m2 = morph[ep-pos:]
				result.append([m1, link])
				result += morph_split((m2, pos+len(m1)), links)
				break
			else:
				result.append([morph, link])
				break
	else:
		result.append([morph, None])
	return result

def get_context_words(text, pos, direction, maximum_context=30):
	result = []
	ind = pos
	buf = ""
	text = text.replace("\n", " ")
	while len(result) < maximum_context and ind > 0 and ind < len(text)-1:
		ind += direction
		if text[ind] == " ":
			if len(buf) > 0:
				buf = buf[::direction]
				result.append(buf[:])
				buf = ""
			continue
		buf += text[ind]
	if len(buf) > 0:
		result.append(buf[::direction])
	if len(result) == 0:
		return "EMPTYCTXT"
	result = " ".join(result[::direction])
	# print(result)
	return result

def generate_input(sentence, predict=False, form="PLAIN_SENTENCE"):
	global error_file
	if form not in ["PLAIN_SENTENCE", "ETRI", "CROWDSOURCING"]: raise Exception("Form not match")
	# print(sentence)
	if form == "PLAIN_SENTENCE":
		sentence = make_json(mark_ne(sentence), predict=predict)
	elif form == "ETRI":
		sentence = make_json(find_ne_pos(sentence), predict=predict)
	else:
		sentence = make_json(sentence, predict=predict)
	# if form == "CROWDSOURCING":
	# 	add_candidates(sentence)
	# print(sentence)
	# at this point, sentence should be in Crowdsourcing form
	result = []
	links = []
	print_flag = False
	# sentence["entities"] = list(filter(lambda entity: (redirects[entity["keyword"]] if entity["keyword"] in redirects else entity["keyword"]) in ent_form, sentence["entities"]))
	for entity in sentence["entities"]:
		
		redirected_entity = redirects[entity["answer"]] if entity["answer"] in redirects else entity["answer"]
		
		# if redirected_entity not in ent_form:
		# 	redirected_entity = "NOT_IN_ENTITY_LIST"
		# if "dark_entity" in entity:
		# 	print(entity["surface"])
		# 	redirected_entity = "DARK_ENTITY"
		entity["answer"] = redirected_entity
		# if redirected_entity not in ent_form and redirected_entity not in ["NOT_IN_CANDIDATE", "NOT_AN_ENTITY", "EMPTY_CANDIDATES"]:
		# 	continue
		links.append((entity["surface"], redirected_entity, entity["start"], entity["end"], tuple(entity["candidates"])))
		
	filter_entity = set([])
	for i1 in links:
		if i1 in filter_entity: continue
		for i2 in links:
			if i1 == i2: continue
			if i1[2] <= i2[2] < i1[3] or i1[2] < i2[3] <= i1[3]:
				# overlaps
				shorter = i1 if i1[3] - i1[2] <= i2[3] - i2[2] else i2
				filter_entity.add(shorter)
	links = list(filter(lambda x: x not in filter_entity, links))
	links = sorted(links, key=lambda x: x[2])
	sent = sentence["text"]
	for char in "   ":
		sent.replace(char, " ")
	
	sent = RE_EMOJI.sub(r'', sent)
	morphs = okt.morphs(sent)
	inds = []
	last_char_ind = 0
	conlls = []
	tsvs = []
	fname = sentence["fileName"]
	conlls.append("-DOCSTART- (%s" % fname)
	for item in morphs:
		ind = sent.find(item, last_char_ind) 
		inds.append(ind)
		last_char_ind = ind+len(item)
	assert(len(morphs) == len(inds))
	last_link = None
	added = []
	for morph, pos in zip(morphs, inds):
		for m, link in morph_split((morph, pos), links):
			if link is None: # if train mode, skip if candidate set is empty
				conlls.append(m)
				last_link = None
				continue
			last_label = conlls[-1][1] if len(conlls) > 0 and type(conlls[-1]) is not str else "O"
			bi = "I" if last_label != "O" and last_link is not None and link == last_link else "B"
			ne, en, sp, ep, cand = link
			last_link = link
			if m not in ne:
				error_file.write("%s, %s, %s" % (sentence, m, ne)+"\n")
			assert m in ne, "%s, %s, %s" % (sentence, m, ne)
			conlls.append([m, bi, ne, en, "%s%s" % (dbpedia_prefix, en), "000", "000"])
			if bi == "B":
				added.append(link)
	# not_added = list(filter(lambda x: x not in added, links))
	# if len(not_added) > 0:
	# 	print(not_added)

	for ne, en, sp, ep, cand in added:
		f = [fname, fname, ne, get_context_words(sent, sp, -1), get_context_words(sent, ep-1, 1), "CANDIDATES"]
		cand_list = []
		gold_ind = -1
		ind = 0
		for cand_name, cand_id, cand_score in sorted(cand, key=lambda x: -x[-1]):
			cand_list.append((redirects[cand_name] if cand_name in redirects else cand_name, cand_id, cand_score))
		if en in ["NOT_IN_CANDIDATE", "NOT_AN_ENTITY"]: en = "#UNK#"
		for cand_name, cand_id, cand_score in cand_list:
			# print(cand_score)
			f.append(",".join([str(cand_id), str(cand_score), cand_name])) # order: ID SCORE ENTITY
			if cand_name == en:
				gold_ind = ind
				gold_sent = f[-1]
			ind += 1
		if len(cand_list) == 0:
			f.append("EMPTYCAND")
		f.append("GT:")
		f.append("%d,%s" %(gold_ind, gold_sent) if gold_ind != -1 else "-1")
		tsvs.append("\t".join(f))


	conlls = list(map(lambda x: x if type(x) is str else "\t".join(x), conlls))
	if conlls[-1] in ["", "\n"]:
		conlls = conlls[:-1]
	return sentence, conlls, tsvs



def prepare_sentence(sentence, form, predict):
	try:
		return generate_input(sentence, predict, form)
	# ne_marked = sentence if ne_marked else mark_ne(sentence)
	# j = make_json(ne_marked, predict)
	# try:
	# 	conll = change_to_conll(j)
	# 	tsv = change_to_tsv(j)
	# 	return j, conll, tsv
	except:
		import traceback
		traceback.print_exc()



@TimeUtil.measure_time
def prepare(*sentences, form, predict=False, filter_rate=0.0):
	conlls = []
	tsvs = []
	cw_form = []
	# prog = 0
	# def job(sents, ne_marked, predict, lock, conlls, tsvs, cw_form):
	# 	# print(len(sents))
	# 	for sentence in sents:
	# 		try:
	# 			j, c, t = prepare_sentence(sentence, ne_marked, predict)
	# 			# conll = change_to_conll(sentence)
	# 			# tsv = change_to_tsv(sentence)
	# 			with lock:
	# 				# print(sentence)
	# 				cw_form.append(j)
	# 				conlls += c
	# 				conlls += [""]
	# 				tsvs += t
	# 				print(len(cw_form))
	# 		except Exception as e:
	# 			import traceback
	# 			traceback.print_exc()
	# l = len(sentences)//worker
	# partition = [sentences[(k*l):((k+1)*l)] for k in range(worker)]
	# threads = []
	# for p in partition:
	# 	threads.append(threading.Thread(target=job, args=[p, ne_marked, predict, lock, conlls, tsvs, cw_form]))
	# for t in threads:
	# 	t.start()
	# for t in threads:
	# 	t.join()
	for sentence in sentences:
		s = random.random()
		
		if filter_rate > s: continue
		
		try:
			j, c, t = prepare_sentence(sentence, form, predict)
			# conll = change_to_conll(sentence)
			# tsv = change_to_tsv(sentence)
			cw_form.append(j)
			conlls += c
			conlls += [""]
			tsvs += t
		except Exception as e:
			pass
	return cw_form, conlls, tsvs

