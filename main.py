# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import solidspy.preprocesor as pre
import solidspy.postprocesor as pos
import solidspy.assemutil as ass
import solidspy.solutil as sol
import multiprocessing as mp


def solids_GUI(plot_contours=True, compute_strains=False, folder = None ):
    """
    Run a complete workflow for a Finite Element Analysis

    Parameters
    ----------
    plot_contours : Bool (optional)
        Boolean variable to plot contours of the computed variables.
        By default it is True.
    compute_strains : Bool (optional)
        Boolean variable to compute Strains and Stresses at nodes.
        By default it is False.
    folder : string (optional)
        String with the path to the input files. If not provided
        it would ask for it in a pop-up window.

    Returns
    -------
    UC : ndarray (nnodes, 2)
        Displacements at nodes.
    E_nodes : ndarray (nnodes, 3), optional
        Strains at nodes. It is returned when `compute_strains` is True.
    S_nodes : ndarray (nnodes, 3), optional
        Stresses at nodes. It is returned when `compute_strains` is True.

    """
    if folder is None:
        folder = pre.initial_params()




    #Number of processes
    pool = mp.Pool(mp.cpu_count())
    print (mp.cpu_count())
    start_time = datetime.now()
    echo = False

    # Pre-processing
    nodes, mats, elements, loads = pre.readin(folder=folder)
    if echo:
        pre.echomod(nodes, mats, elements, loads, folder=folder)
    DME , IBC , neq = ass.DME(nodes, elements)
    print("Number of nodes: {}".format(nodes.shape[0]))
    print("Number of elements: {}".format(elements.shape[0]))
    print("Number of equations: {}".format(neq))

    # System assembly
    KG = ass.assembler(elements, mats, nodes, neq, DME)
    RHSG = ass.loadasem(loads, IBC, neq)

    #below line exectued code without paralelisation
    #UG = sol.static_sol(KG, RHSG)
    # paralelisation System solution
    UG = pool.apply(sol.static_sol,[KG, RHSG])

    if not(np.allclose(KG.dot(UG)/KG.max(), RHSG/KG.max())):
        print("The system is not in equilibrium!")
    end_time = datetime.now()
    print('Duration for system solution: {}'.format(end_time - start_time))
    pool.close()
    # Post-processing
    start_time = datetime.now()
    UC = pos.complete_disp(IBC, nodes, UG)
    E_nodes, S_nodes = None, None
    if compute_strains:
        E_nodes, S_nodes = pos.strain_nodes(nodes , elements, mats, UC)
    if plot_contours:
        pos.fields_plot(elements, nodes, UC, E_nodes=E_nodes, S_nodes=S_nodes)
    end_time = datetime.now()
    print('Duration for post processing: {}'.format(end_time - start_time))
    print('Analysis terminated successfully!')
    return (UC, E_nodes, S_nodes) if compute_strains else UC


if __name__ == '__main__':
    displacement = solids_GUI()
    plt.show()
