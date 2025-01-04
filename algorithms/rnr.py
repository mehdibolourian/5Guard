from libraries import *

def random_round_iter(t, r_t, reqs_in, reqs_lp_t_in, X_t_in, Y_t_in, profit_in, file_name):
    profit = 0
    reject = [0,0,0]
    violat = 0
    migrat = 0
    deploy = 0
    timer  = 0
    
    reqs      = reqs_in.copy()
    reqs_lp_t = reqs_lp_t_in.copy()
    X_t       = X_t_in.copy()
    Y_t       = Y_t_in.copy()

    x = []
    y = []
    z = []
    c = []
    b = []
    
    # Auxiliary Variables
    u    = []
    u_h  = []
    a    = []
    a_h  = []
    o    = []
    o_h  = []
    o_h1 = []
    o_h2 = []
    o_h3 = []
    o_h4 = []

    ############## 5G-INS ##############
    # Create Optimization Model
    m = gp.Model("e2esliceiso")

    len_V_P_S = len(V_P_S)
    K_MAX = 101
    F_MAX = 1
    S_MAX = 1

    len_reqs     = len(reqs)
    len_vpaths   = max(len(r.E)   for idx_r, r in enumerate(reqs))
    len_vservers = max(len(r.V_S) for idx_r, r in enumerate(reqs))
    len_vrus     = max(len(r.V_R) for idx_r, r in enumerate(reqs))
    len_V_P_R    = len(V_P_R)
    len_E_P      = len(E_P)
    len_L        = len(L)
    len_L_pqi    = max(len(L_pqi[idx_e_p]) for idx_e_p, e_p in enumerate(E_P))

    if t == 0:
        u   = [[m.addVar(name=f"u_{idx_p}_{chi}", vtype=gp.GRB.CONTINUOUS, ub=1) for chi in range(sys.CHI_MAX+1)] for idx_p in range(len_V_P_S)]
        u_h = [m.addVar(name=f"u_h_{idx_p}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_p in range(len_V_P_S)]
    else:
        m.update()
        m = gp.read(str(file_name))
        m.update()

        u   = [[m.getVarByName(f"u_{idx_p}_{chi}") for chi in range(sys.CHI_MAX+1)] for idx_p in range(len_V_P_S)]
        u_h = [m.getVarByName(f"u_h_{idx_p}") for idx_p in range(len_V_P_S)]
    
        x = [[[m.getVarByName(f"x_{idx_r}_{idx_v}_{idx_p}") for idx_p in range(len_V_P_S)] for idx_v in range(len_vservers)] for idx_r in range(len_reqs-1)]
        y = [[[[[m.getVarByName(f"y_{idx_r}_{idx_v}_{idx_q}_{f}_{k}") for k in range(K_MAX)] for f in range(F_MAX)] for idx_q in range(len_V_P_R)] for idx_v in range(len_vrus)] for idx_r in range(len_reqs-1)]
        z = [[[[m.getVarByName(f"z_{idx_r}_{idx_e}_{idx_l}_{s}") for s in range(S_MAX)] for idx_l in range(len_L)] for idx_e in range(len_vpaths)] for idx_r in range(len_reqs-1)]
        c = [[[m.getVarByName(f"c_{idx_r}_{idx_v}_{idx_p}") for idx_p in range(len_V_P_S)] for idx_v in range(len_vservers)] for idx_r in range(len_reqs-1)]
        b = [[[[[m.getVarByName(f"b_{idx_r}_{idx_e}_{idx_l}_{pqi}_{s}") for s in range(S_MAX)] for pqi in range(len_L_pqi)] for idx_l in range(len_L)] for idx_e in range(len_vpaths)] for idx_r in range(len_reqs-1)]
        
        # Auxiliary Variables
        a    = [[[m.getVarByName(f"a_{idx_r}_{idx_v}_{idx_p}") for idx_p in range(len_V_P_S)] for idx_v in range(len_vpaths)] for idx_r in range(len_reqs-1)]
        a_h  = [[[m.getVarByName(f"a_h_{idx_r}_{idx_v}_{idx_p}") for idx_p in range(len_V_P_R)] for idx_v in range(len_vpaths)] for idx_r in range(len_reqs-1)]
        o    = [[[m.getVarByName(f"o_{idx_r}_{idx_v}_{idx_e}") for idx_e in range(len_E_P)] for idx_v in range(len_vpaths)] for idx_r in range(len_reqs-1)]
        o_h  = [[m.getVarByName(f"o_h_{idx_r}_{idx_v}") for idx_v in range(len_vpaths)] for idx_r in range(len_reqs-1)]
        o_h1 = [[m.getVarByName(f"o_h1_{idx_r}_{idx_v}") for idx_v in range(len_vpaths)] for idx_r in range(len_reqs-1)]
        o_h2 = [[m.getVarByName(f"o_h2_{idx_r}_{idx_p}") for idx_p in range(len_V_P_S)] for idx_r in range(len_reqs-1)]
        o_h3 = [[m.getVarByName(f"o_h3_{idx_r}_{idx_q}") for idx_q in range(len_V_P_R)] for idx_r in range(len_reqs-1)]
        o_h4 = [[m.getVarByName(f"o_h4_{idx_r}_{idx_l}") for idx_l in range(len_L)] for idx_r in range(len_reqs-1)]

    ############## 5G-INS ##############
    ## Decision Variables
    # Main Variables
    #print(len_reqs)

    #print(x)
    
    x.append([[m.addVar(name=f"x_{len_reqs-1}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_p in range(len_V_P_S)] for idx_v in range(len_vservers)])
    y.append([[[[m.addVar(name=f"y_{len_reqs-1}_{idx_v}_{idx_q}_{f}_{k}", vtype=gp.GRB.CONTINUOUS, ub=1) for k in range(K_MAX)] for f in range(F_MAX)] for idx_q in range(len_V_P_R)] for idx_v in range(len_vrus)])
    z.append([[[m.addVar(name=f"z_{len_reqs-1}_{idx_e}_{idx_l}_{s}", vtype=gp.GRB.CONTINUOUS, ub=1) for s in range(S_MAX)] for idx_l in range(len_L)] for idx_e in range(len_vpaths)])
    c.append([[m.addVar(name=f"c_{len_reqs-1}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS) for idx_p in range(len_V_P_S)] for idx_v in range(len_vservers)])
    b.append([[[[m.addVar(name=f"b_{len_reqs-1}_{idx_e}_{idx_l}_{pqi}_{s}", vtype=gp.GRB.CONTINUOUS) for s in range(S_MAX)] for pqi in range(len_L_pqi)] for idx_l in range(len_L)] for idx_e in range(len_vpaths)])
    
    # Auxiliary Variables
    a.append([[m.addVar(name=f"a_{len_reqs-1}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_p in range(len_V_P_S)] for idx_v in range(len_vpaths)])
    a_h.append([[m.addVar(name=f"a_h_{len_reqs-1}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_p in range(len_V_P_R)] for idx_v in range(len_vpaths)])
    o.append([[m.addVar(name=f"o_{len_reqs-1}_{idx_v}_{idx_e}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_e in range(len_E_P)] for idx_v in range(len_vpaths)])
    o_h.append([m.addVar(name=f"o_h_{len_reqs-1}_{idx_v}", vtype=gp.GRB.CONTINUOUS) for idx_v in range(len_vpaths)])
    o_h1.append([m.addVar(name=f"o_h1_{len_reqs-1}_{idx_v}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_v in range(len_vpaths)])
    o_h2.append([m.addVar(name=f"o_h2_{len_reqs-1}_{idx_p}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_p in range(len_V_P_S)])
    o_h3.append([m.addVar(name=f"o_h3_{len_reqs-1}_{idx_q}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_q in range(len_V_P_R)])
    o_h4.append([m.addVar(name=f"o_h4_{len_reqs-1}_{idx_l}", vtype=gp.GRB.CONTINUOUS, ub=1) for idx_l in range(len_L)])

    m.update()
    
    # Set parameters to improve performance
    m.setParam('Threads', 16)

    # variable_names = [v.varName for v in m.getVars()]
    
    ## Constraints
    ###################################### Node Mapping Constraints ######################################
    # Eq. 1
    for idx_v, v in enumerate(r_t.V_S):
        m.addConstr(
            gp.quicksum(x[len_reqs-1][idx_v][idx_p] for idx_p in range(len(V_P_S))) == 1,
            name=f"vserver_unique_mapping_{len_reqs-1}_{idx_v}"
        )

    # Eq. 2
    for idx_w, w in enumerate(r_t.V_R):
        m.addConstr(
            gp.quicksum(y[len_reqs-1][idx_w][idx_q][f][k]
                        for idx_q, q in enumerate(V_P_R)
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, w.K_REQ + 1)) == 1,
            name=f"ru_unique_mapping_{len_reqs-1}_{idx_w}"
        )

    # Eq. 3
    for idx_p, p in enumerate(V_P_S):
        if len_reqs >= 2:
            constraint_to_remove = m.getConstrByName(f"vserver_max_isolation_limit_{idx_p}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)

        m.addConstr(
            gp.quicksum(o_h2[idx_r][idx_p]
                        for idx_r, r in enumerate(reqs)
                        if r.gamma == 2) <= 1,
            name=f"vserver_max_isolation_limit_{idx_p}"
        )
        

    # Eq. 4
    for idx_q, q in enumerate(V_P_R):
        if len_reqs >= 2:
            constraint_to_remove = m.getConstrByName(f"ru_max_isolation_limit_{idx_q}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)
        
        m.addConstr(
            gp.quicksum(o_h3[idx_r][idx_q]
                        for idx_r, r in enumerate(reqs)
                        if r.gamma == 2) <= 1,
            name=f"ru_max_isolation_limit_{idx_q}"
        )

    # Eq. 5
    for idx_r, r in enumerate(reqs):
        for idx_v, v in enumerate(r.V_S):
            for idx_p, p in enumerate(V_P_S):
                if len_reqs >= 2:
                    constraint_to_remove = m.getConstrByName(f"vserver_regular_isolation_limit_{idx_r}_{idx_v}_{idx_p}")
                    if constraint_to_remove is not None:
                        m.remove(constraint_to_remove)
                    
                m.addConstr(
                    x[idx_r][idx_v][idx_p] <= 1 - gp.quicksum(
                        o_h2[idx_r1][idx_p]
                        for idx_r1, r1 in enumerate(reqs)
                        if r1.gamma == 2 and reqs.index(r1) != reqs.index(r)
                    ),
                    name=f"vserver_regular_isolation_limit_{idx_r}_{idx_v}_{idx_p}"
                    )

    # Eq. 6
    for idx_r, r in enumerate(reqs):
        for idx_w, w in enumerate(r.V_R):
            for idx_q, q in enumerate(V_P_R):
                if len_reqs >= 2:
                    constraint_to_remove = m.getConstrByName(f"ru_regular_isolation_limit_{idx_r}_{idx_w}_{idx_q}")
                    if constraint_to_remove is not None:
                        m.remove(constraint_to_remove)
                
                m.addConstr(
                    gp.quicksum(
                        y[idx_r][idx_w][idx_q][f][k]
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, w.K_REQ + 1)
                    ) <= 1 - gp.quicksum(
                        o_h3[idx_r1][idx_q]
                        for idx_r1, r1 in enumerate(reqs)
                        if r1.gamma == 2 and reqs.index(r1) != reqs.index(r)
                    ),
                    name=f"ru_regular_isolation_limit_{idx_r}_{idx_w}_{idx_q}"
                )

    # Eq. 7
    for idx_v, v in enumerate(r_t.V_S):
        for idx_p, p in enumerate(V_P_S):
            m.addConstr(
                delta * x[len_reqs-1][idx_v][idx_p] <= c[len_reqs-1][idx_v][idx_p],
                name=f"mips_limit_1_{len_reqs-1}_{idx_v}_{idx_p}"
            )
            m.addConstr(
                c[len_reqs-1][idx_v][idx_p] <= v.C_REQ * x[len_reqs-1][idx_v][idx_p],
                name=f"mips_limit_2_{len_reqs-1}_{idx_v}_{idx_p}"
            )

    # Eq. 8
    for idx_w, w in enumerate(r_t.V_R):
        for idx_q, q in enumerate(V_P_R):
            m.addConstr(
                gp.quicksum(
                    k * y[len_reqs-1][idx_w][idx_q][f][k]
                    for f in range(len(q.Pi_MAX))
                    for k in range(1, w.K_REQ + 1)
                ) <= w.K_REQ,
                name=f"radio_overprovision_{len_reqs-1}_{idx_w}_{idx_q}"
            )

    # Eq. 36 (Simplified Eq. 10)
    h_VM_0 = [gp.quicksum(x[idx_r][idx_v][idx_p]
                  for idx_r, r in enumerate(reqs)
                  if  (r.gamma == 0) and (r.kappa == 0)
                  for idx_v, v in enumerate(r.V_S)
                  for xi       in range(v.Xi_REQ)
                  if  v.Chi_REQ[xi] == (sys.CHI_MAX + 1)
                 ) / p.Xi_MAX[0] + gp.quicksum(u[idx_p][chi]
                                       for chi in range(sys.CHI_MAX)
                                      ) / p.Xi_MAX[0] + gp.quicksum(v.Xi_REQ * x[idx_r][idx_v][idx_p]
                                                            for idx_r, r in enumerate(reqs)
                                                            if (r.gamma == 0) and (r.kappa == 1)
                                                            for idx_v, v in enumerate(r.V_S)
                                                           ) / p.Xi_MAX[0] + 1 ## Plus 1 is the simplification of the ceiling function
              for idx_p, p in enumerate(V_P_S)
             ]

    # Eq. 37 (Simplified Eq. 9)
    for idx_p, p in enumerate(V_P_S):
        if len_reqs >= 2:
            constraint_to_remove = m.getConstrByName(f"mips_max_limit_{idx_p}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)
        
        m.addConstr(
            gp.quicksum(
                c[idx_r][idx_v][idx_p]
                for idx_r, r in enumerate(reqs)
                for idx_v, v in enumerate(r.V_S)
            ) + (sys.C_CON + sys.C_GOS) * h_VM_0[idx_p] + sys.C_HHO * u_h[idx_p] + sys.C_GOS * gp.quicksum(
                v.Xi_REQ * x[idx_r][idx_v][idx_p]
                for idx_r, r in enumerate(reqs)
                if r.gamma == 1
                for idx_v, v in enumerate(r.V_S)
            ) <= p.C_MAX,
            name=f"mips_max_limit_{idx_p}"
        )

    # Eq. 11
    for idx_p, p in enumerate(V_P_S):
        if len_reqs >= 2:
            constraint_to_remove = m.getConstrByName(f"instance_max_limit_{idx_p}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)
        
        m.addConstr(
            h_VM_0[idx_p] + gp.quicksum(
                v.Xi_REQ * x[idx_r][idx_v][idx_p]
                for idx_r, r in enumerate(reqs)
                if r.gamma == 1
                for idx_v, v in enumerate(r.V_S)
            ) <= p.Xi_MAX[1],
            name=f"instance_max_limit_{idx_p}"
        )

    # Eq. 50 (Simplified Eq. 12)
    for idx_q, q in enumerate(V_P_R):
        for f in range(len(q.Pi_MAX)):
            if len_reqs >= 2:
                constraint_to_remove = m.getConstrByName(f"radio_max_limit_{idx_q}_{f}")
                if constraint_to_remove is not None:
                    m.remove(constraint_to_remove)
            
            m.addConstr(
                sys.Pi_PRB * sys.N_FRM + gp.quicksum(
                    k * y[idx_r][idx_w][idx_q][f][k] * sys.Pi_PRB
                    for idx_r, r in enumerate(reqs)
                    if r.beta < 1e6
                    for idx_w, w in enumerate(r.V_R)
                    for k in range(1, w.K_REQ + 1)
                ) + gp.quicksum(
                    y[idx_r][idx_w][idx_q][f][k] * sys.Pi_FGB
                    for idx_r, r in enumerate(reqs)
                    if r.beta < 1e6 and r.gamma == 1
                    for idx_w, w in enumerate(r.V_R)
                    for k in range(1, w.K_REQ + 1)
                ) <= q.Pi_MAX[f],
                name=f"radio_max_limit_{idx_q}_{f}"
            )

    ###################################### Link Mapping Constraints ######################################

    # Eq. 13
    for idx_l, l in enumerate(L):
        if len_reqs >= 2:
            constraint_to_remove = m.getConstrByName(f"link_max_isolation_limit_{idx_l}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)
        
        m.addConstr(
            gp.quicksum(
                o_h4[idx_r][idx_l]
                for idx_r, r in enumerate(reqs)
                if r.gamma == 2
            ) <= 1,
            name=f"link_max_isolation_limit_{idx_l}"
        )

    # Eq. 14
    for idx_e, e in enumerate(r_t.E):
        for idx_l, l in enumerate(L):
            m.addConstr(
                gp.quicksum(
                    z[len_reqs-1][idx_e][idx_l][s]
                    for s in range(len(l.B_MAX))
                ) <= 1 - gp.quicksum(
                    o_h4[idx_r1][idx_l]
                    for idx_r1, r1 in enumerate(reqs)
                    if (r1.gamma == 2) and (reqs.index(r1) != reqs.index(r_t))
                ),
                name=f"link_regular_isolation_limit_{len_reqs-1}_{idx_e}_{idx_l}"
            )

    # Eq. 15
    for idx_e, e in enumerate(r_t.E):
        for idx_l, l in enumerate(L):
            for s in range(len(l.B_MAX)):
                m.addConstr(
                    epsilon * z[len_reqs-1][idx_e][idx_l][s] <= gp.quicksum(
                        b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s]
                        for idx_e_p, e_p in enumerate(E_P)
                        if l in L_pqi[idx_e_p]
                    ),
                    name=f"link_path_mapping_coordination_1_{len_reqs-1}_{idx_e}_{idx_l}_{s}"
                    )
    for idx_e, e in enumerate(r_t.E):
        for idx_l, l in enumerate(L):
            for s in range(len(l.B_MAX)):
                m.addConstr(
                    (1 - sys.Psi_HDR * (r_t.gamma == 0)) * gp.quicksum(
                        b[len_reqs-1][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s]
                        for idx_e_p, e_p in enumerate(E_P)
                        if l in L_pqi[idx_e_p]
                    ) <= e.B_REQ * z[len_reqs-1][idx_e][idx_l][s],
                    name=f"link_path_mapping_coordination_2_{len_reqs-1}_{idx_e}_{idx_l}_{s}"
                )

    # Eq. 16
    for idx_e, e in enumerate(r_t.E):
        for idx_e_p, e_p in enumerate(E_P):
            for idx_l_1, l_1 in enumerate(L_pqi[idx_e_p]):
                for idx_l_2, l_2 in enumerate(L_pqi[idx_e_p]):
                    if idx_l_1 != idx_l_2:
                        m.addConstr(
                            gp.quicksum(
                                b[len_reqs-1][idx_e][idx_e_p][idx_l_1][s]
                                for s in range(S_MAX)
                            ) == gp.quicksum(
                                b[len_reqs-1][idx_e][idx_e_p][idx_l_2][s]
                                for s in range(S_MAX)
                            ),
                            name=f"eq_constraint_{len_reqs-1}_{idx_e}_{idx_e_p}_{idx_l_1}_{idx_l_2}"
                        )

    # (Simplified Eq. 17)
    for idx_l, l in enumerate(L):
        for s in range(len(l.B_MAX)):
            if len_reqs >= 2:
                constraint_to_remove = m.getConstrByName(f"bandwidth_max_limit_{idx_l}_{s}")
                if constraint_to_remove is not None:
                    m.remove(constraint_to_remove)
            
            m.addConstr(
                gp.quicksum(
                    b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s] + 
                    z[idx_r][idx_e][idx_l][s] * (sys.B_WSC + sys.B_WGB)
                    for idx_r, r in enumerate(reqs)
                    if r.beta < 1e6 and r.gamma == 1
                    for idx_e, e in enumerate(r.E)
                    for idx_e_p, e_p in enumerate(E_P)
                    if l in L_pqi[idx_e_p]
                ) + gp.quicksum(
                    b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s]
                    for idx_r, r in enumerate(reqs)
                    if r.beta < 1e6 and (r.gamma == 0 or r.gamma == 2)
                    for idx_e, e in enumerate(r.E)
                    for idx_e_p, e_p in enumerate(E_P)
                    if l in L_pqi[idx_e_p]
                ) + sys.B_WSC <= l.B_MAX[s],
                name=f"bandwidth_max_limit_{idx_l}_{s}"
            )


    # Eq. 40 and Eq. 41 (Simplified Eq. 18 and Eq. 27)
    h_B_1 = [[1 - gp.quicksum(a[idx_r][idx_e][idx_p]
                      for idx_p, p in enumerate(V_P_S)
                     )
              for idx_e, e in enumerate(r.E)
             ]
             for idx_r, r in enumerate(reqs)
            ]
    h_B_2 = [[1 - gp.quicksum(a_h[idx_r][idx_e][idx_q]
                      for idx_q, q in enumerate(V_P_R)
                     )
              for idx_e, e in enumerate(r.E)
             ]
             for idx_r, r in enumerate(reqs)
            ]
    h_B_3 = 1
    h_D_3 = 0

    # Eq. 19
    h_B_h_1 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                                                     for idx_e_p, e_p in enumerate(E_P)
                                                     if (e_p.p in V_P_S) and (e_p.q in V_P_S)
                                                     for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                    ) + e.B_REQ*h_B_1[idx_r][idx_e]
                for idx_e, e in enumerate(r.E)
               ]
               for idx_r, r in enumerate(reqs)
              ]
    h_B_h_2 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                                                     for idx_e_p, e_p in enumerate(E_P)
                                                     if (e_p.p in V_P_R) and (e_p.q in V_P_R)
                                                     for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                    ) + e.B_REQ*h_B_2[idx_r][idx_e]
                for idx_e, e in enumerate(r.E)
               ]
               for idx_r, r in enumerate(reqs)
              ]
    h_B_h_3 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                                                     for idx_e_p, e_p in enumerate(E_P)
                                                     if (e_p.p in V_P_S) and (e_p.q in V_P_R)
                                                     for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                    ) + e.B_REQ
                for idx_e, e in enumerate(r.E)
                #if  (e.v in r.V_S) and (e.w in r.V_R)
               ]
               for idx_r, r in enumerate(reqs)
              ]

    # Eq.20
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_S:
            m.addConstr(
                h_B_h_1[len_reqs-1][idx_e] >= 0,
                name=f"bandwidth_overprovisioning_1_{len_reqs-1}_{idx_e}"
            )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_R and e.w in r_t.V_R:
            m.addConstr(
                h_B_h_2[len_reqs-1][idx_e] >= 0,
                name=f"bandwidth_overprovisioning_2_{len_reqs-1}_{idx_e}"
            )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_R:
            m.addConstr(
                h_B_h_3[len_reqs-1][idx_e] >= 0,
                name=f"bandwidth_overprovisioning_3_{len_reqs-1}_{idx_e}"
            )

    # Eq. 21
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S:
            for idx_p, p in enumerate(V_P_S):
                m.addConstr(
                    (1 - sys.Psi_HDR * (r_t.gamma == 0)) * gp.quicksum(
                        b[len_reqs-1][idx_e][idx_e_p][0][s]
                        for idx_e_p, e_p in enumerate(E_P)
                        if e_p.p in V_P_S and V_P_S.index(e_p.p) == idx_p
                        for s in range(S_MAX)
                    ) <= e.B_REQ * x[len_reqs-1][r_t.V_S.index(e.v)][idx_p],
                    name=f"node_path_mapping_coordination_1_{len_reqs-1}_{idx_e}_{idx_p}"
                )

    # Eq. 22
    for idx_e, e in enumerate(r_t.E):
        if e.w in r_t.V_R:
            for idx_q, q in enumerate(V_P_R):
                m.addConstr(
                    (1 - sys.Psi_HDR * (r_t.gamma == 0)) * gp.quicksum(
                        b[len_reqs-1][idx_e][idx_e_p][0][s]
                        for idx_e_p, e_p in enumerate(E_P)
                        if e_p.q in V_P_R and V_P_R.index(e_p.q) == idx_q
                        for s in range(S_MAX)
                    ) <= e.B_REQ * gp.quicksum(
                        y[len_reqs-1][r_t.V_R.index(e.w)][idx_q][f][k]
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, K_MAX)
                    ),
                    name=f"node_path_mapping_coordination_2_{len_reqs-1}_{idx_e}_{idx_q}"
                )

    # Eq. 38
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_S:
            for idx_p, p in enumerate(V_P_S):
                m.addConstr(
                    a[len_reqs-1][idx_e][idx_p] <= x[len_reqs-1][r.V_S.index(e.v)][idx_p],
                    name=f"auxiliary_constraints_1_1_{len_reqs-1}_{idx_e}_{idx_p}"
                )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_S:
            for idx_p, p in enumerate(V_P_S):
                m.addConstr(
                    a[len_reqs-1][idx_e][idx_p] <= x[len_reqs-1][r_t.V_S.index(e.w)][idx_p],
                    name=f"auxiliary_constraints_1_2_{len_reqs-1}_{idx_e}_{idx_p}"
                )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_S:
            for idx_p, p in enumerate(V_P_S):
                m.addConstr(
                    a[len_reqs-1][idx_e][idx_p] >= x[len_reqs-1][r_t.V_S.index(e.v)][idx_p] + x[len_reqs-1][r_t.V_S.index(e.w)][idx_p] - 1,
                    name=f"auxiliary_constraints_1_3_{len_reqs-1}_{idx_e}_{idx_p}"
                )

    # Eq. 39
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_R and e.w in r_t.V_R:
            for idx_q, q in enumerate(V_P_R):
                m.addConstr(
                    a_h[len_reqs-1][idx_e][idx_q] <= gp.quicksum(
                        y[len_reqs-1][r_t.V_R.index(e.v)][idx_q][f][k]
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, w.K_REQ + 1)
                    ),
                    name=f"auxiliary_constraints_2_1_{len_reqs-1}_{idx_e}_{idx_q}"
                )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_R and e.w in r_t.V_R:
            for idx_q, q in enumerate(V_P_R):
                m.addConstr(
                    a_h[len_reqs-1][idx_e][idx_q] <= gp.quicksum(
                        y[idx_r][r_t.V_R.index(e.w)][idx_q][f][k]
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, w.K_REQ + 1)
                    ),
                    name=f"auxiliary_constraints_2_2_{len_reqs-1}_{idx_e}_{idx_q}"
                )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_R and e.w in r_t.V_R:
            for idx_q, q in enumerate(V_P_R):
                m.addConstr(
                    a_h[len_reqs-1][idx_e][idx_q] >= gp.quicksum(
                        y[len_reqs-1][r_t.V_R.index(e.v)][idx_q][f][k]
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, w.K_REQ + 1)
                    ) + gp.quicksum(
                        y[len_reqs-1][r_t.V_R.index(e.w)][idx_q][f][k]
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, w.K_REQ + 1)
                    ) - 1,
                    name=f"auxiliary_constraints_2_3_{len_reqs-1}_{idx_e}_{idx_q}"
                )

    # Eq. 43
    for idx_e, e in enumerate(r_t.E):
        for idx_e_p, e_p in enumerate(E_P):
            for idx_l, l in enumerate(L_pqi[idx_e_p]):
                m.addConstr(
                    o[len_reqs-1][idx_e][idx_e_p] <= gp.quicksum(
                        z[len_reqs-1][idx_e][L.index(l)][s]
                        for s in range(len(l.B_MAX))
                    ),
                    name=f"auxiliary_constraints_3_1_{len_reqs-1}_{idx_e}_{idx_e_p}_{idx_l}"
                )
    for idx_e, e in enumerate(r_t.E):
        for idx_e_p, e_p in enumerate(E_P):
            m.addConstr(
                o[len_reqs-1][idx_e][idx_e_p] >= gp.quicksum(
                    z[len_reqs-1][idx_e][L.index(l)][s]
                    for idx_l, l in enumerate(L_pqi[idx_e_p])
                    for s in range(len(l.B_MAX))
                ) - (len(L) - 1),
                name=f"auxiliary_constraints_3_2_{len_reqs-1}_{idx_e}_{idx_e_p}"
            )

    # Eq. 44
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_S:
            for idx_e_p, e_p in enumerate(E_P):
                m.addConstr(
                    o_h[len_reqs-1][idx_e] >= e_p.D_RTT * o[len_reqs-1][idx_e][idx_e_p] - e.D_REQ - M * (1 - h_B_1[len_reqs-1][idx_e]),
                    name=f"auxiliary_constraints_6_1_{len_reqs-1}_{idx_e}_{idx_e_p}"
                )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_R and e.w in r_t.V_R:
            for idx_e_p, e_p in enumerate(E_P):
                m.addConstr(
                    o_h[len_reqs-1][idx_e] >= e_p.D_RTT * o[len_reqs-1][idx_e][idx_e_p] - e.D_REQ - M * (1 - h_B_2[len_reqs-1][idx_e]),
                    name=f"auxiliary_constraints_6_2_{len_reqs-1}_{idx_e}_{idx_e_p}"
                )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_R:
            for idx_e_p, e_p in enumerate(E_P):
                m.addConstr(
                    o_h[len_reqs-1][idx_e] >= e_p.D_RTT * o[len_reqs-1][idx_e][idx_e_p] - e.D_REQ,
                    name=f"auxiliary_constraints_6_3_{len_reqs-1}_{idx_e}_{idx_e_p}"
                )

    # Eq. 45
    for idx_e, e in enumerate(r_t.E):
        m.addConstr(
            o_h[len_reqs-1][idx_e] >= 0,
            name=f"auxiliary_constraints_7_{len_reqs-1}_{idx_e}"
        )

    for idx_e, e in enumerate(r_t.E):
        m.addConstr(
            o_h[len_reqs-1][idx_e] <= N * o_h1[len_reqs-1][idx_e],
            name=f"auxiliary_constraints_8_1_{len_reqs-1}_{idx_e}"
        )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_S:
            for idx_e_p, e_p in enumerate(E_P):
                m.addConstr(
                    o_h[len_reqs-1][idx_e] <= e_p.D_RTT * o[len_reqs-1][idx_e][idx_e_p] - e.D_REQ - M * (1 - h_B_1[len_reqs-1][idx_e]) + N * (1 - o_h1[len_reqs-1][idx_e]),
                    name=f"auxiliary_constraints_8_2_{len_reqs-1}_{idx_e}_{idx_e_p}"
                )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_R and e.w in r_t.V_R:
            for idx_e_p, e_p in enumerate(E_P):
                m.addConstr(
                    o_h[len_reqs-1][idx_e] <= e_p.D_RTT * o[len_reqs-1][idx_e][idx_e_p] - e.D_REQ - M * (1 - h_B_2[len_reqs-1][idx_e]) + N * (1 - o_h1[len_reqs-1][idx_e]),
                    name=f"auxiliary_constraints_8_3_{len_reqs-1}_{idx_e}_{idx_e_p}"
                )
    for idx_e, e in enumerate(r_t.E):
        if e.v in r_t.V_S and e.w in r_t.V_R:
            for idx_e_p, e_p in enumerate(E_P):
                m.addConstr(
                    o_h[len_reqs-1][idx_e] <= e_p.D_RTT * o[len_reqs-1][idx_e][idx_e_p] - e.D_REQ + N * (1 - o_h1[len_reqs-1][idx_e]),
                    name=f"auxiliary_constraints_8_4_{len_reqs-1}_{idx_e}_{idx_e_p}"
                )

    if r_t.gamma <= 1:
        for idx_p, p in enumerate(V_P_S):
            for idx_v, v in enumerate(r_t.V_S):
                m.addConstr(
                    u_h[idx_p] >= x[len_reqs-1][idx_v][idx_p],
                    name=f"auxiliary_constraints_8_1_{len_reqs-1}_{idx_v}_{idx_p}"
                )
    for idx_p, p in enumerate(V_P_S):
        if len_reqs >= 2:
            constraint_to_remove = m.getConstrByName(f"auxiliary_constraints_8_2_{idx_p}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)
        
        m.addConstr(
            u_h[idx_p] <= gp.quicksum(
                x[idx_r][idx_v][idx_p]
                for idx_r, r in enumerate(reqs)
                if r.gamma <= 1
                for idx_v, v in enumerate(r.V_S)
            ),
            name=f"auxiliary_constraints_8_2_{idx_p}"
        )

    if r_t.gamma == 0 and r_t.kappa == 0:
        for idx_p, p in enumerate(V_P_S):
            for chi in range(sys.CHI_MAX + 1):
                for idx_v, v in enumerate(r.V_S):
                    for xi in range(v.Xi_REQ):
                        m.addConstr(
                            u[idx_p][chi] >= (v.Chi_REQ[xi] == chi) * x[len_reqs-1][idx_v][idx_p],
                            name=f"auxiliary_constraints_9_1_{idx_p}_{chi}_{len_reqs-1}_{idx_v}_{xi}"
                        )
                            
    for idx_r, r in enumerate(reqs):
        if r.gamma == 0 and r.kappa == 0:
            for idx_v, v in enumerate(r.V_S):
                for idx_p, p in enumerate(V_P_S):
                    for chi in range(sys.CHI_MAX + 1):
                        for xi in range(v.Xi_REQ):
                            if len_reqs >= 2:
                                constraint_to_remove = m.getConstrByName(f"auxiliary_constraints_9_2_{idx_p}_{chi}_{idx_r}_{idx_v}_{xi}")
                                if constraint_to_remove is not None:
                                    m.remove(constraint_to_remove)
                            
                            m.addConstr(
                                u[idx_p][chi] <= gp.quicksum(
                                    (v.Chi_REQ[xi] == chi) * x[idx_r][idx_v][idx_p]
                                    for idx_r, r in enumerate(reqs)
                                    if r.gamma == 0 and r.kappa == 0
                                    for idx_v, v in enumerate(r.V_S)
                                    for xi in range(v.Xi_REQ)
                                ),
                                name=f"auxiliary_constraints_9_2_{idx_p}_{chi}_{idx_r}_{idx_v}_{xi}"
                            )
    
    if r_t.gamma == 2:
        for idx_v, v in enumerate(r_t.V_S):
            for idx_p, p in enumerate(V_P_S):
                m.addConstr(
                    o_h2[idx_r][idx_p] >= x[len_reqs-1][idx_v][idx_p],
                    name=f"auxiliary_constraints_9_1_{len_reqs-1}_{idx_p}_{idx_v}"
                )
    for idx_r, r in enumerate(reqs):
        if r.gamma == 2:
            for idx_p, p in enumerate(V_P_S):
                if len_reqs >= 2:
                    constraint_to_remove = m.getConstrByName(f"auxiliary_constraints_9_2_{idx_r}_{idx_p}")
                    if constraint_to_remove is not None:
                        m.remove(constraint_to_remove)
                
                m.addConstr(
                    o_h2[idx_r][idx_p] <= gp.quicksum(
                        x[idx_r][idx_v][idx_p]
                        for idx_v, v in enumerate(r.V_S)
                    ),
                    name=f"auxiliary_constraints_9_2_{idx_r}_{idx_p}"
                )

    if r_t.gamma == 2:
        for idx_w, w in enumerate(r_t.V_R):
            for idx_q, q in enumerate(V_P_R):
                for f in range(len(q.Pi_MAX)):
                    for k in range(1, w.K_REQ + 1):
                        m.addConstr(
                            o_h3[len_reqs-1][idx_q] >= y[len_reqs-1][idx_w][idx_q][f][k],
                            name=f"auxiliary_constraints_10_1_{len_reqs-1}_{idx_q}_{idx_w}_{f}_{k}"
                        )
    for idx_r, r in enumerate(reqs):
        if r.gamma == 2:
            for idx_q, q in enumerate(V_P_R):
                if len_reqs >= 2:
                    constraint_to_remove = m.getConstrByName(f"auxiliary_constraints_10_2_{idx_r}_{idx_q}")
                    if constraint_to_remove is not None:
                        m.remove(constraint_to_remove)
                
                m.addConstr(
                    o_h3[idx_r][idx_q] <= gp.quicksum(
                        y[idx_r][idx_w][idx_q][f][k]
                        for idx_w, w in enumerate(r.V_R)
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, w.K_REQ + 1)
                    ),
                    name=f"auxiliary_constraints_10_2_{idx_r}_{idx_q}"
                )
    
    if r_t.gamma == 2:
        for idx_e, e in enumerate(r_t.E):
            for idx_l, l in enumerate(L):
                for s in range(S_MAX):
                    m.addConstr(
                        o_h4[len_reqs-1][idx_l] >= z[len_reqs-1][idx_e][idx_l][s],
                        name=f"auxiliary_constraints_11_1_{len_reqs-1}_{idx_l}_{idx_e}_{s}"
                    )
    for idx_r, r in enumerate(reqs):
        if r.gamma == 2:
            for idx_l, l in enumerate(L):
                if len_reqs >= 2:
                    constraint_to_remove = m.getConstrByName(f"auxiliary_constraints_11_2_{idx_r}_{idx_l}")
                    if constraint_to_remove is not None:
                        m.remove(constraint_to_remove)
                
                m.addConstr(
                    o_h4[idx_r][idx_l] <= gp.quicksum(
                        z[idx_r][idx_e][idx_l][s]
                        for idx_e, e in enumerate(r.E)
                        for s in range(S_MAX)
                    ),
                    name=f"auxiliary_constraints_11_2_{idx_r}_{idx_l}"
                )

    ###################################### Profit Constraints ######################################

    # Eq. 23
    g_dep = gp.quicksum(b[idx_r][idx_e][idx_e_p][idx_l][s] * r.Theta[idx_e_p]
                for idx_r, r     in enumerate(reqs)
                for idx_e, e     in enumerate(r.E)
                for idx_e_p, e_p in enumerate(E_P)
                for idx_l, l     in enumerate(L_pqi[idx_e_p])
                for s            in range(len(l.B_MAX))
               ) + gp.quicksum(c[idx_r][idx_v][idx_p] * r.Omega[idx_p]
                       for idx_r, r in enumerate(reqs)
                       for idx_v, v in enumerate(r.V_S)
                       for idx_p, p in enumerate(V_P_S)
                      ) + gp.quicksum(k * y[idx_r][idx_w][idx_q][f][k] * r.Phi[idx_q]
                              for idx_r, r in enumerate(reqs)
                              for idx_w, w in enumerate(r.V_R)
                              for idx_q, q in enumerate(V_P_R)
                              for f in range(len(q.Pi_MAX))
                              for k in range(w.K_REQ + 1)
                             )

    # Eq. 24
    g_C = gp.quicksum(r.rho_C * v.C_REQ - r.rho_C * gp.quicksum(c[idx_r][idx_v][idx_p]
                                                for idx_p, p in enumerate(V_P_S)
                                               )
              for idx_r, r in enumerate(reqs)
              for idx_v, v in enumerate(r.V_S)
             )

    # Eq. 25
    g_K = gp.quicksum((r.rho_K * w.K_REQ) - (r.rho_K * gp.quicksum(k*y[idx_r][idx_w][idx_q][f][k]
                                                   for idx_q, q in enumerate(V_P_R)
                                                   for f in range(len(q.Pi_MAX))
                                                   for k in range(w.K_REQ + 1)
                                                  ))
              for idx_r, r in enumerate(reqs)
              for idx_w, w in enumerate(r.V_R)
             )

    # Eq. 26
    g_B_1 = gp.quicksum(r.rho_B * h_B_h_1[idx_r][idx_e]
                for idx_r, r in enumerate(reqs)
                for idx_e, e in enumerate(r.E)
                if (e.v in r.V_S) and (e.w in r.V_S)
               )
    g_B_2 = gp.quicksum(r.rho_B * h_B_h_2[idx_r][idx_e]
                for idx_r, r in enumerate(reqs)
                for idx_e, e in enumerate(r.E)
                if (e.v in r.V_R) and (e.w in r.V_R)
               )
    g_B_3 = gp.quicksum(r.rho_B * h_B_h_3[idx_r][idx_e]
                for idx_r, r in enumerate(reqs)
                for idx_e, e in enumerate(r.E)
                if (e.v in r.V_S) and (e.w in r.V_R)
               )

    # Eq. 29
    g_D = gp.quicksum(
              r.rho_D * o_h[idx_r][idx_e]
              for idx_r, r in enumerate(reqs)
              for idx_e, e in enumerate(r.E)
             )

    # Eq. 30
    g_vio = g_D + g_C + g_K + g_B_1 + g_B_2 + g_B_3

    # Eq. 31
    g_mig = gp.quicksum(gp.quicksum(r.beta * x[idx_r][idx_v][idx_p]
                    for idx_p, p in enumerate(V_P_S)
                    if(len(X_t))
                    if(X_t[idx_r][idx_v][idx_p] == 0)
                   )
                for idx_r, r in enumerate(reqs_lp_t)
                for idx_v, v in enumerate(r.V_S)
               ) + gp.quicksum(gp.quicksum(r.beta * gp.quicksum(y[idx_r][idx_w][idx_q][f][k]
                                        for f in range(len(q.Pi_MAX))
                                        for k in range(1, w.K_REQ + 1)
                                       )
                           for idx_q, q in enumerate(V_P_R)
                           if(len(Y_t))
                           if(sum(Y_t[idx_r][idx_w][idx_q][f][k]
                                  for f in range(len(q.Pi_MAX))
                                  for k in range(1, w.K_REQ + 1)
                                 ) == 0)
                          )
                       for idx_r, r in enumerate(reqs_lp_t)
                       for idx_w, w in enumerate(r.V_R)
                      )

    if len_reqs >= 2:
        constraint_to_remove = m.getConstrByName(f"minimum_profit")
        if constraint_to_remove is not None:
            m.remove(constraint_to_remove)
    if t >= 1:
        # Eq. 32
        m.addConstr(
            (
                (sum(r.R for r in reqs) - g_dep - g_vio - g_mig - profit_in) >= P_min
            ), name="minimum_profit"
        )
    else:
        m.addConstr(
            (
                sum(r.R for r in reqs) - g_dep - g_vio - g_mig >= P_min
            ), name="minimum_profit"
        )

    m.update()
    
    m.setObjective(sum(r.R for r in reqs) - g_dep - g_vio - g_mig, GRB.MAXIMIZE)

    # Start the timer
    start_time = time.time()
    
    timeout = 0
    try:
        m = run_with_timeout(r_t.timeout, timeout_optimize, m)
        print(f"Result: {m}")
    except TimeoutException as e:
        print(e)
        timeout = 1
    
    # Stop the timer
    end_time = time.time()
    timer = end_time - start_time

    status = m.status

    # Determine feasibility based on the status
    if (status == gp.GRB.OPTIMAL) and (timeout == 0):
        print("Optimal solution found.")

        # Get the optimal values of variables
        vars_opt = {var.varName: var.x for var in m.getVars()}

        x_opt_lp = [[[vars_opt["x_{}_{}_{}".format(idx_r,idx_v,idx_p)] for idx_p, p in enumerate(V_P_S)] for idx_v, v in enumerate(r.V_S)] for idx_r,r in enumerate(reqs)]
        x_opt    = [[[0 for idx_p, p in enumerate(V_P_S)] for idx_v, v in enumerate(r.V_S)] for idx_r,r in enumerate(reqs)]

        c_opt_lp = [[[vars_opt["c_{}_{}_{}".format(idx_r,idx_v,idx_p)] for idx_p, p in enumerate(V_P_S)] for idx_v, v in enumerate(r.V_S)] for idx_r,r in enumerate(reqs)]
        c_opt    = [[[0 for idx_p, p in enumerate(V_P_S)] for idx_v, v in enumerate(r.V_S)] for idx_r,r in enumerate(reqs)]

        for idx_r,r in enumerate(reqs):
            for idx_v, v in enumerate(r.V_S):
                idx_p_sel = random.choices(range(len(x_opt_lp[idx_r][idx_v])), weights=x_opt_lp[idx_r][idx_v], k=1)[0]
                x_opt[idx_r][idx_v][idx_p_sel] = 1
                c_opt[idx_r][idx_v][idx_p_sel] = c_opt_lp[idx_r][idx_v][idx_p_sel]/x_opt_lp[idx_r][idx_v][idx_p_sel]

        y_opt_lp = [[[[[vars_opt["y_{}_{}_{}_{}_{}".format(idx_r,idx_w,idx_q,f,k)] for k in range(K_MAX)] for f in range(F_MAX)] for idx_q, q in enumerate(V_P_R)] for idx_w, w in enumerate(r.V_R)] for idx_r,r in enumerate(reqs)]
        y_opt    = [[[[[0 for k in range(K_MAX)] for f in range(F_MAX)] for idx_q, q in enumerate(V_P_R)] for idx_w, w in enumerate(r.V_R)] for idx_r,r in enumerate(reqs)]

        for idx_r,r in enumerate(reqs):
            for idx_w, w in enumerate(r.V_R):
                list_tmp = [item for sublist1 in y_opt_lp[idx_r][idx_w] for sublist2 in sublist1 for item in sublist2]
                qfk_sel  = random.choices(range(len(list_tmp)), weights=list_tmp, k=1)[0]
                q_sel    = int(qfk_sel/K_MAX//F_MAX)
                fk_sel   = int(qfk_sel - q_sel*K_MAX*F_MAX)
                f_sel    = int(fk_sel//K_MAX)
                k_sel    = w.K_REQ if r.beta >= 1e6 else fk_sel - int(f_sel*K_MAX)
                y_opt[idx_r][idx_w][q_sel][f_sel][k_sel] = 1 

        z_opt_lp = [[[[vars_opt["z_{}_{}_{}_{}".format(idx_r,idx_e,idx_l,s)] for s in range(S_MAX)] for idx_l, l in enumerate(L)] for idx_e, e in enumerate(r.E)] for idx_r, r in enumerate(reqs)]
        z_opt    = [[[[0 for s in range(S_MAX)] for l in L] for idx_e, e in enumerate(r.E)] for idx_r, r in enumerate(reqs)]

        b_opt_lp = [[[[[vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,idx_l,s)] for s in range(S_MAX)] for idx_l,l in enumerate(L_pqi[idx_e_p])] for idx_e_p, e_p in enumerate(E_P)] for idx_e, e in enumerate(r.E)] for idx_r,r in enumerate(reqs)]
        b_opt    = [[[[[0 for s in range(S_MAX)] for idx_l, l in enumerate(L_pqi[idx_e_p])] for idx_e_p, e_p in enumerate(E_P)] for idx_e, e in enumerate(r.E)] for idx_r,r in enumerate(reqs)]

        for idx_r,r in enumerate(reqs):
            for idx_e, e in enumerate(r.E):
                list_tmp = [item for sublist1 in z_opt_lp[idx_r][idx_e] for item in sublist1]
                if any(num != 0 for num in list_tmp):
                    ls_sel   = random.choices(range(len(list_tmp)), weights=list_tmp, k=1)[0]
                    l_sel    = int(ls_sel//S_MAX)
                    s_sel    = int(ls_sel - l_sel*S_MAX)
                    z_opt[idx_r][idx_e][l_sel][s_sel] = 1

        for idx_r,r in enumerate(reqs):
            for idx_e, e in enumerate(r.E):
                for idx_e_p, e_p in enumerate(E_P):
                    for idx_l, l in enumerate(L_pqi[idx_e_p]):
                        for s in range(S_MAX):
                            if z_opt[idx_r][idx_e][L.index(l)][s] == 1:
                                b_opt[idx_r][idx_e][idx_e_p][idx_l][s] = b_opt_lp[idx_r][idx_e][idx_e_p][idx_l][s]/z_opt_lp[idx_r][idx_e][L.index(l)][s]


        a_opt_lp = [[[vars_opt["a_{}_{}_{}".format(idx_r,idx_e,idx_p)] for idx_p, p in enumerate(V_P_S)] for idx_e, e in enumerate(r.E)] for idx_r,r in enumerate(reqs)]
        a_opt    = [[[0 for idx_p, p in enumerate(V_P_S)] for idx_e, e in enumerate(r.E)] for idx_r,r in enumerate(reqs)]
        for idx_r,r in enumerate(reqs):
            for idx_e, e in enumerate(r.E):
                for idx_p, p in enumerate(V_P_S):
                    a_opt[idx_r][idx_e][idx_p] = (random.random() < a_opt_lp[idx_r][idx_e][idx_p])
                        
        a_h_opt_lp = [[[vars_opt["a_h_{}_{}_{}".format(idx_r,idx_e,idx_q)] for idx_q, q in enumerate(V_P_R)] for idx_e, e in enumerate(r.E)] for idx_r,r in enumerate(reqs)]
        a_h_opt    = [[[0 for idx_q, q in enumerate(V_P_R)] for idx_e, e in enumerate(r.E)] for idx_r,r in enumerate(reqs)]
        for idx_r,r in enumerate(reqs):
            for idx_e, e in enumerate(r.E):
                for idx_q, q in enumerate(V_P_R):
                    a_h_opt[idx_r][idx_e][idx_q] = (random.random() <= a_h_opt_lp[idx_r][idx_e][idx_q])

        if timeout == 0:
            g_dep_opt = sum(b_opt[idx_r][idx_e][idx_e_p][idx_l][s] * r.Theta[idx_e_p]
                         for idx_r, r     in enumerate(reqs)
                         for idx_e, e     in enumerate(r.E)
                         for idx_e_p, e_p in enumerate(E_P)
                         for idx_l, l     in enumerate(L_pqi[idx_e_p])
                         for s            in range(len(l.B_MAX))
                        ) + sum(c_opt[idx_r][idx_v][idx_p] * r.Omega[idx_p]
                                for idx_r, r in enumerate(reqs)
                                for idx_v, v in enumerate(r.V_S)
                                for idx_p, p in enumerate(V_P_S)
                               ) + sum(k * y_opt[idx_r][idx_w][idx_q][f][k] * r.Phi[idx_q]
                                       for idx_r, r in enumerate(reqs)
                                       for idx_w, w in enumerate(r.V_R)
                                       for idx_q, q in enumerate(V_P_R)
                                       for f in range(len(q.Pi_MAX))
                                       for k in range(w.K_REQ + 1)
                                      )
            g_D_opt = sum(
                          r.rho_D * vars_opt["o_h_{}_{}".format(idx_r,idx_e)]
                          for idx_r, r in enumerate(reqs)
                          for idx_e, e in enumerate(r.E)
                         )
            g_C_opt = sum(r.rho_C * v.C_REQ - r.rho_C * sum(c_opt[idx_r][idx_v][idx_p]
                                                            for idx_p, p in enumerate(V_P_S)
                                                           )
                      for idx_r, r in enumerate(reqs)
                      for idx_v, v in enumerate(r.V_S)
                     )
            g_K_opt = max((r.rho_K * w.K_REQ) - (r.rho_K * sum(k*y_opt[idx_r][idx_w][idx_q][f][k]
                                                               for idx_q, q in enumerate(V_P_R)
                                                               for f in range(len(q.Pi_MAX))
                                                               for k in range(w.K_REQ + 1)
                                                              ))
                      for idx_r, r in enumerate(reqs)
                      for idx_w, w in enumerate(r.V_R)
                     )


            h_B_1 = [[1 - sum(a_opt[idx_r][idx_e][idx_p]
                              for idx_p, p in enumerate(V_P_S)
                             )
                      for idx_e, e in enumerate(r.E)
                     ]
                     for idx_r, r in enumerate(reqs)
                    ]
            h_B_2 = [[1 - sum(a_h_opt[idx_r][idx_e][idx_q]
                              for idx_q, q in enumerate(V_P_R)
                             )
                      for idx_e, e in enumerate(r.E)
                     ]
                     for idx_r, r in enumerate(reqs)
                    ]
            h_B_3 = 1
            h_D_3 = 0

            h_B_h_1 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(b_opt[idx_r][idx_e][idx_e_p][0][s]
                                                             for idx_e_p, e_p in enumerate(E_P)
                                                             if  (e_p.p in V_P_S) and (e_p.q in V_P_S)
                                                             for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                            ) + e.B_REQ*h_B_1[idx_r][idx_e]
                        for idx_e, e in enumerate(r.E)
                       ]
                       for idx_r, r in enumerate(reqs)
                      ]
            h_B_h_2 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(b_opt[idx_r][idx_e][idx_e_p][0][s]
                                                             for idx_e_p, e_p in enumerate(E_P)
                                                             if  (e_p.p in V_P_R) and (e_p.q in V_P_R)
                                                             for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                            ) + e.B_REQ*h_B_2[idx_r][idx_e]
                        for idx_e, e in enumerate(r.E)
                       ]
                       for idx_r, r in enumerate(reqs)
                      ]
            h_B_h_3 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(b_opt[idx_r][idx_e][idx_e_p][0][s]
                                                             for idx_e_p, e_p in enumerate(E_P)
                                                             if  (e_p.p in V_P_S) and (e_p.q in V_P_R)
                                                             for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                            ) + e.B_REQ
                        for idx_e, e in enumerate(r.E)
                       ]
                       for idx_r, r in enumerate(reqs)
                      ]
            g_B_1_opt = sum(r.rho_B * max(h_B_h_1[idx_r][idx_e], 0)
                            for idx_r, r in enumerate(reqs)
                            for idx_e, e in enumerate(r.E)
                            if (e.v in r.V_S) and (e.w in r.V_S)
                           )

            g_B_2_opt = sum(r.rho_B * max(h_B_h_2[idx_r][idx_e], 0)
                            for idx_r, r in enumerate(reqs)
                            for idx_e, e in enumerate(r.E)
                            if (e.v in r.V_R) and (e.w in r.V_R)
                           )
            g_B_3_opt = sum(r.rho_B * max(h_B_h_3[idx_r][idx_e], 0)
                            for idx_r, r in enumerate(reqs)
                            for idx_e, e in enumerate(r.E)
                            if (e.v in r.V_S) and (e.w in r.V_R)
                           )
            g_vio_opt = g_D_opt + g_C_opt + g_K_opt + g_B_1_opt + g_B_2_opt + g_B_3_opt

            g_mig_opt = sum(sum(r.beta * x_opt[idx_r][idx_v][idx_p]
                                for idx_p, p in enumerate(V_P_S)
                                if(len(X_t))
                                if(X_t[idx_r][idx_v][idx_p] == 0)
                               )
                            for idx_r, r in enumerate(reqs_lp_t)
                            for idx_v, v in enumerate(r.V_S)
                           ) + sum(sum(r.beta * sum(y_opt[idx_r][idx_w][idx_q][f][k]
                                                    for f in range(len(q.Pi_MAX))
                                                    for k in range(1, w.K_REQ + 1)
                                                   )
                                       for idx_q, q in enumerate(V_P_R)
                                       if(len(Y_t))
                                       if(sum(Y_t[idx_r][idx_w][idx_q][f][k]
                                              for f in range(len(q.Pi_MAX))
                                              for k in range(1, w.K_REQ + 1)
                                             ) == 0)
                                      )
                                   for idx_r, r in enumerate(reqs_lp_t)
                                   for idx_w, w in enumerate(r.V_R)
                                  )

            n_mig_opt = sum(sum(x_opt[idx_r][idx_v][idx_p]
                            for idx_p, p in enumerate(V_P_S)
                            if(len(X_t))
                            if(X_t[idx_r][idx_v][idx_p] == 0)
                           )
                        for idx_r, r in enumerate(reqs_lp_t)
                        for idx_v, v in enumerate(r.V_S)
                       ) + sum(sum(sum(y_opt[idx_r][idx_w][idx_q][f][k]
                                                for f in range(len(q.Pi_MAX))
                                                for k in range(1, w.K_REQ + 1)
                                               )
                                   for idx_q, q in enumerate(V_P_R)
                                   if(len(Y_t))
                                   if(sum(Y_t[idx_r][idx_w][idx_q][f][k]
                                          for f in range(len(q.Pi_MAX))
                                          for k in range(1, w.K_REQ + 1)
                                         ) == 0)
                                  )
                               for idx_r, r in enumerate(reqs_lp_t)
                               for idx_w, w in enumerate(r.V_R)
                              )

            profit = sum(r.R for r in reqs) - g_dep_opt - g_vio_opt - g_mig_opt
            print("Delay, Radio, MIPS, and Bandwidth Violation Costs:")
            print(g_D_opt, g_K_opt, g_C_opt, g_B_1_opt, g_B_2_opt, g_B_3_opt)
            print("Deployment, Violation, and Migration Costs:")
            print(g_dep_opt, g_vio_opt, g_mig_opt)
            print("Profit:")
            print(profit)

            if t >= 1:
                h_VM_0 = [sum(x_opt[idx_r][idx_v][idx_p]
                            for idx_r, r in enumerate(reqs)
                            if  (r.gamma == 0) and (r.kappa == 0)
                            for idx_v, v in enumerate(r.V_S)
                            for xi       in range(v.Xi_REQ)
                            if  v.Chi_REQ[xi] == (sys.CHI_MAX + 1)
                            ) / p.Xi_MAX[0] + sum((random.random() <= vars_opt["u_{}_{}".format(idx_p,chi)])
                                               for chi in range(sys.CHI_MAX)
                                              ) / p.Xi_MAX[0] + sum(v.Xi_REQ * x_opt[idx_r][idx_v][idx_p]
                                                                    for idx_r, r in enumerate(reqs)
                                                                    if (r.gamma == 0) and (r.kappa == 1)
                                                                    for idx_v, v in enumerate(r.V_S)
                                                                   ) / p.Xi_MAX[0] + 1 ## Plus 1 is the simplification of the ceiling function
                            for idx_p, p in enumerate(V_P_S)
                         ]
                
                cond_1 = sum(c_opt[idx_r][idx_v][idx_p]
                                for idx_r, r in enumerate(reqs)
                                for idx_v, v in enumerate(r.V_S)
                            ) + (sys.C_CON + sys.C_GOS) * h_VM_0[idx_p] + sys.C_HHO * (random.random() <= vars_opt["u_h_{}".format(idx_p)]) + sys.C_GOS * sum(
                                v.Xi_REQ * x_opt[idx_r][idx_v][idx_p]
                                for idx_r, r in enumerate(reqs)
                                if r.gamma == 1
                                for idx_v, v in enumerate(r.V_S)
                            ) <= p.C_MAX

                cond_1 = all((sum(c_opt[idx_r][idx_v][idx_p]
                                    for idx_r, r in enumerate(reqs)
                                    for idx_v, v in enumerate(r.V_S)
                                ) + (sys.C_CON + sys.C_GOS) * h_VM_0[idx_p] + sys.C_HHO * (random.random() <= vars_opt["u_h_{}".format(idx_p)]) + sys.C_GOS * sum(
                                    v.Xi_REQ * x_opt[idx_r][idx_v][idx_p]
                                    for idx_r, r in enumerate(reqs)
                                    if r.gamma == 1
                                    for idx_v, v in enumerate(r.V_S)
                                )
                            ) <= p.C_MAX
                            for idx_p, p in enumerate(V_P_S)
                        )
                cond_2 = all((sys.Pi_PRB * sys.N_FRM + sum(
                                k * y_opt[idx_r][idx_w][idx_q][f][0] * sys.Pi_PRB
                                for idx_r, r in enumerate(reqs)
                                if r.beta < 1e6
                                for idx_w, w in enumerate(r.V_R)
                                for k in range(1, w.K_REQ + 1)
                            ) + sum(
                                y_opt[idx_r][idx_w][idx_q][f][0] * sys.Pi_FGB
                                for idx_r, r in enumerate(reqs)
                                if r.beta < 1e6 and r.gamma == 1
                                for idx_w, w in enumerate(r.V_R)
                                for k in range(1, w.K_REQ + 1)
                            )) <= q.Pi_MAX[0]
                             for idx_q, q in enumerate(V_P_R)
                            )
                cond_3 = all((sum(b_opt[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][0] + z_opt[idx_r][idx_e][idx_l][0] * (sys.B_WSC + sys.B_WGB)
                                        for idx_r, r in enumerate(reqs)
                                        if r.beta < 1e6 and r.gamma == 1
                                        for idx_e, e in enumerate(r.E)
                                        for idx_e_p, e_p in enumerate(E_P)
                                        if l in L_pqi[idx_e_p]
                                    ) + sum(
                                        b_opt[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][0]
                                        for idx_r, r in enumerate(reqs)
                                        if r.beta < 1e6 and (r.gamma == 0 or r.gamma == 2)
                                        for idx_e, e in enumerate(r.E)
                                        for idx_e_p, e_p in enumerate(E_P)
                                        if l in L_pqi[idx_e_p]
                                    ) + sys.B_WSC) <= l.B_MAX[0]
                             for idx_l, l in enumerate(L)
                            )
                cond_4 = profit - profit_in >= P_min
                
                if cond_1 and cond_2 and cond_3 and cond_4:
                    reqs_lp_t.append(r_t)
                    X_t = [[[x_opt[idx_r][idx_v][idx_p] for idx_p, p in enumerate(V_P_S)] for idx_v, v in enumerate(r_t.V_S)] for idx_r, r in enumerate(reqs)]
                    Y_t = [[[[[y_opt[idx_r][idx_w][idx_q][f][k] for k in range(K_MAX)] for f in range(F_MAX)] for idx_q, q in enumerate(V_P_R)] for idx_w, w in enumerate(r_t.V_R)] for idx_r, r in enumerate(reqs)]

                    violat = g_vio_opt
                    migrat = n_mig_opt
                    deploy = g_dep_opt
                else:
                    reqs.pop()
                    len_reqs = len(reqs)
                    
                    profit = profit_in
                    deploy = 0
                    reject[r_t.gamma] = 1

        #print(x)
        m.update()
        m.write(file_name)

        return profit, violat, migrat, deploy, reject, timer, X_t, Y_t, m
    else:
        reqs.pop()
        
        if t != 0:
            profit = profit_in
            deploy = 0
        reject[r_t.gamma] = 1
        
        return profit_in, 0, 0, 0, reject, timer, X_t, Y_t, m