import numpy as np
import copy
import itertools
import re

# All code in this file from the SpectroscPy script package (https://gitlab.com/kdu002/SpectroscPy and https://pypi.org/project/SpectroscPy/) in verbatim or near-verbatim form. See README.md for more information.

# Class to hold information about a response property
class rspProperty:

	def __init__(self, order, ops, comps, freqs, tensor=None):

		self.order = order
		self.ops = ops
		self.comps = comps
		self.freqs = freqs

		# May optionally add tensor at initialization, marking as default that this is not done
		self.hasTensor = 0

		# Adding tensor if given and if so, specifying that it was given
		if tensor is not None:

			self.hasTensor = 1
			self.tensor = tensor

	# May add tensor later if wanted
	def addTensor(self, tensor):

		self.hasTensor = 1
		self.tensor = tensor

	# Print summary of property
	def tellProp(self):

		print 'Order is', self.order
		print 'Operators are', self.ops
		print 'Number of components are', self.comps
		print 'Frequencies are', self.freqs

		# Also print tensor if it has been provided
		if (self.hasTensor):

			print 'Tensor:'
			print self.tensor			

# Take the specification prop of a property and an index of the associated tensor
# Generate all equivalent tensor indices based on perturbation equivalence symmetry
# Assumes that perturbations have been sorted according to operator and according
# to frequency within collections of identical operators
# Also assumes that operators with same labels have same number of components
def get_perm_ind(prop, index):

	# Find number of blocks by perturbation equivalence

	# Initial setup
	num_blocks = 0
	blocks = [[0,1]]
	blk = 0

	# Traverse all perturbations
	for i in range(prop.order):

		# If operator is the same, test frequency value
		if (prop.ops[i] == prop.ops[blocks[blk][0]]):

			# If frequency value is the same, set new end point of block to this perturbation
			if (prop.freqs[i] == prop.freqs[blocks[blk][0]]):

				blocks[blk][1] = i + 1

			# Otherwise, end this block and start a new one at next perturbation
			else:

				blocks[blk][1] = i
				blk += 1
				blocks.append([i,i+1])

		# Otherwise, end this block and start a new one at next perturbation	
		else:

			blocks[blk][1] = i
			blk += 1
			blocks.append([i,i+1])

	# For each block:
	# Generate permutations of associated indices but keep only unique
	blk_perms = []

	for i in range(blk + 1):

		blk_perms.append([list(j) for j in itertools.permutations(index[blocks[i][0]:blocks[i][1]])])

		new_blk_perms = []
		
		for j in range(len(blk_perms[i])):

			if not blk_perms[i][j] in new_blk_perms:

				new_blk_perms.append(copy.deepcopy(blk_perms[i][j]))
			
		blk_perms[i] = copy.deepcopy(new_blk_perms)

	# Build direct product of block permutations block by block

	prod_blocks = blk_perms[0]

	for i in range(1, blk + 1):

		prod_blocks = [list(j) for j in itertools.product(prod_blocks, blk_perms[i])]

		sing_list = []

		# Collapse list of lists into single list
		for j in range(len(prod_blocks)):

			sing_list.append([])

			for k in range(len(prod_blocks[j])):

				sing_list[j].extend(prod_blocks[j][k])

		prod_blocks = copy.deepcopy(sing_list)
		
	# Turn every permutation thus generated into tuples and decrement by one since counting starts at zero
	for i in range(len(prod_blocks)):

		prod_blocks[i] = tuple([j - 1 for j in prod_blocks[i]])

	return prod_blocks		

# Check if keyword inp matches the expected string compare; if not then quit (currently not gracefully)
def keyw_chk(inp, compare):

	if (inp == compare):
		return
	else:
		print 'Input read error: Expected keyword '
		print compare
		print ' but read '
		print inp
		# Maybe graceful quit instead
		print fdsafds
		return

# Read a line from a file and skip leading and trailing whitespace and newline
def rline(f):

	return f.readline().rstrip('\n').rstrip().lstrip()

# Read a tensor file, return a list of property class instances and individual data as numpy arrays
def read_orsp_tensor_file(fname):

	f = open(fname, 'r')

	keyw_chk(rline(f), 'VERSION')

	format_version = int(rline(f))

	if not (format_version == 1):
		print 'ERROR: File format version was given as ', format_version, ' but only version 1 is supported in this routine'
		return [], []

	keyw_chk(rline(f), 'NUM_PROPERTIES')

	nprops = int(rline(f))

	rsp_prop_specs = []
	rsp_tensors = []

	# Loop over number of properties that it was told that this file contains
	for i in range(nprops):

		keyw_chk(rline(f), 'NEW_PROPERTY')

		# Order (number of perturbations) for this property
		keyw_chk(rline(f), 'ORDER')
		curr_order = int(rline(f))
		
		# Number of frequency configurations given for this property
		keyw_chk(rline(f), 'NUM_FREQ_CFGS')
		curr_n_cfgs = int(rline(f))

		# Specification of perturbing operators associated with this property
		keyw_chk(rline(f), 'OPERATORS')
		
		curr_ops = []

		for j in range(curr_order):
			curr_ops.append(rline(f))

		# Specification of number of components for each operator
		keyw_chk(rline(f), 'NUM_COMPONENTS')

		curr_ncomps = []

		for j in range(curr_order):
			curr_ncomps.append(int(rline(f)))

		# Specification of frequencies associated with perturbations
		keyw_chk(rline(f), 'FREQUENCIES')

		curr_freqs = []

		# Loop over number of frequency configurations
		for j in range(curr_n_cfgs):

			curr_freqs.append([])

			# Marks start of new frequency configuration
			keyw_chk(rline(f), 'CONFIGURATION')

			for k in range(curr_order):
				curr_freqs[j].append(float(rline(f)))


		# Specification of values of the associated tensor (or tensors if more than one freq. config.)
		keyw_chk(rline(f), 'VALUES')

		# Loop over frequency configurations
		for j in range(curr_n_cfgs):

			# Marks start of new frequency configuration
			keyw_chk(rline(f), 'CONFIGURATION')
			curr_tensor = np.zeros(tuple(curr_ncomps))

			# Make new instance of property class for this property with this freq. config. 
			new_prop = rspProperty(curr_order, curr_ops, curr_ncomps, curr_freqs[j])

			# Reading values of tensor elements until done
			tensor_done = 0

			while not(tensor_done):

				prev_line = f.tell()

				nline = f.readline()

				# If reached EOF, break read
				if nline == '':

					break

				nline = nline.rstrip('\n').rstrip().lstrip()

				# If starting new property, undo line read consider this tensor read done
				if (nline == 'NEW_PROPERTY'):
					tensor_done = 1
					f.seek(prev_line)

				# If starting new frequency configuration, undo line read and consider this tensor read done
				elif (nline == 'CONFIGURATION'):
					tensor_done = 1
					f.seek(prev_line)
				else:
					
					# Read index of tensor whose value is to be specified on next line
					new_index = tuple([int(m) for m in nline.split()])
					# Read the value of tensor element with this index
					new_val = float(rline(f))

					# Get all permutations of indices known to have same value
					# due to symmetry of perturbations
					all_perm_ind = get_perm_ind(new_prop, new_index)

					# Assign the read tensor element value to all such valid permuted indices
					for k in all_perm_ind:

						curr_tensor[k] = new_val

			# Append the property specification and tensor to the arrays to be returned			
			rsp_prop_specs.append(new_prop)
			rsp_tensors.append(curr_tensor)

	return rsp_prop_specs, rsp_tensors


