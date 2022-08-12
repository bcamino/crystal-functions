#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A comprehensive module for lattice dynamics based on harmonic and quasiharmonic
approximations.
"""
from crystal_functions.file_readwrite import Crystal_output


class Mode:
    """
    Class Mode - store important information for a given vibrational mode. Can
    be used for a single harmonic phonon calculation and multiple calculations
    on the same system.

    Initialization:
        self.rank, __init__, The rank of the mode object. Start from 1.
        self.ncalc, __init__, The number of harmonic frequency calculations.
        self.frequency, __init__, Angular frequencies of the mode. Unit: THz
        self.volume, __init__, Cell volumes of harmonic calculations.
                     Unit: Angstrom^3
        self.eigenvector, __init__, Corresponding eigenvectors. Unit: Angstrom

    Limited to ncalc = 1 cases:
        self.zp_energy, get_zp_energy, Zero point energy of the mode.
                        Unit: KJ/mol cell
        self.U_vib, get_U_vib, Vibration contribution to internal energy,
                    including zero-point energy. Unit: KJ/mol cell
        self.entropy, get_entropy, Entropy of the mode. Unit: J/mol cell*K
        self.C_v, get_C_v, Constant volume specific heat. Unit: J/mol cell*K
    """

    def __init__(self, rank=0, frequency=[], volume=[], eigenvector=[]):
        """
        Input:
            rank, int, The rank of the mode object, from 1.
            frequency, ncalc * 1 array / list, Angular frequencies of the mode.
                       Unit: THz
            volume, ncalc * 1 array / list, Lattice volumes of harmonic
                    calculations. Unit: Angstrom^3
            eigenvector, ncalc * natom * 3 array / list, Corresponding
                         eigenvectors. Unit: Angstrom
        Output:
            self.rank
            self.ncalc, int, The number of harmonic calculations
            self.frequency
            self.volume
            self.eigenvector
        """
        import numpy as np

        self.rank = rank
        self.ncalc = len(frequency)
        self.frequency = np.array(frequency, dtype=float) * 2 * np.pi
        self.volume = np.array(volume, dtype=float)
        self.eigenvector = np.array(eigenvector, dtype=float)

    def get_zp_energy(self):
        """
        Get the zero-point energy of a single mode. Limited to ncalc = 1 cases.

        Input:
            -
        Output:
            self.zp_energy, float, Zero-point energy of a given mode.
                            Unit: KJ/mol cell
        """
        import numpy as np

        if self.ncalc > 1:
            print('Error: This modulus is limited to a single frequency calculation.')
            return

        hbar_freq = self.frequency[0] * 6.022141 * 6.626070E-2 / 2 / np.pi
        self.zp_energy = 0.5 * hbar_freq

        return self.zp_energy

    def get_U_vib(self, temperature=298.15):
        """
        Get the vibration contribution to internal energy of a single mode.
        Limited to ncalc = 1 cases. U_vib includes zero-point energy.

        Input:
            temperature: float, the temperature where the thermal contribution
                         is computed.
        Output:
            self.U_vib, float, Vibration contribution to internal energy of a
                        given mode. Unit: KJ/mol cell
        """
        import numpy as np

        if self.ncalc > 1:
            print('Error: This modulus is limited to a single frequency calculation.')
            return

        if not hasattr(self, 'zp_energy'):
            self.get_zp_energy()

        if temperature == 0:
            self.U_vib = self.zp_energy
            return self.U_vib

        hbar_freq = self.frequency[0] * 6.022141 * 6.626070E-2 / 2 / np.pi
        kb_t = 1.380649E-3 * 6.022141 * temperature
        expon = np.exp(hbar_freq / kb_t)
        self.U_vib = self.zp_energy + hbar_freq / (expon - 1)

        return self.U_vib

    def get_entropy(self, temperature):
        """
        Get the entropy of a single mode. Limited to ncalc = 1 cases.

        Input:
            temperature: float, the temperature where the thermal contribution
                         is computed.
        Output:
            self.entropy, float, The entropy of a given mode.
                          Unit: J/mol cell*K
        """
        import numpy as np

        if self.ncalc > 1:
            print('Error: This modulus is limited to a single frequency calculation.')
            return

        if temperature == 0:
            self.entropy = 0
            return self.entropy

        hbar_freq = self.frequency[0] * 6.022141 * 6.626070E-2 / 2 / np.pi
        kb_t = 1.380649E-3 * 6.022141 * temperature
        expon = np.exp(hbar_freq / kb_t)
        entS = kb_t * (hbar_freq / kb_t / (expon - 1) - np.log(1 - 1 / expon))
        self.entropy = entS / temperature * 1000

        return self.entropy

    def get_C_v(self, temperature):
        """
        Get the constant volume specific heat of a single mode. Limited to
        ncalc = 1 cases.

        Input:
            temperature: float, the temperature where the thermal contribution
                         is computed.
        Output:
            self.C_v, float, The constant volume specific heat of a given mode.
            Unit: J/mol cell*K
        """
        import numpy as np

        if self.ncalc > 1:
            print('Error: This modulus is limited to a single frequency calculation.')
            return

        if temperature == 0:
            self.C_v = 0
            return self.C_v

        hbar_freq = self.frequency[0] * 6.022141 * 6.626070E-2 / 2 / np.pi
        kb_t = 1.380649E-3 * 6.022141 * temperature
        expon = np.exp(hbar_freq / kb_t)

        self.C_v = hbar_freq**2 / kb_t / \
            temperature * expon / (expon - 1)**2 * 1000

        return self.C_v


class Harmonic(Crystal_output):
    """
    Class Harmonic, inherited from the Crystal_output class, with thermodynamic
    attributes. Used for harmonic phonon calclulations. Harmonic object can be
    defined by either a harmonic phonon calculation output file or manually set
    the all the information (usually for QHA).

    Inherited attributes:
        self.edft (length should be 1)
        self.nqpoint
        self.qpoint
        self.nmode
        self.frequency
        self.eigenvector

    New attributes:
        self.strucrure, The pymatgen Structure object of the calculation cell.
        self.mode, The list of mode objects.
        self.temperature, The temperature range for HA thermodynamics.
        self.pressure, The pressure range for HA thermodynamics.
        self.helmholtz, Helmholtz free energy of the cell, at HA level.
                        Unit: KJ/mol cell
        self.gibbs, Gibbs free energy of the cell, at HA level.
                    Unit: KJ/mol cell
        * Following attributes are the summed up values of corresponding
          attributes of class Mode.
        self.U_vib, thermodynamics
        self.zp_energy, thermodynamics 
        self.entropy, thermodynamics
        self.C_v, thermodynamics
    """

    def __init__(self):
        pass

    def from_file(self, output_name, temperature=[298.15], pressure=[0.],
                  scelphono=[], write_out=True, filename='HA-thermodynamics.dat'):
        """
        Generate the Harominc object from a HA file.

        Input:
            output_name, str, Name of the output file.
            temperature, nTempt * 1 array / list, Temperatures where the
                         thermodynamic properties are computed. Unit: K
            pressure, npress * 1 array / list, Pressures where the
                      thermodyanmic properties are calculated. Unit: GPa
            scellphono, ndimension * ndimension list, Supercell manipulation
                        matrix used for vibrational properties. Should be the
                        same as 'SCELPHONO' keyword in CRYSTAL input file. 3x3
                        list is also allowed.
            write_out, bool, Wheter to print out HA thermodynamic properties.
            filename, str, Name of the printed-out file, used only if
                      write_out = True.
        Output:
            self.mode, nqpoint * nmode array, List of mode objects at all
                       qpoints.
            self.temperature, nTempt * 1 array / list, Temperature range.
                              Unit: K
            self.pressure, nTempt * 1 array / list, Pressure range. Unit: GPa
            self.structure, pymatgen Structure object. The calculation cell
                            without the 'SCELPHONO' expansion.
            self.mode, nqpoint * nmode list, List of mode objects at all
                       qpoints.
            filename, text file, HA thermodynamic data. 'Thermodynamics' method
                      will be automatically executed and a file will be printed
                      out, if write_out = True.
        """
        import numpy as np

        if hasattr(self, "volume"):
            return "ERROR: Data exists. Cannot overwriting the existing data."

        super(Harmonic, self).read_cry_output(output_name)
        self.temperature = np.array(temperature, dtype=float)
        self.pressure = np.array(pressure, dtype=float)
        self.get_mode()
        self.clean_imaginary()
        self.generate_structure(scelphono=scelphono)

        if len(self.edft) != 1:
            return "ERROR: Only a single frequency calculation is premitted."
        else:
            self.edft = self.edft[0]

        # Transfer the modes in self.freqency into lists of mode objects
        self.mode = []
        for qpoint in self.frequency:
            qmode = []
            for m, freq in enumerate(qpoint):
                qmode.append(
                    Mode(rank=m + 1, frequency=[freq], volume=[self.volume]))

            self.mode.append(qmode)

        if write_out:
            self.thermodynamics(sumphonon=True)
            wtout = open(filename, 'w')
            self.print_results(file=wtout)
            wtout.close()

        return self

    def generate_structure(self, scelphono):
        """
        Eliminate the influences of the keyword 'SCELPHONO' and generate the
        pymatgen 'structure' object of the actual cell used for phonon
        calculation. Not a standalone method.

        Input:
            scellphono, ndimension * ndimension list. 3*3 list is also allowed.
        Output:
            self.structure, pymatgen Structure object. The calculation cell
                            without 'SCELPHONO' expansion.
            self.natom, int, Number of atoms in the cell.
            self.volume, float, pymatgen structure.volume. Cell volume.
                         Unit: Angstrom^3
        """
        from crystal_functions.convert import cry_out2pmg
        from pymatgen.core.structure import Structure
        import numpy as np

        ndimen = self.get_dimensionality()

        if not scelphono or not ndimen:
            self.structure = cry_out2pmg(self, vacuum=100)
            self.natom = len(self.structure.species)
            self.volume = self.structure.volume

            return self

        scell_mx = np.eye(3, dtype=float)
        scell_mx[: ndimen, : ndimen] = np.array(scelphono)[: ndimen, : ndimen]
        shrink_mx = np.linalg.pinv(scell_mx)

        scel = cry_out2pmg(self, vacuum=100)

        pcel_lattice = np.dot(scel.lattice.matrix, shrink_mx)
        all_coord = np.dot(
            scel.cart_coords, np.linalg.pinv(pcel_lattice)).tolist()
        all_species = scel.species

        pcel_coord = []
        pcel_species = []

        for i, coord in enumerate(all_coord):
            if coord[0] >= 1 or coord[0] < 0 or \
               coord[1] >= 1 or coord[1] < 0 or \
               coord[2] >= 1 or coord[2] < 0:
                continue
            else:
                pcel_coord.append(coord)
                pcel_species.append(all_species[i])

        pcel_natom = len(pcel_species)
        pcel_charge = int(scel.charge * pcel_natom / len(all_species))

        self.structure = Structure(
            pcel_lattice, pcel_species, pcel_coord, pcel_charge)
        self.natom = len(self.structure.species)
        self.volume = self.structure.volume

        return self

    def phonon_sumup(self, temperature=None):
        """
        Summing up inidival phonon modes at each q point. Translational modes
        with frequencies = 0 are skipped.

        Not a standalone method. For thermodynamics, use 'self.thermodyanmics'
        instead.

        Input:
            temperature, float, The temperature where the U_vib, entropy and
                         C_v are calculated. If = None, zero_point energy will
                         be calculated.
        Output:
            zp_energy, nqpoint * 1 array, Zero-point energy at a given q point.
                       Returned if temperature = None.
            U_vib, nqpoint * 1 array, Vibrational contribution to internal
                   energy at constant temperature and all q points. Returned
                   if temperature is given.
            entropy, nqpoint * 1 array, Entropy at constant temperature and
                     given q point. Returned if temperature is given.
            C_v, nqpoint * 1 array, Constant volume specific heat at constant
                 temperature and given q point. Returned if temperature is
                 given.
        """
        import numpy as np

        if temperature == None:
            zp_energy = np.array([], dtype=float)
            for qpoint in self.mode:
                zp_energy_q = 0.
                # Remove the translational modes
                for mode in qpoint:
                    if not np.isnan(mode.frequency) and mode.frequency > 1e-5:
                        zp_energy_q += mode.get_zp_energy()

                zp_energy = np.append(zp_energy, zp_energy_q)

            return zp_energy
        else:
            T = temperature
            U_vib = np.array([], dtype=float)
            entropy = np.array([], dtype=float)
            C_v = np.array([], dtype=float)
            for qpoint in self.mode:
                U_vib_q = 0.
                entropy_q = 0.
                C_v_q = 0.
                # Remove the translational modes
                for mode in qpoint:
                    if not np.isnan(mode.frequency) and mode.frequency > 1e-5:
                        U_vib_q += mode.get_U_vib(temperature=T)
                        entropy_q += mode.get_entropy(temperature=T)
                        C_v_q += mode.get_C_v(temperature=T)

                U_vib = np.append(U_vib, U_vib_q)
                entropy = np.append(entropy, entropy_q)
                C_v = np.append(C_v, C_v_q)

            return U_vib, entropy, C_v

    def thermodynamics(self, sumphonon=True):
        """
        Calculate the thermodynamic properties (zp_energy, U_vib, entropy, C_v
        and Helmholtz free energy) of the given system, at all qpoints and the
        whole temperature range.

        Input:
            sumphonon, bool, Whether summing up the phonon contributions across
                       the first Brillouin zone.
        Output:
            self.helmholtz, nqpoint * nTempt numpy array, Helmholtz free energy.
                            Unit: KJ/mol cell
            self.gibbs, nqpoint * nTempt * npress numpy array, Gibbs free energy.
                        Unit: KJ/mol cell
            self.zp_energy, nqpoint * 1 numpy array, Zero-point energy.
                            Unit: KJ/mol cell
            self.U_vib, nqpoint * nTempt numpy array, Vibrational contribute to
                        internal energy. Unit: KJ/mol cell
            self.entropy, nqpoint * nTempt numpy array, Entropy.
                          Unit: J/mol cell*K
            self.C_v, nqpoint * nTempt numpy array, Constant volume specific
                      heat. Unit: J/mol cell*K

        Note: If sumphonon = True, the thermodyanmic properties of phonon 
              dispersion are summed. In this case, nqpoint = 1 but the
              dimension is kept.
        """
        import numpy as np

        self.zp_energy = self.phonon_sumup()
        U_vib = []
        entropy = []
        C_v = []
        helmholtz = []
        gibbs = []

        for T in self.temperature:
            gibbs_t = []
            U_vib_t, entropy_t, C_v_t = self.phonon_sumup(temperature=T)
            helm_t = -entropy_t * T + U_vib_t + self.edft

            for p in self.pressure:
                gibbs_tp = p * self.volume * 0.602214 + helm_t
                gibbs_t.append(gibbs_tp)

            # nTemp * nqpoint
            U_vib.append(U_vib_t)
            entropy.append(entropy_t)
            C_v.append(C_v_t)
            helmholtz.append(helm_t)
            # nTemp * npress * nqpoint
            gibbs.append(gibbs_t)

        U_vib = np.transpose(np.array(U_vib, dtype=float))
        entropy = np.transpose(np.array(entropy, dtype=float))
        C_v = np.transpose(np.array(C_v, dtype=float))
        helmholtz = np.transpose(np.array(helmholtz, dtype=float))
        gibbs = np.transpose(np.array(gibbs, dtype=float), (2, 0, 1))

        if sumphonon:
            self.U_vib = np.array([np.sum(U_vib, axis=0)])
            self.entropy = np.array([np.sum(entropy, axis=0)])
            self.C_v = np.array([np.sum(C_v, axis=0)])
            self.helmholtz = np.array([np.sum(helmholtz, axis=0)])
            self.gibbs = np.array([np.sum(gibbs, axis=0)])
            self.nqpoint = 1
            self.qpoint = np.array([[0., 0., 0.]], dtype=float)
        else:
            self.U_vib = U_vib
            self.entropy = entropy
            self.C_v = C_v
            self.helmholtz = helmholtz
            self.gibbs = gibbs

        return self.helmholtz, self.gibbs, self.zp_energy, self.U_vib,\
            self.entropy, self.C_v

    def print_results(self, file):
        """
        Print a single output file for HA thermodynamics. Used if write_out=True.

        Note: Phonon dispersions are forced to be summed to keep the output
        succinct if the automatic scheme (write_out=True) is launched. To get
        verbose outputs, directly use this attribute.

        Input:
            file, file object obtained by 'open' command.
        Output:
            filename, text file.
        Format:
# DFT TOTAL ENERGY =         edft eV,         =         edft kJ/mol
# CELL VOLUME      = volume       Angstrom^3, =       volume cm^3/mol
# LATTICE PARAMETERS (ANGSTROM, DEGREE)
           A           B           C       ALPHA        BETA       GAMMA
           a           b           c       alpha        beta       gamma

# HARMONIC THERMODYNAMICS AT QPOINT #   rank of qpoint

  zero point energy =    zp_energy kJ/mol

  temperature dependent properties
    T(K)     U_vib(kJ/mol)  Entropy(J/mol*K)      C_V(J/mol*K) Helmholtz(kJ/mol)
   Tempt             U_vib           entropy               C_v         Helmholtz
   ...

  Gibbs free energy
    rows    : pressure (GPa)  pressure list
    columns : temperature (K) temperature list
    data  data  data  ...
    ...


# HARMONIC THERMODYNAMICS AT QPOINT #   rank of qpoint

  zero point energy =    zp_energy kJ/mol

  temperature dependent properties
    T(K)     U_vib(kJ/mol)  Entropy(J/mol*K)      C_V(J/mol*K) Helmholtz(kJ/mol)
   Tempt             U_vib           entropy               C_v         Helmholtz
   ...

  Gibbs free energy
    rows    : pressure (GPa)  pressure list
    columns : temperature (K) temperature list
    data  data  data  ...
    ...


        """
        file.write('%-21s%12.4e%-15s%12.4e%-10s\n' %
                   ('# DFT TOTAL ENERGY = ', self.edft * 2625.500256,
                    ' eV,         = ', self.edft, ' kJ/mol'))
        file.write('%-21s%12.6f%-15s%12.6f%-10s\n' %
                   ('# CELL VOLUME      = ', self.volume,
                    ' Angstrom^3, = ', self.volume * 0.602214, ' cm^3/mol'))
        file.write('%s\n' % '# LATTICE PARAMETERS (ANGSTROM, DEGREE)')
        file.write('%12s%12s%12s%12s%12s%12s\n' % ('A', 'B', 'C',
                                                   'ALPHA', 'BETA', 'GAMMA'))
        file.write('%12.4f%12.4f%12.4f%12.4f%12.4f%12.4f\n\n' %
                   (self.structure.lattice.parameters[0:6]))

        for q in range(self.nqpoint):
            file.write('%-40s%5i\n\n' %
                       ('# HARMONIC THERMODYNAMICS AT QPOINT #', q))
            file.write('%-23s%12.6e%8s\n\n' %
                       ('  zero point energy = ', self.zp_energy[q], ' kJ/mol'))
            file.write('%s\n' % '  temperature dependent properties')
            file.write('%8s%18s%18s%18s%18s\n' %
                       ('    T(K)', 'U_vib(kJ/mol)', 'Entropy(J/mol*K)',
                        'C_V(J/mol*K)', 'Helmholtz(kJ/mol)'))
            for t, tempt in enumerate(self.temperature):
                file.write('%8.2f%18.6e%18.6e%18.6e%18.6e\n' %
                           (tempt, self.U_vib[q, t], self.entropy[q, t],
                            self.C_v[q, t], self.helmholtz[q, t]))

            file.write('\n')
            file.write('%s\n' % '  Gibbs free energy')
            file.write('%-30s' % '    rows    : pressure (GPa)  ')
            for p in self.pressure:
                file.write('%8.3f%1s' % (p, ''))

            file.write('\n')
            file.write('%-30s' % '    columns : temperature (K) ')
            for t in self.temperature:
                file.write('%8.3f%1s' % (t, ''))

            for gibbs_t in self.gibbs[q]:
                file.write('\n%4s' % '')
                for gibbs_p in gibbs_t:
                    file.write('%18.6e%2s' % (gibbs_p, ''))

            file.write('\n\n\n')

        return
