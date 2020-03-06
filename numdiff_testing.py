import numpy as np
import copy
import os
from openrsp_tensor_reader import *




# Read a Dalton mol file and return the information needed to write a corresponding file later on with write_mol
def read_mol(fname):

	f = open(fname, 'r')
	
	start_of_atoms = 0

	coords = []
	charges_per_type = []

	nline = f.readline()

	# Basis set given on the second line
	basis_set = f.readline()

	num_atoms_per_type = []

	while not(start_of_atoms):

		nline = f.readline()
		
		start_of_atoms = re.search('atomtypes', nline, flags=re.I)

		if (start_of_atoms):

			num_atomtypes = int(re.search('\d+', nline).group())

	for i in range(num_atomtypes):

		nline = f.readline()

		re.search('atomtypes', nline, flags=re.I)
		curr_charge = int(re.sub('charge\s*\=\s*', '', re.search('charge\s*\=\s*\d+', nline, flags=re.I).group(), flags=re.I))
		curr_num_atoms = int(re.sub('atoms\s*\=\s*', '', re.search('atoms\s*\=\s*\d+', nline, flags=re.I).group(), flags=re.I))

		charges_per_type.append(curr_charge)
		num_atoms_per_type.append(curr_num_atoms)

		for j in range(curr_num_atoms):

			nline = f.readline().split()
			coords.append([float(k) for k in nline[1:]])

	return basis_set, num_atomtypes, num_atoms_per_type, charges_per_type, coords

# Generate a Dalton mol file fname based on provided information
# Will overwrite fname if it already exists
# Will use nosymmetry flag
# Coordinate units assumed to be bohr
def write_mol(fname, basis_set, num_atomtypes, num_atoms_per_type, charges_per_type, coords):

	# Overwrites the existing file
	f = open(fname, 'w')

	f.write('BASIS\n')
	f.write(basis_set)

	f.write('Mol file generated by write_mol routine\n')
	f.write('This line intentionally left blank\n')
	f.write('AtomTypes=' + str(num_atomtypes) + ' Nosymmetry\n')

	acc_atom = 0

	for i in range(num_atomtypes):

		f.write('Charge=' + str(charges_per_type[i]) + ' Atoms=' + str(num_atoms_per_type[i]) + '\n')
		
		for j in range(num_atoms_per_type[i]):

			# Atoms will be called A1, A2, A3, ...
			# Can be changed later on to dictionary-style lookup of atom name based on nuclear charge
			f.write('A' + str(acc_atom + 1) + ' ' + str(coords[acc_atom][0]) + ' ' + str(coords[acc_atom][1]) + ' ' + str(coords[acc_atom][2]) + '\n' )

			acc_atom += 1

	f.write('')

	return

# Take a mol and dal file and execute an (LSDalton with OpenRSP) binary fname_bin with basis set directory basdir
# Return the appropriate response tensor
def do_rsp_calc(fname_mol, fname_dal, fname_bin, basdir):

	os.system('cp ' + fname_mol + ' MOLECULE.INP')
	os.system('cp ' + fname_dal + ' LSDALTON.INP')

	os.system('export BASDIR=' + basdir)

	os.system('echo $BASDIR')

	os.system(fname_bin)

	prop, tensor = read_orsp_tensor_file('rsp_tensor')

	return tensor[0]



# Do numerical differentiation and compare to reference data
# Input data: 
	# Template mol file fname_mol
	# Template lower-order dal file fname_dal
	# Result tensor from higher-order calculation fname_ref
	# Path to binary fname_bin
	# Path to basis set directory basdir
	# Displacement d to use for numerical differentiation (default = 0.001 bohr)
def perform_num_diff_and_compare(fname_mol, fname_dal, fname_ref, fname_bin, basdir, d=0.001):

	fname_mol_chg = 'numdiff_geo.mol'

	# Get reference property specification and tensor from reference file
	prop_ref, tensor_ref = read_orsp_tensor_file(fname_ref)
	tensor_ref = tensor_ref[0]

	# Get molecule information from mol file
	basis_set, num_atomtypes, num_atoms_per_type, charges_per_type, coords = read_mol(fname_mol)
	# Set up zeroed comparison tensor to be filled with num diff results
	tensor_cmp = np.zeros(tensor_ref.shape)

	acc_coord = 0

	# Change each coordinate of reference geometry in turn
	# Write altered mol file and run rsp calculation
	# Read resulting tensor and accumulate
	for i in range(len(coords)):

		for j in range(3):

			new_coords = copy.deepcopy(coords)

			# Make positive displacement and write altered mol file
			new_coords[i][j] += d
			write_mol(fname_mol_chg, basis_set, num_atomtypes, num_atoms_per_type, charges_per_type, new_coords)

			# Do response calculation with positively displaced geometry and get tensor
			tensor_p = do_rsp_calc(fname_mol_chg, fname_dal, fname_bin, basdir)

			# Make negative (double to counteract positive) displacement and write altered mol file
			new_coords[i][j] -= 2.0*d
			write_mol(fname_mol_chg, basis_set, num_atomtypes, num_atoms_per_type, charges_per_type, new_coords)

			# Do response calculation with negatively displaced geometry and get tensor
			tensor_m = do_rsp_calc(fname_mol_chg, fname_dal, fname_bin, basdir)

			# Put num diff result in comparison tensor
			tensor_cmp[acc_coord:acc_coord+1,:] = (tensor_p - tensor_m)/(2.0 * d)

			acc_coord +=1

			
	tensor_diff = tensor_ref - tensor_cmp

	print 'Maximum of reference data array', np.amax(tensor_ref)

	print 'Maximum difference between reference and and num diff data', np.amax(abs(tensor_diff))
	

	print 'Reference tensor', tensor_ref
	print 'Num diff tensor', tensor_cmp
	print 'Difference between reference and num diff data', tensor_diff

# Name of mol file of system 
fname_mol = 'HF.mol'
# Name of dal file to calculate tensor which will be differentiated
fname_dal = 'hf.dal'
# Name of OpenRSP rsp_tensor file with reference results
fname_ref = 'hf_HF.rsp_tensor'
# Path to the executable to be run
fname_bin = '/home/ringholm/Desktop/dev_lsdalton_openrsp/release-work/bld_numdiff/lsdalton.x'
# Path to basis set directory
basdir = '/home/ringholm/Desktop/dev_lsdalton_openrsp/release-work/basis'
# Geometric displacement used in numerical differentiation
d = 0.001

perform_num_diff_and_compare(fname_mol, fname_dal, fname_ref, fname_bin, basdir, d)




