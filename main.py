#!/usr/bin/python

import csv, sys, itertools

class AprioriExtractor:

	def __init__(self, datafile, min_sup, min_conf):
		self.datafile = datafile
		self.min_sup = min_sup
		self.min_conf = min_conf
		self.discrete_granularity = [-1, -1, -1, 50, 50, 50000, 1000000, 20, 5000000, 50]
		self.discrete_start = [0, 0, 0, 50, 1850, 50000, 1000000, 20, 5000000, 50]

	def run(self):
		# read data
		database, header = self.loadData()
		if not database:
			print 'Error reading data file'
			return
		
		# sort items in transactions
		for transac in database:
			transac.sort()

		# initialize data structures
		L = [[] for i in range(2)]
		Supports = [{} for i in range(2)]

		# compute large 1-itemsets
		candidates = [(item,) for item in set(itertools.chain(*database))]
		Supports[1] = self.selectCandidates(candidates, database)
		L[1] = Supports[1].keys()
		
		# compute large k-itemsets
		i = 1
		while len(L[i]) != 0:
			i += 1
			candidates = self.apriorGen(L[i-1])
			Supports.append(self.selectCandidates(candidates, database))
			L.append(Supports[i].keys())
		Supports.pop()
		L.pop()
		
		# extract rules
		rules = self.extract1RRules(L, Supports)
		print rules

	def loadData(self):
		database = header = None
		# read raw from file
		with open(self.datafile, 'r') as csvfile:
			csvreader = csv.reader(csvfile)
			header = csvreader.next()
			database = []
			for row in csvreader:
				database.append(map(lambda i: (i, row[i]), range(len(row))))
		# discretize numeric attributes
		for i in range(len(header)):
			self.discretizeAttribute(database, i)
		return database, header

	def discretizeAttribute(self, database, k):
		# negative granularity means this is not a numeric attribute
		if self.discrete_granularity[k] < 0:
			return
		for row in database:
			bound = ((int(float(row[k][1])) - self.discrete_start[k]) / self.discrete_granularity[k] + 1) * self.discrete_granularity[k] + self.discrete_start[k]
			row[k] = (row[k][0], bound)

	# This function selects large itemsets and returns a dictionary with the keys large itemsets and the values supports
	def selectCandidates(self, candidates, database):
		support = dict.fromkeys(candidates, 0)
		for transac in database:
			transac_set = set(transac)
			for cand in candidates:
				if set(cand) <= transac_set:
					support[cand] += 1
		total = len(database)
		largeItemsetSupport = {key: val / float(total) for key, val in support.iteritems() if val / float(total) >= self.min_sup}
		return largeItemsetSupport

	# Return a list of candidates
	def apriorGen(self, l):
		# join step
		def largersets(l):
			for p in l:
				for q in l:
					if p == q:
						continue
					elif p[:-1] == q[:-1] and p[-1] < q[-1]:
						yield p + q[-1:]
		# prune step
		candidates = []
		for itemset in largersets(l):
			qual = True
			for sub in itertools.combinations(itemset, len(itemset) - 1):
				if sub not in l:
					qual = False
					break
			if qual:
				candidates.append(itemset)
		return candidates

	# Extract rules in such format: ((item1, item2,...), (itema, itemb,...))
	def extractRules(self, L, Supports):
		if len(L) <= 2:
			print 'No rule extracted'
			return
		rules = []
		for largesets in L:
			for lset in largesets:
				for lhs in itertools.chain.from_iterable(itertools.combinations(lset, i) for i in range(1, len(lset))):
					conf = Supports[len(lset)][lset] / Supports[len(lhs)][lhs]
					if conf >= self.min_conf:
						rhs = tuple(item for item in lset if item not in lhs)
						rules.append((lhs, rhs))
		return rules

	def extract1RRules(self, L, Supports):
		if len(L) <= 2:
			print 'No rule extracted'
			return
		rules = []
		for largesets in L:
			for lset in largesets:
				for lhs in itertools.combinations(lset, len(lset) - 1):
					conf = Supports[len(lset)][lset] / Supports[len(lhs)][lhs]
					if conf >= self.min_conf:
						rhs = tuple(item for item in lset if item not in lhs)
						rules.append((lhs, rhs))
		return rules

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print 'Usage: main.py datafile min_sup min_conf'
		sys.exit()
	try:
		min_sup = float(sys.argv[2])
		min_conf = float(sys.argv[3])
	except:
		print 'Illegal parameters'
		sys.exit()

	extractor = AprioriExtractor(sys.argv[1], min_sup, min_conf)
	extractor.run()