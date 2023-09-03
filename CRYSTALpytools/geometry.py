"""
Basic methods to manipulate pymatgen geometries
"""
def rotate_lattice(struc, rot):
    """
    Geometries generated by ``base.crysout.GeomBASE`` might be rotated.
    Rotate them back to make them consistent with geometries in output.

    .. math::
        \mathbf{L}_{crys} = \mathbf{L}_{pmg}\mathbf{R}

    :math:`\mathbf{R}` is the rotation matrix.

    Args:
        struc (Structure): Pymatgen structure
        rot (array): 3\*3 numpy array, rotation matrix.

    Returns:
        struc_new (Structure): Pymatgen structure
    """
    from pymatgen.core.lattice import Lattice
    from pymatgen.core.structure import Structure
    import numpy as np

    latt_mx = struc.lattice.matrix @ rot
    latt = Lattice(latt_mx, pbc=struc.pbc)
    spec = list(struc.atomic_numbers)
    coord = struc.frac_coords.tolist()
    struc_new = Structure(lattice=latt, species=spec, coords=coord, coords_are_cartesian=False)

    return struc_new

def refine_geometry(struc, **kwargs):
    """
    Get refined geometry. Useful when reducing the cell to the irrducible
    one. 3D only.

    Args:
        struc (Structure): Pymatgen structure
        **kwargs: Passed to Pymatgen `SpacegroupAnalyzer <https://pymatgen.org/pymatgen.symmetry.html#pymatgen.symmetry.analyzer.SpacegroupAnalyzer>`_ object.
    Returns:
        sg (int): Space group number
        pstruc (Structure): Symmetrized, irrducible structure
    """
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

    ndimen = struc.pbc.count(True)
    if ndimen < 3:
        raise Exception('This method is for 3D systems only.')

    analyzer = SpacegroupAnalyzer(struc, **kwargs)
    # Analyze the refined geometry
    struc2 = analyzer.get_refined_structure()
    analyzer2 = SpacegroupAnalyzer(struc2, **kwargs)
    struc_pri = analyzer2.get_primitive_standard_structure()
    analyzer3 = SpacegroupAnalyzer(struc_pri, **kwargs)

    pstruc = analyzer3.get_symmetrized_structure()
    sg = analyzer2.get_space_group_number()

    if sg >= 143 and sg < 168:  # trigonal, convert to hexagonal
        pstruc = analyzer3.get_conventional_standard_structure()
        analyzer4 = SpacegroupAnalyzer(pstruc, **kwargs)
        pstruc = analyzer4.get_symmetrized_structure()

    return sg, pstruc

def get_pcel(struc, smx):
    """
    Restore the supercell to primitive cell, with the origin shifted to the
    middle of lattice to utilize symmetry (as the default of CRYSTAL).

    Args:
        struc (Structure): Pymatgen structure of supercell
        smx (array): 3\*3 array of supercell expansion matrix
    Returns:
        pcel (Structure): Pymatgen structure of primitive cell
    """
    from pymatgen.core.structure import Structure
    from pymatgen.core.lattice import Lattice
    import numpy as np

    ndimen = struc.pbc.count(True)
    pbc = struc.pbc
    natom = struc.num_sites

    # That forces origin back to (0.5,0.5,0.5), but makes pbc to be 3D
    struc.make_supercell([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    shrink_mx = np.linalg.inv(smx)
    scel_mx = struc.lattice.matrix
    all_species = list(struc.atomic_numbers)
    # Shift origin to (0,0,0), consistent with CRYSTAL
    all_coords = struc.cart_coords
    for i in range(natom):
        for j in range(ndimen):
            all_coords[i, 0:ndimen] -= 0.5 * scel_mx[j, 0:ndimen]

    pcel_mx = shrink_mx @ scel_mx
    pcel_latt = Lattice(pcel_mx, pbc=pbc)
    # Fractional coords of pcel: Both periodic and no periodic sites
    all_coords = all_coords @ np.linalg.inv(pcel_mx)
    pcel_coords = []
    pcel_species = []
    for i, coord in enumerate(all_coords.round(12)): # Slightly reduce the accuracy
        if np.any(coord[0:ndimen] > 0.5) or np.any(coord[0:ndimen] <= -0.5):
            continue
        else:
            pcel_coords.append(coord)
            pcel_species.append(all_species[i])

    # For low dimen systems, this restores the non-periodic vecter length
    pcel = Structure(lattice=pcel_latt, species=pcel_species,
                     coords=pcel_coords, coords_are_cartesian=False)
    return pcel

def get_scel(struc, smx):
    """
    Get the supercell from primitive cell, with the origin shifted to the
    middle of lattice to utilize symmetry (as the default of CRYSTAL).

    Args:
        struc (Structure): Pymatgen structure of supercell
        smx (array): 3\*3 array of supercell expansion matrix
    Returns:
        scel (Structure): Pymatgen structure of supercell
    """
    from pymatgen.core.structure import Structure
    from pymatgen.core.lattice import Lattice

    ndimen = struc.pbc.count(True)
    pbc = struc.pbc
    natom = struc.num_sites

    struc.make_supercell(smx)
    scel_mx = struc.lattice.matrix
    all_species = list(struc.atomic_numbers)
    # Shift origin to (0,0,0), consistent with CRYSTAL
    all_coords = struc.cart_coords
    for i in range(natom):
        for j in range(ndimen):
            all_coords[i, 0:ndimen] -= 0.5 * scel_mx[j, 0:ndimen]

    scel_latt = Lattice(struc.lattice.matrix, pbc=pbc)

    scel = Structure(lattice=scel_latt, species=all_species,
                     coords=all_coords, coords_are_cartesian=True)
    return scel

def get_sg_symmops(struc, **kwargs):
    """
    Get space group number and corresponding symmetry operations.

    Args:
        struc (Structure): Pymatgen Structure object.
        **kwargs: Passed to Pymatgen SpacegroupAnalyzer object.
    Returns:
        sg (int): Space group number
        n_symmops (int): number of symmetry operations
        symmops (array): n_symmops\*4\*3 array of symmetry operations
    """
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    import numpy as np

    # Analyze the refined geometry
    ref_struc = SpacegroupAnalyzer(struc, **kwargs).get_refined_structure()
    sg = SpacegroupAnalyzer(ref_struc, **kwargs).get_space_group_number()

    all_symmops = SpacegroupAnalyzer(ref_struc, **kwargs).get_symmetry_operations(cartesian=True)
    symmops = []
    n_symmops = 0
    for symmop in all_symmops:
        if np.all(symmop.translation_vector == 0.):
            n_symmops += 1
            symmops.append(
                np.vstack([symmop.rotation_matrix, symmop.translation_vector])
            )

    symmops = np.reshape(np.array(symmops, dtype=float), [n_symmops, 4, 3])

    return sg, n_symmops, symmops

