import re
import time
import pickle
from ...utils import TimeUtil

def load_person_names(path):
    data = []
    with open(path, 'r', encoding='utf8') as f:
        for line in f:
            data.append(line.strip().replace(' ', '_'))
    return set(data)


wiki_link_prefix = 'http://en.wikipedia.org/wiki/'
def read_csv_file(path):
    data = {}
    with open(path, 'r', encoding='utf8') as f:
        for line in f:
            if len(line.strip()) == 0: continue
            comps = line.strip().split('\t')
            doc_name = comps[0] + ' ' + comps[1]
            mention = comps[2]
            lctx = comps[3]
            rctx = comps[4]

            if comps[6] != 'EMPTYCAND':
                cands = [c.split(',') for c in comps[6:-2]]
                cands = [(','.join(c[2:]).replace('"', '%22').replace(' ', '_'), float(c[1])) for c in cands]
            else:
                cands = []

            gold = comps[-1].split(',')
            if gold[0] == '-1':
                gold = (','.join(gold[2:]).replace('"', '%22').replace(' ', '_'), 1e-5, -1)
            else:
                gold = (','.join(gold[3:]).replace('"', '%22').replace(' ', '_'), 1e-5, -1)

            if doc_name not in data:
                data[doc_name] = []
            data[doc_name].append({'mention': mention,
                                   'context': (lctx, rctx),
                                   'candidates': cands,
                                   'gold': gold})

    return data

def read_tsv_from_str(texts):
    data = {}
    for line in texts:
        if len(line.strip()) == 0: continue
        comps = line.strip().split('\t')
        doc_name = comps[0] + ' ' + comps[1]
        mention = comps[2]
        lctx = comps[3]
        rctx = comps[4]

        if comps[6] != 'EMPTYCAND':
            cands = [c.split(',') for c in comps[6:-2]]
            # print(cands)
            cands = [(','.join(c[2:]).replace('"', '%22').replace(' ', '_'), float(c[1])) for c in cands]
        else:
            cands = []

        gold = comps[-1].split(',')
        if gold[0] == '-1':
            gold = (','.join(gold[2:]).replace('"', '%22').replace(' ', '_'), 1e-5, -1)
        else:
            gold = (','.join(gold[3:]).replace('"', '%22').replace(' ', '_'), 1e-5, -1)

        if doc_name not in data:
            data[doc_name] = []
        data[doc_name].append({'mention': mention,
                               'context': (lctx, rctx),
                               'candidates': cands,
                               'gold': gold})
    return data

def read_conll_from_str(data, texts):
    conll = {}
    cur_sent = None
    cur_doc = None

    for line in texts:
        line = line.strip()
        if line.startswith('-DOCSTART-'):
            docname = line.split()[1][1:]
            conll[docname] = {'sentences': [], 'mentions': []}
            cur_doc = conll[docname]
            cur_sent = []

        else:
            if line == '' and cur_sent != []:
                cur_doc['sentences'].append(cur_sent)
                cur_sent = []

            else:
                comps = line.split('\t')
                tok = comps[0]
                if tok == " ": continue
                cur_sent.append(tok)

                if len(comps) >=6 :
                    bi = comps[1]
                    wikilink = comps[4]
                    if bi == 'I':
                        cur_doc['mentions'][-1]['end'] += 1
                    else:
                        new_ment = {'sent_id': len(cur_doc['sentences']),
                                    'start': len(cur_sent) - 1,
                                    'end': len(cur_sent),
                                    'wikilink': wikilink}
                        cur_doc['mentions'].append(new_ment)

    # merge with data
    rmpunc = re.compile('[^a-zA-Z0-9ㄱ-ㅣ가-힣]+')
    removed_mentions = 0
    no_entity_docs = []
    for doc_name, content in data.items():
        conll_doc = conll[doc_name.split()[0]]
        content[0]['conll_doc'] = conll_doc
        cur_conll_m_id = 0
        conll_m_id_buf = 0
        check = 0
        errorous_mentions = []
        for m in content:
            mention = m['mention']
            gold = m['gold']
            # if "candidates" not in m:
            #     print(m)
            while True:
                try:
                    cur_conll_m = conll_doc['mentions'][cur_conll_m_id]
                except IndexError:
                    # print(m["mention"], m["gold"])
                    errorous_mentions.append(m)
                    cur_conll_m_id = conll_m_id_buf
                    break

                cur_conll_mention = ' '.join(conll_doc['sentences'][cur_conll_m['sent_id']][cur_conll_m['start']:cur_conll_m['end']])
                # if rmpunc.sub('', cur_conll_mention.lower()) != rmpunc.sub('', mention.lower()):
                #     print(rmpunc.sub('', cur_conll_mention.lower()), rmpunc.sub('', mention.lower()))
                if rmpunc.sub('', cur_conll_mention.lower()) == rmpunc.sub('', mention.lower()):
                    m['conll_m'] = cur_conll_m
                    conll_m_id_buf = cur_conll_m_id
                    cur_conll_m_id += 1
                    break
                else:
                    cur_conll_m_id += 1
        content = list(filter(lambda x: x not in errorous_mentions, content))
        removed_mentions += len(errorous_mentions)
        data[doc_name] = content
        if len(content) == 0:
            no_entity_docs.append(doc_name)
    # print("%d mentions removed" % removed_mentions)
    # print("%d docs removed" % len(no_entity_docs))
    data = {k: v for k, v in data.items() if k not in no_entity_docs}
    
    return data

# @TimeUtil.measure_time
def generate_dataset_from_str(conll_str, tsv_str):
    dataset = read_tsv_from_str(tsv_str)
    dataset = read_conll_from_str(dataset, conll_str)
    with open("data_conll.json", "w", encoding="UTF8") as f:
        import json
        json.dump(dataset, f, ensure_ascii=False, indent="\t")
    return dataset

def find_coref(ment, mentlist, person_names):
    cur_m = ment['mention'].lower()
    coref = []
    for m in mentlist:
        if len(m['candidates']) == 0 or m['candidates'][0][0] not in person_names:
            continue

        mention = m['mention'].lower()
        start_pos = mention.find(cur_m)
        if start_pos == -1 or mention == cur_m:
            continue

        end_pos = start_pos + len(cur_m) - 1
        if (start_pos == 0 or mention[start_pos-1] == ' ') and \
                (end_pos == len(mention) - 1 or mention[end_pos + 1] == ' '):
            coref.append(m)

    return coref


def with_coref(dataset, person_names):
    for data_name, content in dataset.items():
        for cur_m in content:
            coref = find_coref(cur_m, content, person_names)
            if coref is not None and len(coref) > 0:
                cur_cands = {}
                for m in coref:
                    for c, p in m['candidates']:
                        cur_cands[c] = cur_cands.get(c, 0) + p
                for c in cur_cands.keys():
                    cur_cands[c] /= len(coref)
                cur_m['candidates'] = sorted(list(cur_cands.items()), key=lambda x: x[1])[::-1]


def eval(testset, system_pred):
    gold = []
    pred = []

    for doc_name, content in testset.items():
        gold += [c['gold'][0] for c in content]
        pred += [c['pred'][0] for c in system_pred[doc_name]]

    true_pos = 0
    for g, p, in zip(gold, pred):
        if g == p and p not in ['NIL', "NOT_IN_CANDIDATE"]:
            true_pos += 1

    # precision = true_pos / len([p for p in pred if p not in ['NIL', "NOT_IN_CANDIDATE"]])
    # recall = true_pos / len(gold)
    # print(precision)
    # print(recall)
    # f1 = 2 * precision * recall / (precision + recall) if precision+recall >0 else 0
    return true_pos / len([p for p in pred if p not in ['NIL', "NOT_IN_CANDIDATE"]]) # only accuracy



def make_result_dict(testset, system_pred):
    gold = []
    pred = []
    mention = []
    cand_length = []

    true_pos = 0
    true_pos_2 = 0
    pred_num = 0
    gold_num = 0
    result = []
    result = {}
    for doc_name, pred in system_pred.items():
        # print(doc_name)
        result[doc_name.split()[0]] = []
        mention = [c["mention"] for c in testset[doc_name]]
        gold = [c["gold"][0] for c in testset[doc_name]]
        # print(len(mention), len(gold), len(pred))
        if len(mention) != len(pred):
            print(doc_name.split()[0], len(mention), len(pred))
        # assert len(gold) == len(mention) == len(pred)
        for m, g, p in zip(mention, gold, pred):
            result[doc_name.split()[0]].append((m, g, p["pred"][0]))

    return result



