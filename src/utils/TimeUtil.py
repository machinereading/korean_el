import time
import functools
import logging
time_checker = {}
time_millis = lambda: int(round(time.time() * 1000))
class TimeHierarchy():
	def __init__(self, name, parent):
		self.parent = parent
		if self.parent is not None:
			self.name = self.parent.name + "." + name
		else:
			self.name = name
		self.start_time = 0
		self.total_time = 0
		
		if self.parent is not None:
			self.parent.child.append(self)
		self.child = []

	def getroot(self):
		if self.parent is None:
			return self
		return self.parent.getroot()

	def printiter(self):

		if self.total_time is None:
			raise Exception("Time not measured properly: %s" % self.name)
		
		# parent_total_time = self.parent.total_time if self.parent is not None else self.total_time
		longest_name = max([len(x) for x in time_checker.keys()])
		if self.parent is None:
			self.total_time = time_millis() - self.start_time
			total_time_len = len(convert_millis(self.total_time))
			print(("{0:%d}{1:%d}{2:10}" % (longest_name+5, total_time_len+5)).format("Name", "Time", "Global %"))
		
		global_total_time = self.getroot().total_time
		global_total_time_str = convert_millis(global_total_time)
		print(("{0:%d}{1:%d}{2:10}" % (longest_name+5, len(global_total_time_str)+5)).format(self.name, convert_millis(self.total_time), "%.2f%%" % (self.total_time / global_total_time * 100)))
		for item in sorted(self.child, key=lambda x: x.total_time):
			item.printiter()


def convert_millis(val):
	millis = val % 1000
	result = ".%2ds" % millis
	val /= 1000
	sec = val % 60
	result = ("%d" % sec) + result
	val /= 60
	minute = val % 60
	if minute > 0 or val / 60 > 0:
		result = ("%dm " % minute) + result
	val /= 60
	hour = val
	if hour > 0:
		result = ("%dh " % hour) + result
	return result
	


root = TimeHierarchy("R", None)
current_running_item = root
root.start_time = time_millis()

def time_analysis(except_keys=[]):
	root.printiter()
	# total_time = time_millis() - global_start_time
	# time_checker["Time Total"] = total_time
	# k = list(sorted([x for x in time_checker.keys() if x not in except_keys], key=lambda x: -time_checker[x]))

	# longest = max([len(x) for x in k])
	# for item in k:
	# 	v = time_checker[item]
	# 	print(("{0:%d}{1:10}{2:10}" % (longest+5)).format(item, "%.2fs" % (v / 1000), "%.2f%%" % (v / total_time * 100)))
	# del time_checker["Time Total"]

# def add_time_elem(key, amount):
# 	if key not in time_checker:
# 		time_checker[key] = TimeHierarchy(key, current_running_item)
# 	time_checker[key].total_time += amount

def enter(key):
	global current_running_item
	appended_key = current_running_item.name + key
	if appended_key not in time_checker:
		time_checker[appended_key] = TimeHierarchy(key, current_running_item)
	current_running_item = time_checker[appended_key]
	current_running_item.start_time = time_millis()

def out():
	global current_running_item
	current_running_item.total_time += time_millis() - current_running_item.start_time
	current_running_item = current_running_item.parent

def reset_time():
	time_checker = {}

def measure_time(fn):
	@functools.wraps(fn)
	def wrapper(*args, **kwargs):
		enter(fn.__name__)
		result = fn(*args, **kwargs)
		out()
		return result
	return wrapper

class TimeChecker():
	def __init__(self, name):
		self.name = name

	def __enter__(self):
		enter(self.name)

	def __exit__(self, type, value, traceback):
		out()