
class Buffer():
	def __init__(self, max_num):
		self.buffer = {}
		self.max_num = max_num
		self.decay_iter = max_num / 10
		self.decay_rate = 0.05
		self.it = 0

	def __getitem__(self, query):
		if query not in self.buffer:
			return None
		result = self.buffer[query]
		result.access_count += 1
		self.it += 1
		if self.it % decay_iter == 0:
			self.it = 0
			for v in self.buffer.values():
				v.access_count *= 1-self.decay_rate
		return result

	def __setitem__(self, query, value):
		val = BufferElem(value)
		val.access_count += 1
		if len(self.buffer) >= self.max_num:
			m = self.max_num
			mk = None
			for k, v in self.buffer.items():
				if v.access_count < m:
					m = v.access_count
					mk = k
			del self.buffer[k]
		self.buffer[query] = val



class BufferElem():
	def __init__(self, value):
		self.value = value
		self.access_count = 0