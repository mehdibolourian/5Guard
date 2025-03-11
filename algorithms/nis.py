from libraries import *

# class TimeoutException(Exception):
#     pass

# def timeout_optimize(model):
#     model.optimize()
#     return model

# def run_with_timeout(timeout, func, *args, **kwargs):
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         future = executor.submit(func, *args, **kwargs)
#         try:
#             return future.result(timeout=timeout)
#         except concurrent.futures.TimeoutError:
#             raise TimeoutException("Timeout reached!")

def nis_iter(profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, f_fgr, X_t, Y_t):
    offset = 0
    scale  = 5
    
    reqs = R_t.copy()
    
    len_R      = len(reqs)
    len_V_P_S  = len(V_P_S)
    len_V_P_R  = len(V_P_R)
    len_E_P    = len(E_P)
    len_L      = len(L)
    len_L_pqi  = max((len(L_pqi[idx_e_p]) for idx_e_p, e_p in enumerate(E_P)), default=0)
    len_E_P_l  = max((len(E_P_l[idx_l]) for idx_l, l in enumerate(L)), default=0)

    ## Before appending r_t
    len_R    = len(reqs)
    len_E    = max((len(r.E)   for idx_r, r in enumerate(reqs)), default=0)
    len_V_S  = max((len(r.V_S) for idx_r, r in enumerate(reqs)), default=0)
    len_V_R  = max((len(r.V_R) for idx_r, r in enumerate(reqs)), default=0)

    profit_opt = 0
    violat_opt = np.zeros(5) ## 5 for Total, Radio, Bandwidth, MIPS, and Delay
    migrat_opt = 0
    deploy_opt = np.zeros(4) ## 4 for Total, Radio, Bandwidth, and MIPS
    overhe_opt = np.zeros(4) ## 4 for Total, Radio, Bandwidth, and MIPS  --> Resource Overhead
    reseff_opt = np.zeros(4) ## 4 for Overal, Radio, Bandwidth, and MIPS --> Resource Efficiency
    reject_opt = np.zeros(3) ## 3 for 3 isolation levels
    time_opt   = 0           ## --> Allocation Time
    vars_opt   = {}
    feasible   = 0
    timeout    = 0

    # Main Variables
    x = []
    y = []
    z = []
    c = []
    b = []
    
    # Auxiliary Variables
    a_x2 = []
    a_x3 = []
    a_x4 = []

    a_y2 = []
    
    a_z2 = []
    a_z3 = []
    a_z4 = []

    ############## 5G-INS ##############
    # Create Optimization Model
    m = gp.read(f'saved_model/model_backup_nis_{iter}.mps')

    ##  Main Variables
    #   Only append the variable for the incoming SR and reuse the other variables from the last instance of the problem
    x = [[[m.getVarByName(f"x_{idx_r}_{idx_v}_{idx_p}")
           if m.getVarByName(f"x_{idx_r}_{idx_v}_{idx_p}") is not None
           else m.addVar(name=f"x_{idx_r}_{idx_v}_{idx_p}", vtype=gp.GRB.BINARY)
           for idx_p in range(len_V_P_S)]
          for idx_v in range(len_V_S)]
         for idx_r in range(len_R)]
    y = [[[[[m.getVarByName(f"y_{idx_r}_{idx_v}_{idx_q}_{f}_{k}")
             if m.getVarByName(f"y_{idx_r}_{idx_v}_{idx_q}_{f}_{k}") is not None
             else m.addVar(name=f"y_{idx_r}_{idx_v}_{idx_q}_{f}_{k}", vtype=gp.GRB.BINARY)
             for k in range(K_MAX)]
            for f in range(F_MAX)]
           for idx_q in range(len_V_P_R)]
          for idx_v in range(len_V_R)]
         for idx_r in range(len_R)]
    z = [[[[m.getVarByName(f"z_{idx_r}_{idx_e}_{idx_l}_{s}")
            if m.getVarByName(f"z_{idx_r}_{idx_e}_{idx_l}_{s}") is not None
            else m.addVar(name=f"z_{idx_r}_{idx_e}_{idx_l}_{s}", vtype=gp.GRB.BINARY)
            for s in range(S_MAX)]
           for idx_l in range(len_L)]
          for idx_e in range(len_E)]
         for idx_r in range(len_R)]
    c = [[[m.getVarByName(f"c_{idx_r}_{idx_v}_{idx_p}")
           if m.getVarByName(f"c_{idx_r}_{idx_v}_{idx_p}") is not None
           else m.addVar(name=f"c_{idx_r}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS)
           for idx_p in range(len_V_P_S)]
          for idx_v in range(len_V_S)]
         for idx_r in range(len_R)]
    b = [[[[[m.getVarByName(f"b_{idx_r}_{idx_e}_{idx_l}_{e_p}_{s}")
             if m.getVarByName(f"b_{idx_r}_{idx_e}_{idx_l}_{e_p}_{s}") is not None
             else m.addVar(name=f"b_{idx_r}_{idx_e}_{idx_l}_{e_p}_{s}", vtype=gp.GRB.CONTINUOUS)
             for s in range(S_MAX)]
            for e_p in range(len_E_P)]
           for idx_l in range(len_L)]
          for idx_e in range(len_E)]
         for idx_r in range(len_R)]
    
    # Auxiliary Variables
    a_x2 = [[m.getVarByName(f"a_x2_{idx_p}_{chi}")
             for chi in range(sys.CHI_MAX+1)]
            for idx_p in range(len_V_P_S)]
    a_x3 = [m.getVarByName(f"a_x3_{idx_p}")
            for idx_p in range(len_V_P_S)]  
    a_x4 = [[[m.getVarByName(f"a_x4_{idx_r}_{idx_v}_{idx_p}")
              if m.getVarByName(f"a_x4_{idx_r}_{idx_v}_{idx_p}") is not None
              else m.addVar(name=f"a_x4_{idx_r}_{idx_v}_{idx_p}", vtype=gp.GRB.BINARY)
              for idx_p in range(len_V_P_S)]
             for idx_v in range(len_E)]
            for idx_r in range(len_R)]

    a_y2 = [[[m.getVarByName(f"a_y2_{idx_r}_{idx_v}_{idx_p}")
              if m.getVarByName(f"a_y2_{idx_r}_{idx_v}_{idx_p}") is not None
              else m.addVar(name=f"a_y2_{idx_r}_{idx_v}_{idx_p}", vtype=gp.GRB.BINARY)
              for idx_p in range(len_V_P_R)]
             for idx_v in range(len_E)]
            for idx_r in range(len_R)]

    a_z2 = [[[m.getVarByName(f"a_z2_{idx_r}_{idx_v}_{idx_e}")
              if m.getVarByName(f"a_z2_{idx_r}_{idx_v}_{idx_e}") is not None
              else m.addVar(name=f"a_z2_{idx_r}_{idx_v}_{idx_e}", vtype=gp.GRB.BINARY)
              for idx_e in range(len_E_P)]
             for idx_v in range(len_E)]
            for idx_r in range(len_R)]
    a_z3 = [[m.getVarByName(f"a_z3_{idx_r}_{idx_v}")
             if m.getVarByName(f"a_z3_{idx_r}_{idx_v}") is not None
             else m.addVar(name=f"a_z3_{idx_r}_{idx_v}", vtype=gp.GRB.CONTINUOUS)
             for idx_v in range(len_E)]
            for idx_r in range(len_R)]
    a_z4 = [[m.getVarByName(f"a_z4_{idx_r}_{idx_v}")
             if m.getVarByName(f"a_z4_{idx_r}_{idx_v}") is not None
             else m.addVar(name=f"a_z4_{idx_r}_{idx_v}", vtype=gp.GRB.BINARY)
             for idx_v in range(len_E)]
            for idx_r in range(len_R)]

    # ## Auxiliary variables
    if len(R_t) == 0: ## No model is defined yet --> No a_x2 or a_x3 defined
        a_x2 = [[m.addVar(name=f"a_x2_{idx_p}_{chi}", vtype=gp.GRB.BINARY)
                 for chi in range(sys.CHI_MAX+1)]
                for idx_p in range(len_V_P_S)]
        a_x3 = [m.addVar(name=f"a_x3_{idx_p}", vtype=gp.GRB.BINARY)
                for idx_p in range(len_V_P_S)]

    feasible = 1
        
    reqs.append(r_t)

    len_R    = len(reqs)
    len_E    = max(len(r.E)   for idx_r, r in enumerate(reqs))
    len_V_S  = max(len(r.V_S) for idx_r, r in enumerate(reqs))
    len_V_R  = max(len(r.V_R) for idx_r, r in enumerate(reqs))

    B_REQ_EFF = [[e.B_REQ
                  for e in r.E]
                 for r in reqs]
    K_REQ_EFF = [[w.K_REQ
                  for w in r.V_R]
                 for r in reqs]

    ## Only used for 5Guard: To handle infeasibility in the previous time step where the last SR is removed from the model.
    R_miss = [idx_r for idx_r, r in enumerate(reqs) if m.getVarByName(f"c_{idx_r}_{0}_{0}") is None]

    ################################ 5G-INS ################################
    ### Decision Variables
    ##  Main Variables
    #   Only append the variable for the incoming SR and reuse the other variables from the last instance of the problem
    x.append([[m.addVar(name=f"x_{len_R-1}_{idx_v}_{idx_p}", vtype=gp.GRB.BINARY)
               for idx_p in range(len_V_P_S)]
              for idx_v in range(len_V_S)])
    y.append([[[[m.addVar(name=f"y_{len_R-1}_{idx_v}_{idx_q}_{f}_{k}", vtype=gp.GRB.BINARY)
                 for k in range(K_MAX)]
                for f in range(F_MAX)]
               for idx_q in range(len_V_P_R)]
              for idx_v in range(len_V_R)])
    z.append([[[m.addVar(name=f"z_{len_R-1}_{idx_e}_{idx_l}_{s}", vtype=gp.GRB.BINARY)
                for s in range(S_MAX)]
               for idx_l in range(len_L)]
              for idx_e in range(len_E)])
    c.append([[m.addVar(name=f"c_{len_R-1}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS)
               for idx_p in range(len_V_P_S)]
              for idx_v in range(len_V_S)])
    b.append([[[[m.addVar(name=f"b_{len_R-1}_{idx_e}_{idx_e_p}_{idx_l}_{s}", vtype=gp.GRB.CONTINUOUS)
                 for s in range(S_MAX)]
                for idx_l in range(len_L_pqi)]
               for idx_e_p in range(len_E_P)]
              for idx_e in range(len_E)])
    
    # Auxiliary Variables
    a_x4.append([[m.addVar(name=f"a_x4_{len_R-1}_{idx_e}_{idx_p}", vtype=gp.GRB.BINARY)
                  for idx_p in range(len_V_P_S)]
                 for idx_e in range(len_E)])

    a_y2.append([[m.addVar(name=f"a_y2_{len_R-1}_{idx_e}_{idx_q}", vtype=gp.GRB.BINARY)
                  for idx_q in range(len_V_P_R)]
                 for idx_e in range(len_E)])

    a_z2.append([[m.addVar(name=f"a_z2_{len_R-1}_{idx_e}_{idx_e_p}", vtype=gp.GRB.BINARY)
                  for idx_e_p in range(len_E_P)]
                 for idx_e in range(len_E)])
    a_z3.append([m.addVar(name=f"a_z3_{len_R-1}_{idx_e}", vtype=gp.GRB.CONTINUOUS)
                 for idx_e in range(len_E)])
    a_z4.append([m.addVar(name=f"a_z4_{len_R-1}_{idx_e}", vtype=gp.GRB.BINARY)
                 for idx_e in range(len_E)])

    m.setParam('Threads', THREADS)
    
    m.update()
    
    ## Constraints
    ################################ Node Mapping Constraints ################################
    # Eq. 1
    for idx_r in R_miss:
        for idx_v, v in enumerate(reqs[idx_r].V_S):
            m.addConstr(
                gp.quicksum(x[idx_r][idx_v][idx_p] for idx_p in range(len(V_P_S))) == 1,
                name=f"nf_unique_mapping_{idx_r}_{idx_v}"
            )

    
    # Eq. 2
    for idx_r in R_miss:
        for idx_w, w in enumerate(reqs[idx_r].V_R):
            m.addConstr(
                gp.quicksum(y[idx_r][idx_w][idx_q][f][k]
                            for idx_q, q in enumerate(V_P_R)
                            for f in range(len(q.Pi_MAX))
                            for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)) == 1,
                name=f"ru_unique_mapping_{idx_r}_{idx_w}"
            )
    
    # Eq. 8
    for idx_r in R_miss:
        for idx_v, v in enumerate(reqs[idx_r].V_S):
            for idx_p, p in enumerate(V_P_S):
                m.addConstr(
                    delta * x[idx_r][idx_v][idx_p] <= c[idx_r][idx_v][idx_p],
                    name=f"mips_limit_1_{idx_r}_{idx_v}_{idx_p}"
                )
                m.addConstr(
                    c[idx_r][idx_v][idx_p] <= v.C_REQ * x[idx_r][idx_v][idx_p],
                    name=f"mips_limit_2_{idx_r}_{idx_v}_{idx_p}"
                )

    
    # Eq. 9
    for idx_r in R_miss:
        for idx_w, w in enumerate(reqs[idx_r].V_R):
            for idx_q, q in enumerate(V_P_R):
                m.addConstr(
                    gp.quicksum(
                        k * y[idx_r][idx_w][idx_q][f][k]
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                    ) <= K_REQ_EFF[idx_r][idx_w],
                    name=f"radio_overprovision_{idx_r}_{idx_w}_{idx_q}"
                )

    
    # Reduced Eq. 13
    h_VM_L0 = [gp.quicksum(x[idx_r][idx_v][idx_p]
                              for idx_r, r in enumerate(reqs)
                              for idx_v, v in enumerate(r.V_S)
                              for xi       in range(v.Xi_REQ)
                              if  (v.Chi_REQ[xi] == (sys.CHI_MAX + 1))
                          ) / p.Xi_MAX[0]
               + gp.quicksum(a_x2[idx_p][chi]
                                for chi in range(sys.CHI_MAX)
                            ) / p.Xi_MAX[0] + 1
               ## Plus 1 is the approximation of the ceiling function
               for idx_p, p in enumerate(V_P_S)
              ]

    
    # Reduced Eq. 15
    for idx_p, p in enumerate(V_P_S):
        if len_R >= 2:
            constraint_to_remove = m.getConstrByName(f"mips_max_limit_1_{idx_p}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)
                
        m.addConstr(
            gp.quicksum(c[idx_r][idx_v][idx_p]
                        for idx_r, r in enumerate(reqs)
                        for idx_v, v in enumerate(r.V_S)
                       ) 
            + (sys.C_K8S + sys.C_GOS) * h_VM_L0[idx_p]
            + sys.C_HHO * a_x3[idx_p]
            <= p.C_MAX,
            name=f"mips_max_limit_1_{idx_p}"
        )

    # Eq. 16
    for idx_p, p in enumerate(V_P_S):
        if len_R >= 2:
            constraint_to_remove = m.getConstrByName(f"mips_max_limit_2_{idx_p}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)
        
        m.addConstr(
            h_VM_L0[idx_p] <= p.Xi_MAX[1],
            name=f"mips_max_limit_2_{idx_p}"
        )

    # Reduced Eq. 19
    for idx_q, q in enumerate(V_P_R):
        for f in range(len(q.Pi_MAX)):
            if len_R >= 2:
                constraint_to_remove = m.getConstrByName(f"radio_max_limit_{idx_q}_{f}")
                if constraint_to_remove is not None:
                    m.remove(constraint_to_remove)
            
            m.addConstr(
                gp.quicksum(k * y[idx_r][idx_w][idx_q][f][k]
                            for idx_r, r in enumerate(reqs)
                            for idx_w, w in enumerate(r.V_R)
                            for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                           ) * sys.Pi_PRB
                <= q.Pi_MAX[f],
                name=f"radio_max_limit_{idx_q}_{f}"
            )

    # ###################################### Link Mapping Constraints ######################################

    # Eq. 20
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            m.addConstr(
                sum(a_z2[idx_r][idx_e][idx_e_p]
                    for idx_e_p, e_p in enumerate(E_P)
                ) <= 1,
                name=f"vp_unique_mapping_{idx_r}_{idx_e}"
            )

            
    # Eq. 23
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            for idx_l, l in enumerate(L):
                for s in range(len(l.B_MAX)):
                    m.addConstr(
                        epsilon * z[idx_r][idx_e][idx_l][s] <=
                        gp.quicksum(b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s]
                                    for idx_e_p, e_p in enumerate(E_P)
                                    if e_p in E_P_l[idx_l]
                                ),
                        name=f"link_path_mapping_coordination_1_{idx_r}_{idx_e}_{idx_l}_{s}"
                        )
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            for idx_l, l in enumerate(L):
                for s in range(len(l.B_MAX)):
                    m.addConstr(
                        (1 - sys.Psi_HDR)
                        * gp.quicksum(b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s]
                                    for idx_e_p, e_p in enumerate(E_P)
                                    if e_p in E_P_l[idx_l]
                                    )
                        <= B_REQ_EFF[idx_r][idx_e] * z[idx_r][idx_e][idx_l][s],
                        name=f"link_path_mapping_coordination_2_{idx_r}_{idx_e}_{idx_l}_{s}"
                    )
                
                
    # Eq. 24
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            for idx_e_p, e_p in enumerate(E_P):
                for idx_l_1, l_1 in enumerate(L_pqi[idx_e_p]):
                    for idx_l_2, l_2 in enumerate(L_pqi[idx_e_p]):
                        if (idx_l_1 != idx_l_2):
                            m.addConstr(
                                gp.quicksum(b[idx_r][idx_e][idx_e_p][idx_l_1][s]
                                            for s in range(S_MAX)
                                        ) ==
                                gp.quicksum(b[idx_r][idx_e][idx_e_p][idx_l_2][s]
                                            for s in range(S_MAX)
                                        ),
                                name=f"eq_constraint_{idx_r}_{idx_e}_{idx_e_p}_{idx_l_1}_{idx_l_2}"
                            )
                        
                        
    # Eq. 25
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S:
                for idx_p, p in enumerate(V_P_S):
                    m.addConstr(
                        (1 - sys.Psi_HDR)
                        * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                            for idx_e_p, e_p in enumerate(E_P)
                            if e_p.p in V_P_S
                            if V_P_S.index(e_p.p) == idx_p
                            for s in range(S_MAX)
                        )
                        <= B_REQ_EFF[idx_r][idx_e] * x[idx_r][reqs[idx_r].V_S.index(e.v)][idx_p],
                        name=f"node_path_mapping_coordination_1_{idx_r}_{idx_e}_{idx_p}"
                    )
            if e.w in reqs[idx_r].V_S:
                for idx_p, p in enumerate(V_P_S):
                    m.addConstr(
                        (1 - sys.Psi_HDR)
                        * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                            for idx_e_p, e_p in enumerate(E_P)
                            if e_p.p in V_P_S
                            if V_P_S.index(e_p.p) == idx_p
                            for s in range(S_MAX)
                        )
                        <= B_REQ_EFF[idx_r][idx_e] * x[idx_r][reqs[idx_r].V_S.index(e.w)][idx_p],
                        name=f"node_path_mapping_coordination_1_{idx_r}_{idx_e}_{idx_p}"
                    )

    # Eq. 26
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_R:
                for idx_q, q in enumerate(V_P_R):
                    m.addConstr(
                        (1 - sys.Psi_HDR)
                        * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                            for idx_e_p, e_p in enumerate(E_P)
                            if e_p.q in V_P_R
                            if V_P_R.index(e_p.q) == idx_q
                            for s in range(S_MAX)
                        )
                        <= B_REQ_EFF[idx_r][idx_e] * gp.quicksum(y[idx_r][reqs[idx_r].V_R.index(e.v)][idx_q][f][k]
                            for f in range(len(q.Pi_MAX))
                            for k in range(1, K_MAX)
                        ),
                        name=f"node_path_mapping_coordination_2_{idx_r}_{idx_e}_{idx_q}"
                    )
            if e.w in reqs[idx_r].V_R:
                for idx_q, q in enumerate(V_P_R):
                    m.addConstr(
                        (1 - sys.Psi_HDR)
                        * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                            for idx_e_p, e_p in enumerate(E_P)
                            if e_p.q in V_P_R
                            if V_P_R.index(e_p.q) == idx_q
                            for s in range(S_MAX)
                        )
                        <= B_REQ_EFF[idx_r][idx_e] * gp.quicksum(y[idx_r][reqs[idx_r].V_R.index(e.w)][idx_q][f][k]
                            for f in range(len(q.Pi_MAX))
                            for k in range(1, K_MAX)
                        ),
                        name=f"node_path_mapping_coordination_2_{idx_r}_{idx_e}_{idx_q}"
                    )


    # Revisitation
    h_REV_1 = [[1 - gp.quicksum(a_x4[idx_r][idx_e][idx_p]
                                for idx_p, p in enumerate(V_P_S)
                               )
                for idx_e, e in enumerate(r.E)
               ]
               for idx_r, r in enumerate(reqs)
              ]
    h_REV_2 = [[1 - gp.quicksum(a_y2[idx_r][idx_e][idx_q]
                                for idx_q, q in enumerate(V_P_R)
                               )
                for idx_e, e in enumerate(r.E)
               ]
               for idx_r, r in enumerate(reqs)
              ]
    h_D_3 = 0

    # Eq. 27
    h_B_h_1 = [[(sys.Psi_HDR - 1)
                * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                              for idx_e_p, e_p in enumerate(E_P)
                              if (e_p.p in V_P_S) and (e_p.q in V_P_S)
                              for s in range(S_MAX)
                             )
                + B_REQ_EFF[idx_r][idx_e] * h_REV_1[idx_r][idx_e]
                for idx_e, e in enumerate(r.E)
                #if  (e.v in r.V_S) and (e.w in r.V_S)
               ]
               for idx_r, r in enumerate(reqs)
              ]
    h_B_h_2 = [[(sys.Psi_HDR - 1)
                * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                              for idx_e_p, e_p in enumerate(E_P)
                              if (e_p.p in V_P_R) and (e_p.q in V_P_R)
                              for s in range(S_MAX)
                             )
                + B_REQ_EFF[idx_r][idx_e] * h_REV_2[idx_r][idx_e]
                for idx_e, e in enumerate(r.E)
                #if  (e.v in r.V_R) and (e.w in r.V_R)
               ]
               for idx_r, r in enumerate(reqs)
              ]
    h_B_h_3 = [[(sys.Psi_HDR - 1)
                * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                              for idx_e_p, e_p in enumerate(E_P)
                              if (e_p.p in V_P_S) and (e_p.q in V_P_R)
                              for s in range(S_MAX)
                             ) + B_REQ_EFF[idx_r][idx_e]
                for idx_e, e in enumerate(r.E)
                #if  (e.v in r.V_S) and (e.w in r.V_R)
               ]
               for idx_r, r in enumerate(reqs)
              ]

    # Eq. 28
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_S:
                m.addConstr(
                    h_B_h_1[idx_r][idx_e] >= 0,
                    name=f"bandwidth_overprovisioning_1_{idx_r}_{idx_e}"
                )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_R and e.w in reqs[idx_r].V_R:
                m.addConstr(
                    h_B_h_2[idx_r][idx_e] >= 0,
                    name=f"bandwidth_overprovisioning_2_{idx_r}_{idx_e}"
                )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_R:
                m.addConstr(
                    h_B_h_3[idx_r][idx_e] >= 0,
                    name=f"bandwidth_overprovisioning_3_{idx_r}_{idx_e}"
                )
            
                        
    # Reduced Eq. 31
    for idx_l, l in enumerate(L):
        for s in range(len(l.B_MAX)):
            if len_R >= 2:
                constraint_to_remove = m.getConstrByName(f"bandwidth_max_limit_{idx_l}_{s}")
                if constraint_to_remove is not None:
                    m.remove(constraint_to_remove)
            
            m.addConstr(
                gp.quicksum(b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s]
                              for idx_r, r in enumerate(reqs)
                              for idx_e, e in enumerate(r.E)
                              for idx_e_p, e_p in enumerate(E_P)
                              if e_p in E_P_l[idx_l]
                ) <= l.B_MAX[s],
                name=f"bandwidth_max_limit_{idx_l}_{s}"
            )


    # Auxiliary variables' constraints
    ##################### a_x4 = min(x1, x2):
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_S:
                for idx_p, p in enumerate(V_P_S):
                    m.addConstr(
                        a_x4[idx_r][idx_e][idx_p] <= x[idx_r][reqs[idx_r].V_S.index(e.v)][idx_p],
                        name=f"auxiliary_constraints_1_1_{idx_r}_{idx_e}_{idx_p}"
                    )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_S:
                for idx_p, p in enumerate(V_P_S):
                    m.addConstr(
                        a_x4[idx_r][idx_e][idx_p] <= x[idx_r][reqs[idx_r].V_S.index(e.w)][idx_p],
                        name=f"auxiliary_constraints_1_2_{idx_r}_{idx_e}_{idx_p}"
                    )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_S:
                for idx_p, p in enumerate(V_P_S):
                    m.addConstr(
                        a_x4[idx_r][idx_e][idx_p] >= x[idx_r][reqs[idx_r].V_S.index(e.v)][idx_p] + x[idx_r][reqs[idx_r].V_S.index(e.w)][idx_p] - 1,
                        name=f"auxiliary_constraints_1_3_{idx_r}_{idx_e}_{idx_p}"
                    )

    ##################### a_y2 = min(sum(sum(y1)), sum(sum(y2))):
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_R and e.w in reqs[idx_r].V_R:
                for idx_q, q in enumerate(V_P_R):
                    m.addConstr(
                        a_y2[idx_r][idx_e][idx_q] <= gp.quicksum(y[idx_r][reqs[idx_r].V_R.index(e.v)][idx_q][f][k]
                                                                for f in range(len(q.Pi_MAX))
                                                                for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                                                                ),
                        name=f"auxiliary_constraints_2_1_{idx_r}_{idx_e}_{idx_q}"
                    )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_R and e.w in reqs[idx_r].V_R:
                for idx_q, q in enumerate(V_P_R):
                    m.addConstr(
                        a_y2[idx_r][idx_e][idx_q] <= gp.quicksum(y[idx_r][reqs[idx_r].V_R.index(e.w)][idx_q][f][k]
                                                                for f in range(len(q.Pi_MAX))
                                                                for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                                                                ),
                        name=f"auxiliary_constraints_2_2_{idx_r}_{idx_e}_{idx_q}"
                    )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_R and e.w in reqs[idx_r].V_R:
                for idx_q, q in enumerate(V_P_R):
                    m.addConstr(
                        a_y2[idx_r][idx_e][idx_q] >= gp.quicksum(y[idx_r][reqs[idx_r].V_R.index(e.v)][idx_q][f][k]
                                                                for f in range(len(q.Pi_MAX))
                                                                for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                                                                )
                        + gp.quicksum(y[idx_r][reqs[idx_r].V_R.index(e.w)][idx_q][f][k]
                                    for f in range(len(q.Pi_MAX))
                                    for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                                    ) - 1,
                        name=f"auxiliary_constraints_2_3_{idx_r}_{idx_e}_{idx_q}"
                    )

    ##################### a_z2 = min(sum(z)):
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            for idx_e_p, e_p in enumerate(E_P):
                for idx_l, l in enumerate(L_pqi[idx_e_p]):
                    m.addConstr(
                        a_z2[idx_r][idx_e][idx_e_p] <= gp.quicksum(z[idx_r][idx_e][L.index(l)][s]
                                                                    for s in range(len(l.B_MAX))
                                                                    ),
                        name=f"auxiliary_constraints_3_1_{idx_r}_{idx_e}_{idx_e_p}_{idx_l}"
                    )
        for idx_e, e in enumerate(reqs[idx_r].E):
            for idx_e_p, e_p in enumerate(E_P):
                m.addConstr(
                    a_z2[idx_r][idx_e][idx_e_p] >= gp.quicksum(z[idx_r][idx_e][L.index(l)][s]
                                                                for idx_l, l in enumerate(L_pqi[idx_e_p])
                                                                for s in range(len(l.B_MAX))
                                                                ) - (len(L) - 1),
                    name=f"auxiliary_constraints_3_2_{idx_r}_{idx_e}_{idx_e_p}"
                )

    ##################### a_z3 = [sum(D*a_z2) - h_D]+:
    for idx_r in R_miss:
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_S:
                m.addConstr(
                    a_z3[idx_r][idx_e] >= sum(e_p.D_RTT * a_z2[idx_r][idx_e][idx_e_p]
                                                for idx_e_p, e_p in enumerate(E_P)
                                            ) - e.D_REQ - M * (1 - h_REV_1[idx_r][idx_e]),
                    name=f"auxiliary_constraints_6_1_{idx_r}_{idx_e}_{idx_e_p}"
                )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_R and e.w in reqs[idx_r].V_R:
                m.addConstr(
                    a_z3[idx_r][idx_e] >= sum(e_p.D_RTT * a_z2[idx_r][idx_e][idx_e_p]
                                                for idx_e_p, e_p in enumerate(E_P)
                                            ) - e.D_REQ - M * (1 - h_REV_2[idx_r][idx_e]),
                    name=f"auxiliary_constraints_6_2_{idx_r}_{idx_e}_{idx_e_p}"
                )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_R:
                m.addConstr(
                    a_z3[idx_r][idx_e] >= sum(e_p.D_RTT * a_z2[idx_r][idx_e][idx_e_p]
                                                for idx_e_p, e_p in enumerate(E_P)
                                            ) - e.D_REQ,
                    name=f"auxiliary_constraints_6_3_{idx_r}_{idx_e}_{idx_e_p}"
                )
        for idx_e, e in enumerate(reqs[idx_r].E):
            m.addConstr(
                a_z3[idx_r][idx_e] >= 0,
                name=f"auxiliary_constraints_7_{idx_r}_{idx_e}"
            )

        for idx_e, e in enumerate(reqs[idx_r].E):
            m.addConstr(
                a_z3[idx_r][idx_e] <= N * a_z4[idx_r][idx_e],
                name=f"auxiliary_constraints_8_1_{idx_r}_{idx_e}"
            )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_S:
                for idx_e_p, e_p in enumerate(E_P):
                    m.addConstr(
                        a_z3[idx_r][idx_e] <= e_p.D_RTT * a_z2[idx_r][idx_e][idx_e_p] - e.D_REQ - M * (1 - h_REV_1[idx_r][idx_e]) + N * (1 - a_z4[idx_r][idx_e]),
                        name=f"auxiliary_constraints_8_2_{idx_r}_{idx_e}_{idx_e_p}"
                    )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_R and e.w in reqs[idx_r].V_R:
                for idx_e_p, e_p in enumerate(E_P):
                    m.addConstr(
                        a_z3[idx_r][idx_e] <= e_p.D_RTT * a_z2[idx_r][idx_e][idx_e_p] - e.D_REQ - M * (1 - h_REV_2[idx_r][idx_e]) + N * (1 - a_z4[idx_r][idx_e]),
                        name=f"auxiliary_constraints_8_3_{idx_r}_{idx_e}_{idx_e_p}"
                    )
        for idx_e, e in enumerate(reqs[idx_r].E):
            if e.v in reqs[idx_r].V_S and e.w in reqs[idx_r].V_R:
                for idx_e_p, e_p in enumerate(E_P):
                    m.addConstr(
                        a_z3[idx_r][idx_e] <= e_p.D_RTT * a_z2[idx_r][idx_e][idx_e_p] - e.D_REQ + N * (1 - a_z4[idx_r][idx_e]),
                        name=f"auxiliary_constraints_8_4_{idx_r}_{idx_e}_{idx_e_p}"
                    )

    ##################### a_x3 = max_{\gamma<=1}(x):
    for idx_r in R_miss:
        for idx_p, p in enumerate(V_P_S):
            for idx_v, v in enumerate(reqs[idx_r].V_S):
                m.addConstr(
                    a_x3[idx_p] >= x[idx_r][idx_v][idx_p],
                    name=f"auxiliary_constraints_8_1_{idx_r}_{idx_v}_{idx_p}"
                )

    for idx_p, p in enumerate(V_P_S):
        if len_R >= 2:
            constraint_to_remove = m.getConstrByName(f"auxiliary_constraints_8_2_{idx_p}")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)
        
        m.addConstr(
            a_x3[idx_p] <= gp.quicksum(x[idx_r][idx_v][idx_p]
                                       for idx_r, r in enumerate(reqs)
                                       for idx_v, v in enumerate(r.V_S)
                                      ),
            name=f"auxiliary_constraints_8_2_{idx_p}"
        )

    ##################### a_x2 = max_{\gamma=\kappa=0}(x):
    for idx_r in R_miss:
        for idx_p, p in enumerate(V_P_S):
            for chi in range(sys.CHI_MAX + 1):
                for idx_v, v in enumerate(reqs[idx_r].V_S):
                    for xi in range(v.Xi_REQ):
                        m.addConstr(
                            a_x2[idx_p][chi] >= (v.Chi_REQ[xi] == chi) * x[idx_r][idx_v][idx_p],
                            name=f"auxiliary_constraints_9_1_{idx_p}_{chi}_{idx_r}_{idx_v}_{xi}"
                        )

    for idx_p, p in enumerate(V_P_S):
        for chi in range(sys.CHI_MAX + 1):
            if len_R >= 2:
                constraint_to_remove = m.getConstrByName(f"auxiliary_constraints_9_2_{idx_p}_{chi}")
                if constraint_to_remove is not None:
                    m.remove(constraint_to_remove)
            
            m.addConstr(
                a_x2[idx_p][chi] <= gp.quicksum((v.Chi_REQ[xi] == chi) * x[idx_r][idx_v][idx_p]
                                                for idx_r, r in enumerate(reqs)
                                                for idx_v, v in enumerate(r.V_S)
                                                for xi in range(v.Xi_REQ)
                                               ),
                name=f"auxiliary_constraints_9_2_{idx_p}_{chi}"
            )

    ###################################### Profit Constraints ######################################

    # Violation Costs
    # Eq. 32
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

    # Eq. 34
    g_D = gp.quicksum(r.rho_D * a_z3[idx_r][idx_e]
                      for idx_r, r in enumerate(reqs)
                      for idx_e, e in enumerate(r.E)
                     )
    
    # Eq. 35
    g_C = gp.quicksum(r.rho_C * (v.C_REQ - gp.quicksum(c[idx_r][idx_v][idx_p]
                                                       for idx_p, p in enumerate(V_P_S)
                                                      )
                                )
                      for idx_r, r in enumerate(reqs)
                      for idx_v, v in enumerate(r.V_S)
                     )

    # Eq. 36
    g_K = gp.quicksum(r.rho_K * (K_REQ_EFF[idx_r][idx_w] - gp.quicksum(k * y[idx_r][idx_w][idx_q][f][k]
                                                       for idx_q, q in enumerate(V_P_R)
                                                       for f in range(len(q.Pi_MAX))
                                                       for k in range(K_REQ_EFF[idx_r][idx_w] + 1)
                                                      )
                                )
                      for idx_r, r in enumerate(reqs)
                      for idx_w, w in enumerate(r.V_R)
                     )

    # Violation Cost
    g_vio = g_D + g_C + g_K + g_B_1 + g_B_2 + g_B_3

    # Deployment Costs
    g_dep = ( sys.Theta * gp.quicksum(b[idx_r][idx_e][idx_e_p][idx_l][s]
                                      for idx_r, r     in enumerate(reqs)
                                      for idx_e, e     in enumerate(r.E)
                                      for idx_e_p, e_p in enumerate(E_P)
                                      for idx_l, l     in enumerate(L_pqi[idx_e_p])
                                      for s            in range(len(l.B_MAX))
                                     )
            + sys.Omega * gp.quicksum(c[idx_r][idx_v][idx_p]
                                      for idx_r, r in enumerate(reqs)
                                      for idx_v, v in enumerate(r.V_S)
                                      for idx_p, p in enumerate(V_P_S)
                                     )
            + sys.Phi   * gp.quicksum(k * y[idx_r][idx_w][idx_q][f][k]
                                      for idx_r, r in enumerate(reqs)
                                      for idx_w, w in enumerate(r.V_R)
                                      for idx_q, q in enumerate(V_P_R)
                                      for f in range(len(q.Pi_MAX))
                                      for k in range(K_REQ_EFF[idx_r][idx_w] + 1)
                                     )
            )

    # Overhead Cost
    g_ovh = ( sys.Omega * gp.quicksum((sys.C_K8S + sys.C_GOS) * h_VM_L0[idx_p]
                                       + sys.C_HHO * a_x3[idx_p]
                                      for idx_p, p in enumerate(V_P_S)
                                     )
            )

    # Migration Cost
    g_mig = (gp.quicksum(gp.quicksum(r.beta * x[idx_r][idx_v][idx_p]
                                     for idx_p, p in enumerate(V_P_S)
                                     if(len(X_t))
                                     if(X_t[idx_r][idx_v][idx_p] == 0)
                                    )
                        for idx_r, r in enumerate(R_t)
                        for idx_v, v in enumerate(r.V_S)
                   )
            + gp.quicksum(gp.quicksum(r.beta * gp.quicksum(y[idx_r][idx_w][idx_q][f][k]
                                                           for f in range(len(q.Pi_MAX))
                                                           for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                                                          )
                                      for idx_q, q in enumerate(V_P_R)
                                      if(len(Y_t))
                                      if(sum(Y_t[idx_r][idx_w][idx_q][f][k]
                                             for f in range(len(q.Pi_MAX))
                                             for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                                            ) == 0)
                                     )
                          for idx_r, r in enumerate(R_t)
                          for idx_w, w in enumerate(r.V_R)
                         )
            )


    cost = ( sys.Theta  * sum(e.B_REQ for r in reqs for idx_e, e in enumerate(r.E))
            + sys.Omega * sum(v.C_REQ + (sys.C_K8S + sys.C_GOS)*v.Xi_REQ/110 + sys.C_HHO*v.Xi_REQ/110/60 for r in reqs for idx_v, v in enumerate(r.V_S))
            + sys.Phi   * sum(K_REQ_EFF[idx_r][idx_w] for idx_r, r in enumerate(reqs) for idx_w, w in enumerate(r.V_R))
           )
    revenue = int(cost * scale) + offset

    if len_R >= 2:
        constraint_to_remove = m.getConstrByName(f"minimum_profit")
        if constraint_to_remove is not None:
            m.remove(constraint_to_remove)
    # Eq. 38
    m.addConstr(
        (
            (revenue - g_dep - g_vio - g_mig - g_ovh - profit_prev) >= P_min
        ), name="minimum_profit"
    )
    
    m.setObjective(revenue - g_dep - g_vio - g_mig - g_ovh, GRB.MAXIMIZE)

    # Start the timer
    start_time = time.perf_counter()
    
    timeout = 0
    m.optimize()
    if time.perf_counter() - start_time > r_t.timeout:
        timeout = 1

    # Stop the timer
    end_time = time.perf_counter()
    time_opt = end_time - start_time

    status = m.status

    # Determine feasibility based on the status
    if (status == gp.GRB.OPTIMAL) and (timeout == 0):
        # Get the optimal values of variables
        vars_opt = {var.varName: var.x for var in m.getVars()}

        ############################## Deployment Costs ##############################
        g_dep_K_opt = (sys.Phi   * sum(k * vars_opt["y_{}_{}_{}_{}_{}".format(idx_r,idx_w,idx_q,f,k)]
                                      for idx_r, r in enumerate(reqs)
                                      for idx_w, w in enumerate(r.V_R)
                                      for idx_q, q in enumerate(V_P_R)
                                      for f in range(len(q.Pi_MAX))
                                      for k in range(K_REQ_EFF[idx_r][idx_w] + 1)
                                     )
                    )

        g_dep_B_opt = ( sys.Theta * sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,idx_l,s)]
                                      for idx_r, r     in enumerate(reqs)
                                      for idx_e, e     in enumerate(r.E)
                                      for idx_e_p, e_p in enumerate(E_P)
                                      for idx_l, l     in enumerate(L_pqi[idx_e_p])
                                      for s            in range(len(l.B_MAX))
                                     )
                    )

        g_dep_C_opt = (sys.Omega * sum(vars_opt["c_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                                      for idx_r, r in enumerate(reqs)
                                      for idx_v, v in enumerate(r.V_S)
                                      for idx_p, p in enumerate(V_P_S)
                                     )
                      )

        mips_cons = sum(vars_opt["c_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                      for idx_r, r in enumerate(reqs)
                      for idx_v, v in enumerate(r.V_S)
                      for idx_p, p in enumerate(V_P_S)
                   )
        mips_reqs = sum(v.C_REQ
                      for idx_r, r in enumerate(reqs)
                      for idx_v, v in enumerate(r.V_S)
                   )
        
        g_dep_opt = g_dep_K_opt + g_dep_B_opt + g_dep_C_opt
        
        ############################## Violation Costs ##############################
        g_D_opt = sum(r.rho_D * vars_opt["a_z3_{}_{}".format(idx_r,idx_e)]
                      for idx_r, r in enumerate(reqs)
                      for idx_e, e in enumerate(r.E)
                     )
        g_C_opt = sum(r.rho_C * v.C_REQ - r.rho_C * sum(vars_opt["c_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                                                        for idx_p, p in enumerate(V_P_S)
                                                       )
                      for idx_r, r in enumerate(reqs)
                      for idx_v, v in enumerate(r.V_S)
                     )
        g_K_opt = sum((r.rho_K * K_REQ_EFF[idx_r][idx_w]) - (r.rho_K * sum(k*vars_opt["y_{}_{}_{}_{}_{}".format(idx_r,idx_w,idx_q,f,k)]
                                                           for idx_q, q in enumerate(V_P_R)
                                                           for f in range(len(q.Pi_MAX))
                                                           for k in range(K_REQ_EFF[idx_r][idx_w] + 1)
                                                          )
                                            )
                      for idx_r, r in enumerate(reqs)
                      for idx_w, w in enumerate(r.V_R)
                     )


        h_REV_1 = [[1 - sum(vars_opt["a_x4_{}_{}_{}".format(idx_r,idx_e,idx_p)]
                            for idx_p, p in enumerate(V_P_S)
                           )
                    for idx_e, e in enumerate(r.E)
                   ]
                   for idx_r, r in enumerate(reqs)
                  ]
        h_REV_2 = [[1 - sum(vars_opt["a_y2_{}_{}_{}".format(idx_r,idx_e,idx_q)]
                            for idx_q, q in enumerate(V_P_R)
                           )
                    for idx_e, e in enumerate(r.E)
                   ]
                   for idx_r, r in enumerate(reqs)
                  ]
        h_D_3 = 0

        h_B_h_1 = [[(sys.Psi_HDR - 1) * sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                             for idx_e_p, e_p in enumerate(E_P)
                                                             if  (e_p.p in V_P_S) and (e_p.q in V_P_S)
                                                             for s            in range(S_MAX)
                                                            ) + B_REQ_EFF[idx_r][idx_e] * h_REV_1[idx_r][idx_e]
                    for idx_e, e in enumerate(r.E)
                    #if  (e.v in r.V_S) and (e.w in r.V_S)
                   ]
                   for idx_r, r in enumerate(reqs)
                  ]
        h_B_h_2 = [[(sys.Psi_HDR - 1) * sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                           for idx_e_p, e_p in enumerate(E_P)
                                                           if  (e_p.p in V_P_R) and (e_p.q in V_P_R)
                                                           for s            in range(S_MAX)
                                                          ) + B_REQ_EFF[idx_r][idx_e] * h_REV_2[idx_r][idx_e]
                    for idx_e, e in enumerate(r.E)
                    #if  (e.v in r.V_R) and (e.w in r.V_R)
                   ]
                   for idx_r, r in enumerate(reqs)
                  ]
        h_B_h_3 = [[(sys.Psi_HDR - 1) * sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                           for idx_e_p, e_p in enumerate(E_P)
                                                           if  (e_p.p in V_P_S) and (e_p.q in V_P_R)
                                                           for s            in range(S_MAX)
                                                          ) + B_REQ_EFF[idx_r][idx_e]
                    for idx_e, e in enumerate(r.E)
                    #if  (e.v in r.V_S) and (e.w in r.V_R)
                   ]
                   for idx_r, r in enumerate(reqs)
                  ]
        g_B_1_opt = sum(r.rho_B * h_B_h_1[idx_r][idx_e]
                        for idx_r, r in enumerate(reqs)
                        for idx_e, e in enumerate(r.E)
                        if (e.v in r.V_S) and (e.w in r.V_S)
                       )

        g_B_2_opt = sum(r.rho_B * h_B_h_2[idx_r][idx_e]
                        for idx_r, r in enumerate(reqs)
                        for idx_e, e in enumerate(r.E)
                        if (e.v in r.V_R) and (e.w in r.V_R)
                       )
        g_B_3_opt = sum(r.rho_B * h_B_h_3[idx_r][idx_e]
                        for idx_r, r in enumerate(reqs)
                        for idx_e, e in enumerate(r.E)
                        if (e.v in r.V_S) and (e.w in r.V_R)
                       )
        g_vio_opt = g_D_opt + g_C_opt + g_K_opt + g_B_1_opt + g_B_2_opt + g_B_3_opt

        ############################## Migration Cost ##############################
        g_mig_opt = sum(sum(r.beta * vars_opt["x_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                            for idx_p, p in enumerate(V_P_S)
                            if(len(X_t))
                            if(X_t[idx_r][idx_v][idx_p] == 0)
                           )
                        for idx_r, r in enumerate(R_t)
                        for idx_v, v in enumerate(r.V_S)
                       ) + sum(sum(r.beta * sum(vars_opt["y_{}_{}_{}_{}_{}".format(idx_r,idx_w,idx_q,f,k)]
                                                for f in range(len(q.Pi_MAX))
                                                for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                                               )
                                   for idx_q, q in enumerate(V_P_R)
                                   if(len(Y_t))
                                   if(sum(Y_t[idx_r][idx_w][idx_q][f][k]
                                          for f in range(len(q.Pi_MAX))
                                          for k in range(1, K_REQ_EFF[idx_r][idx_w] + 1)
                                         ) == 0)
                                  )
                               for idx_r, r in enumerate(R_t)
                               for idx_w, w in enumerate(r.V_R)
                              )

        ############################## Overhead Costs ##############################
        h_VM_L0 = [math.ceil(sum(vars_opt["x_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                       for idx_r, r in enumerate(reqs)
                       for idx_v, v in enumerate(r.V_S)
                       for xi       in range(v.Xi_REQ)
                       if  (r.gamma == 0) and (r.kappa == 0) and (v.Chi_REQ[xi] == (sys.CHI_MAX + 1))
                      ) / p.Xi_MAX[0]
                 + sum(vars_opt["a_x2_{}_{}".format(idx_p,chi)]
                       for chi in range(sys.CHI_MAX)
                      ) / p.Xi_MAX[0])
                  ## Plus 1 is the approximation of the ceiling function
                  for idx_p, p in enumerate(V_P_S)
                 ]

        g_ovh_K_opt = 0

        g_ovh_B_opt = 0

        g_ovh_C_opt = sum( sys.Omega * ((sys.C_K8S + sys.C_GOS) * h_VM_L0[idx_p]
                                           + sys.C_HHO * vars_opt["a_x3_{}".format(idx_p)]
                                          )
                             for idx_p, p in enumerate(V_P_S)
                            )

        g_ovh_opt = g_ovh_K_opt + g_ovh_B_opt + g_ovh_C_opt

        ############################## Resource Efficiency ##############################
        sum_K_REQ = sum(K_REQ_EFF[idx_r][idx_w]
                        for idx_r, r in enumerate(reqs)
                        for idx_w, w in enumerate(r.V_R)
                       ) * sys.Phi
        g_res_K_opt = min([sum_K_REQ / (g_dep_K_opt + g_ovh_K_opt) if (g_dep_K_opt + g_ovh_K_opt) != 0 else float('inf'), 1]) * 100

        sum_B_REQ = sum(B_REQ_EFF[idx_r][idx_e]
                        for idx_r, r     in enumerate(reqs)
                        for idx_e, e     in enumerate(r.E)
                        if sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,idx_l,s)]
                               for idx_e_p, e_p in enumerate(E_P)
                               for idx_l, l     in enumerate(L_pqi[idx_e_p])
                               for s            in range(len(l.B_MAX))
                              ) != 0
                           ) * sys.Theta
        g_res_B_opt = min([sum_B_REQ / (g_dep_B_opt + g_ovh_B_opt) if (g_dep_B_opt + g_ovh_B_opt) != 0 else float('inf'), 1]) * 100

        sum_C_REQ = sum(v.C_REQ
                        for idx_r, r in enumerate(reqs)
                        for idx_v, v in enumerate(r.V_S)
                       ) * sys.Omega
        g_res_C_opt = min([sum_C_REQ / (g_dep_C_opt + g_ovh_C_opt) if (g_dep_C_opt + g_ovh_C_opt) != 0 else float('inf'), 1]) * 100
        
        g_res_opt = (g_res_K_opt + g_res_B_opt + g_res_C_opt) / 3
        
        profit = revenue - g_dep_opt - g_vio_opt - g_mig_opt - g_ovh_opt #m.objVal

        n_mig_opt = sum(sum(vars_opt["x_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                            for idx_p, p in enumerate(V_P_S)
                            if(len(X_t))
                            if(X_t[idx_r][idx_v][idx_p] == 0)
                           )
                        for idx_r, r in enumerate(R_t)
                        for idx_v, v in enumerate(r.V_S)
                       ) + sum(sum(sum(vars_opt["y_{}_{}_{}_{}_{}".format(idx_r,idx_w,idx_q,f,k)]
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
                               for idx_r, r in enumerate(R_t)
                               for idx_w, w in enumerate(r.V_R)
                              )

        X_t = [[[vars_opt["x_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                 for idx_p, p in enumerate(V_P_S)]
                for idx_v, v in enumerate(r.V_S)]
               for idx_r, r in enumerate(reqs)]
        Y_t = [[[[[vars_opt["y_{}_{}_{}_{}_{}".format(idx_r,idx_w,idx_q,f,k)]
                   for k in range(K_MAX)]
                  for f in range(F_MAX)]
                 for idx_q, q in enumerate(V_P_R)]
                for idx_w, w in enumerate(r.V_R)]
               for idx_r, r in enumerate(reqs)]
        
        profit_opt    = profit
        
        violat_opt[0] = g_vio_opt
        violat_opt[1] = g_K_opt
        violat_opt[2] = g_B_1_opt + g_B_2_opt + g_B_3_opt
        violat_opt[3] = g_C_opt
        violat_opt[4] = g_D_opt
        
        migrat_opt    = n_mig_opt
        
        deploy_opt[0] = g_dep_opt
        deploy_opt[1] = g_dep_K_opt
        deploy_opt[2] = g_dep_B_opt
        deploy_opt[3] = g_dep_C_opt
        
        overhe_opt[0] = g_ovh_opt
        overhe_opt[1] = g_ovh_K_opt
        overhe_opt[2] = g_ovh_B_opt
        overhe_opt[3] = g_ovh_C_opt
        
        reseff_opt[0] = g_res_opt
        reseff_opt[1] = g_res_K_opt
        reseff_opt[2] = g_res_B_opt
        reseff_opt[3] = g_res_C_opt
    else:
        feasible = 0
        reject_opt[0] = 1

        reqs.pop()
        len_R = len(reqs)

        m = gp.read(f'saved_model/model_backup_nis_{iter}.mps')
        m.update()
        
    if time_opt > r_t.timeout:
        timeout  = 1
        feasible = 0
        reject_opt[0] = 1

        if len(reqs):
            reqs.pop()
            len_R = len(reqs)
            
            m = gp.read(f'saved_model/model_backup_nis_{iter}.mps')
            m.update()

    if feasible:
        data = [
            ["Algorithm", "NIS"],
            ["Request Isolation Level", f"({0}, {0})"],
            ["Profit", profit],
            ["Allocation Time", time_opt],
        ]
        if g_D_opt:
            data.append(["Delay Cost", g_D_opt])
        if g_K_opt:
            data.append(["Radio Violation Cost", g_K_opt])
        if g_C_opt:
            data.append(["MIPS Violation Cost", g_C_opt])
        if g_B_1_opt or g_B_2_opt or g_B_3_opt:
            data.append(["Bandwidth Violation Costs", f"{g_B_1_opt}, {g_B_2_opt}, {g_B_3_opt}"])
        if g_mig_opt:
            data.append(["Migration Cost", g_mig_opt])
        if g_ovh_opt:
            data.append(["Overhead Cost", g_ovh_opt])

        data.append(["Deployment Cost", g_dep_opt])
    else:
        data = [
            ["Algorithm", "NIS"],
            ["Request Isolation Level", f"({r_t.gamma}, {r_t.kappa})"],
            ["Allocation Time", time_opt],
            ["Feasible", feasible],
            ["Timeout", timeout]
        ]
    
    print(tabulate(data, headers=["Category", "Value"], tablefmt="grid"))

    m.update()
    m.write(f'saved_model/model_backup_nis_{iter}.mps')

    return [profit_opt, violat_opt, migrat_opt, deploy_opt, overhe_opt, reseff_opt, reject_opt.T, time_opt, vars_opt, feasible, timeout, reqs], X_t, Y_t