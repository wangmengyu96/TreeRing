import sympy as sp
import networkx as nx
import numpy as np
from tree_ring.objects import StateVariable, BasisVariable

def expand(variable_power_mapping, state_variables, disturbance_variables, dependence_graph, moment_basis, reduced_muf = True):
    """
    Args:
        variable_power_mapping (Dictionary): dictionary mapping base variables to powers
        state_variables (set of StateVariable): state variables of the system
        disturbance_variables (set of DisturbanceVariable): disturbance variables of the system
        dependence_graph (networkx graph): nodes are instances of StateVariable, edges represent dependence between two variables
        moment_basis (moment_basis): list of instances of BasisVariable
    """
    # Derive the new relation.
    reduced_vpm = {var : power for var, power in variable_power_mapping.items() if power != 0}
    variable_expansions = [var.update_relation**power for var, power in reduced_vpm.items()]

    # Create a new basis variable and add it to the set of basis variables.
    new_basis_variable = BasisVariable(reduced_vpm, np.prod(variable_expansions))
    moment_basis.add(new_basis_variable)

    # Express in as a polynomial.
    state_variables_sympy = [var.sympy_rep for var in state_variables]
    poly = sp.poly(new_basis_variable.update_relation, state_variables_sympy)

    for multi_index in poly.monoms():
        # Iterate over multi-indicies for the monomials.
        # Construct a dictionary mapping base variables to their power in this monomial.
        new_vpm = {state_variables[i] : multi_index[i] for i in range(len(state_variables))}
        if reduced_muf == False:
            # We are finding a completion w.r.t. the un-reduced moment update form.
            update_relation_exists = any([d_var.equivalent_variable_power_mapping(new_vpm) for d_var in moment_basis])
            if update_relation_exists == False:
                expand(new_vpm, state_variables, disturbance_variables, dependence_graph, moment_basis, reduced_muf=reduced_muf)
        else:
            # We are finding a completion w.r.t. the reduced moment update form.
            # Need to first find a factorization.
            # Find the subgraph induced by multi_index.
            variables_in_mono = {state_variables[i] for i, degree in enumerate(multi_index) if degree != 0}
            dependence_subgraph = dependence_graph.subgraph(variables_in_mono)
            connected_components = list(nx.connected_components(dependence_subgraph))
            for comp in connected_components:
                component_var_power_map = {var : new_vpm[var] for var in comp}
                update_relation_exists = any([d_var.equivalent_variable_power_mapping(component_var_power_map) for d_var in moment_basis])
                if update_relation_exists == False:
                    expand(component_var_power_map, state_variables, disturbance_variables, dependence_graph, moment_basis, reduced_muf=reduced_muf)
    return moment_basis