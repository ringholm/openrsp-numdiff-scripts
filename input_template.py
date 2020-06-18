# This file is part of openrsp-numdiff-scripts.
# openrsp-numdiff-scripts is made available under an LGPL license.

# Adapt the parameters below to your specific situation
#
# The resulting file must be saved in the same folder as the other source files in this package and must have the extension .py

# Name of mol file of system 
# Must be a valid LSDalton mol file and must be identical to the mol file which was used to calculate the reference data
# Units of atom coordinates must be bohr
# Cannot be 'MOLECULE.INP' or 'numdiff_geo.mol' as these names are used by routines invoked by this script
fname_mol = 'MOLECULE.mol'

# Name of dal file to calculate the test property
# Must be a valid LSDalton dal file and must fulfill the following criteria to enable a proper comparison:
# - The level of theory must be identical to that used to calculate the reference data
# - The property specified in the **OPENRSP section must be one that is one fewer orders of geometrical
#   differentiation than the target property
# Cannot be 'LSDALTON.INP' as this name is used by routines invoked by this script
fname_dal = 'DALFILE.dal'

# Name of OpenRSP rsp_tensor file with reference results
fname_ref = 'TARGET_PROPERTY.rsp_tensor'

# Full path to the executable to be run to calculate the test property
fname_bin = '/home/this_user/software/lsdalton/build/lsdalton.x'

# Full path to basis set directory
basdir = '/home/this_user/software/lsdalton/basis'

# Number of points to use in stencil: Available choices are 2 and 7 (7 takes three times longer but is more accurate)
stencil_np = 2

# Geometric displacement (in bohr) to be used in numerical differentiation
# Different choices of this displacement may be suitable in different situations: As a rule of thumb, a displacement
# of 0.001 bohr has been seen to perform decently well
d = 0.001
