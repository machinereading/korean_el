import json
import functools
import logging
def progress(curprog, total, size=10):
	if curprog < 0 or total < 0 or size < 0:
		return ""
	a = int((curprog / total) * size)
	return "["+("*"*a)+(" "*(size - a)) + "]"

def printfunc(s):
	print("\r"+s, end="", flush=True)

def jsonload(fname):
	with open(fname, encoding="UTF8") as f:
		return json.load(f)

def jsondump(obj, fname, split=0):
	with open(fname, "w", encoding="UTF8") as f:
		json.dump(obj, f, ensure_ascii=False, indent="\t")

def readfile(fname):
	result = []
	with open(fname, encoding="UTF8") as f:
		for line in f.readlines():
			yield line.strip()

def writefile(iterable, fname, processor=lambda x: x):
	with open(fname, "w", encoding="UTF8") as f:
		for item in iterable:
			f.write(processor(item)+"\n")

def split_to_batch(l, batch_size=100):
	return [l[x*batch_size:x*batch_size+batch_size] for x in range(len(l) // batch_size + 1)]
	# result = []
	# temp = []
	# for item in l:
	# 	temp.append(item)
	# 	if len(temp) == batch_size:
	# 		result.append(temp[:])
	# 		temp = []
	# result.append(temp)
	# return result

def split_to_equal_size(l, num):
	k = len(l) // num
	return [l[x*k:(x+1)*k] for x in range(num+1)]

def one_hot(i, total):
	i = int(i)
	result = [0 for _ in range(total)]
	result[i] = 1
	return result

#useful macros
inv_dict = lambda x: {v: k for k, v in x.items()}

