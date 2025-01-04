from libraries import *

def ia_ranking_iter(t, r_t, reqs_in, reqs_lp_t_in, X_t_in, Y_t_in, profit_in, file_name):
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

    feasible = 1

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
        
        c = [[[m.getVarByName(f"c_{idx_r}_{idx_v}_{idx_p}") for idx_p in range(len_V_P_S)] for idx_v in range(len_vservers)] for idx_r in range(len_reqs-1)]
        b = [[[[[m.getVarByName(f"b_{idx_r}_{idx_e}_{idx_l}_{pqi}_{s}") for s in range(S_MAX)] for pqi in range(len_L_pqi)] for idx_l in range(len_L)] for idx_e in range(len_vpaths)] for idx_r in range(len_reqs-1)]

    ############## 5G-INS ##############
    ## Decision Variables
    # Main Variables
    #print(len_reqs)

    #print(x)
    
    # c.append([[m.addVar(name=f"c_{len_reqs-1}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS) for idx_p in range(len_V_P_S)] for idx_v in range(len_vservers)])
    # b.append([[[[m.addVar(name=f"b_{len_reqs-1}_{idx_e}_{idx_l}_{pqi}_{s}", vtype=gp.GRB.CONTINUOUS) for s in range(S_MAX)] for pqi in range(len_L_pqi)] for idx_l in range(len_L)] for idx_e in range(len_vpaths)])

    # m.update()
    
    # Set parameters to improve performance
    m.setParam('Threads', 16)

    # variable_names = [v.varName for v in m.getVars()]
    
    ############## Binary Decision Variables ##############
    x = [[[0 for p in V_P_S] for v in r.V_S] for r in reqs]
    y = [[[[[0 for k in range(K_MAX)] for f in range(F_MAX)] for q in V_P_R] for v in r.V_R] for r in reqs]
    z = [[[[0 for s in range(S_MAX)] for l in L] for v in r.E] for r in reqs]
    
    ############## Greedy decisions ##############
    reqs_rem = reqs.copy()
    V_P_S_REM = V_P_S.copy()
    V_P_S_DEL = []
    V_P_R_REM = V_P_R.copy()
    V_P_R_DEL = []
    #print("reqs:",reqs_rem)
    while len(reqs_rem):
        if len(reqs_rem) == 0:
            break
        #print("Revenues:",[r.R for r in reqs_rem])
        r_sel = max(reqs_rem, key=lambda request: request.R)
        #print("rsel:",reqs.index(r_sel))

        index_pop = reqs_rem.index(r_sel)
        reqs_rem.pop(index_pop) #[r for r in reqs_rem if reqs.index(r) != reqs.index(r_sel)]
        #print("reqs_rem:", reqs_rem)

        V_R_REM   = r_sel.V_R.copy()
        for w in V_R_REM:
            V_P_R_REM_TMP = V_P_R_REM.copy()
            w_sel = max(V_R_REM,   key=lambda ru: ru.K_REQ)

            if r_sel.gamma == 2: ## Complete Isolation
                V_P_R_REM_TMP = [q for q in V_P_R_REM_TMP if sum(y[idx_r][idx_w][V_P_R.index(q)][f][k] for idx_r,r in enumerate(reqs) if idx_r != reqs.index(r_sel) for idx_w,w in enumerate(r.V_R) for f in range(F_MAX) for k in range(K_MAX)) == 0]
                #print(V_P_R_REM_TMP)
            
            if len(V_P_R_REM_TMP) == 0:
                print("infeasible2")
                feasible = 0
                if t != 0:
                    profit = profit_in
                reject[r_t.gamma] = 1

            q_sel      = 0
            f_sel      = 0
            k_sel      = 0
            #print("K_REQ:", w_sel.K_REQ)
            found = 0
            for q in V_P_R_REM_TMP:
                for f in range(len(q.Pi_MAX)):
                    for k in range(w_sel.K_REQ, 0, -1):
                        pi_used = sys.Pi_PRB*sys.N_FRM + sum(k1*y[idx_r1][idx_w1][V_P_R.index(q)][f][k1]*sys.Pi_PRB
                                                             for idx_r1, r1 in enumerate(reqs)
                                                             if(r1.beta < 1e6)
                                                             for idx_w1, w1 in enumerate(r1.V_R)
                                                             for k1 in range(w1.K_REQ + 1)
                                                            ) + sum(y[idx_r1][idx_w1][V_P_R.index(q)][f][k1]*sys.Pi_FGB
                                                                    for idx_r1, r1 in enumerate(reqs)
                                                                    if  (r1.beta < 1e6) and (r1.gamma == 1)
                                                                    for idx_w1, w1 in enumerate(r1.V_R)
                                                                    for k1 in range(1, w1.K_REQ + 1)
                                                                   )
                        #print("pi_used:", pi_used + k*sys.Pi_PRB)
                        if pi_used + k*sys.Pi_PRB <= q.Pi_MAX[f]:
                            q_sel = q
                            f_sel = f
                            k_sel = k

                            #print("KKKKKKKKKKKKKKKK", r_sel.gamma)
                            if r_sel.gamma == 2:
                                V_P_R_DEL.append(q_sel)
                                #print("HHHHHHHHHHHHHHHHHHHHHHHH")
                            #print(k_sel)
                            #print(feasible)
                            found = 1
                            break
                        elif (q_sel == 0) and (k == 1) and (V_P_R_REM.index(q) == (len(V_P_R_REM) - 1)) and (f == (len(q.Pi_MAX) - 1)):
                            print("infeasible3")
                            feasible = 0
                            if t != 0:
                                profit = profit_in
                            reject[r_t.gamma] = 1
                    if found:
                        break
                if found:
                    break
                            
            V_R_REM = [w for w in V_R_REM if (r_sel.V_R).index(w) != (r_sel.V_R).index(w_sel)]    
            V_P_R_REM = [w for w in V_P_R_REM if w not in V_P_R_DEL]
            if feasible:
                y[reqs.index(r_sel)][(r_sel.V_R).index(w_sel)][V_P_R.index(q_sel)][f_sel][k_sel] = 1

        #print(x)
        
        if feasible:
            V_S_REM   = r_sel.V_S.copy()
            for v in V_S_REM:
                V_P_S_REM_TMP = V_P_S_REM.copy()
                v_sel = max(V_S_REM,   key=lambda vserver: vserver.C_REQ)
                if r_sel.gamma == 2: ## Complete Isolation
                    V_P_S_REM_TMP = [p for p in V_P_S_REM if sum(x[idx_r][idx_v][V_P_S.index(p)] for idx_r,r in enumerate(reqs) if idx_r != reqs.index(r_sel) for idx_v,v in enumerate(r.V_S)) == 0]
                    # print(V_P_S_REM_TMP)
                    #print(V_P_S_REM_TMP)
                if len(V_P_S_REM_TMP) == 0:
                    print("infeasible1")
                    feasible = 0
                    if t != 0:
                        profit = profit_in
                    reject[r_t.gamma] = 1
                P_list = [e_p.p for e_p in E_P if e_p.q in V_P_R if V_P_R.index(e_p.q) == V_P_R.index(q_sel)]
                #print(V_P_S_REM_TMP)
                #print(P_list)
                #print(V_P_S_REM_TMP[-1], P_list[-1])
                V_P_S_REM_TMP = [p for p in P_list if p in V_P_S_REM_TMP]
                p_sel = max(V_P_S_REM_TMP, key=lambda pserver: pserver.C_MAX)
                #print("psel:", V_P_S.index(p_sel), reqs.index(r_sel))
                x[reqs.index(r_sel)][(r_sel.V_S).index(v_sel)][V_P_S.index(p_sel)] = 1

                if r_sel.gamma == 2:
                    V_P_S_DEL.append(p_sel)
                V_S_REM = [v for v in V_S_REM if (r_sel.V_S).index(v) != (r_sel.V_S).index(v_sel)]
            V_P_S_REM = [p for p in V_P_S_REM if (p in V_P_S_DEL) == 0] ## Remove that server for other slice requests

        if feasible:
            E_REM   = r_sel.E
            E_P_REM = E_P
            E_P_DEL = []
            for e in E_REM:
                e_sel_list = [e for e in r_sel.E if (r_sel.V_S.index(e.v) == r_sel.V_S.index(v_sel)) and (r_sel.V_R.index(e.w) == r_sel.V_R.index(w_sel))]

                e_sel = max(e_sel_list, key=lambda vpath: vpath.B_REQ)
                v_e_sel = e_sel.v
                w_e_sel = e_sel.w

                p_e_sel = p_sel#[p for p in V_P_S if x[reqs.index(r_sel)][r_sel.V_S.index(v_e_sel)][V_P_S.index(p)] == 1][0]
                q_e_sel = q_sel#[q for q in V_P_R if sum(y[reqs.index(r_sel)][r_sel.V_R.index(w_e_sel)][V_P_R.index(q)][f][k] for f in range(F_MAX) for k in range(K_MAX)) == 1][0]

                #print(e_sel_list)
                E_P_REM_SEARCH = [e_p for e_p in E_P_REM if (e_p.p in V_P_S) and (e_p.q in V_P_R)]
                #print(V_P_S.index(p_e_sel), V_P_R.index(q_e_sel))
                #print(E_P_REM)
                E_P_REM_SEARCH = [e_p for e_p in E_P_REM_SEARCH if (V_P_S.index(e_p.p) == V_P_S.index(p_e_sel)) and (V_P_R.index(e_p.q) == V_P_R.index(q_e_sel))]
                if len(E_P_REM_SEARCH) == 0:
                    print("infeasible4")
                    feasible = 0
                    if t != 0:
                        profit = profit_in
                    reject[r_t.gamma] = 1

                if feasible:
                    if e_sel.v in r_sel.V_S and e_sel.w in r_sel.V_S:
                        for p in V_P_S:
                            if(x[reqs.index(r_sel)][(r_sel.V_S).index(e_sel.v)][V_P_S.index(p)] == 1):
                                if(x[reqs.index(r_sel)][(r_sel.V_S).index(e_sel.w)][V_P_S.index(p)] == 1):
                                    E_REM = [e1 for e1 in E_REM if (r_sel.E).index(e1) != (r_sel.E).index(e_sel)]
                                    continue
                    elif e_sel.v in r_sel.V_R and e_sel.w in r_sel.V_R:
                        for q in V_P_R:
                            if(sum(y[reqs.index(r_sel)][(r_sel.V_R).index(e_sel.v)][V_P_R.index(q)][f][k]
                                   for f in range(len(q.Pi_MAX))
                                   for k in range((e.v).K_REQ + 1)) == 1):
                                if(sum(y[reqs.index(r_sel)][(r_sel.V_R).index(e_sel.v)][V_P_R.index(q)][f][k]
                                       for f in range(len(q.Pi_MAX))
                                       for k in range((e.v).K_REQ + 1)) == 1):
                                    E_REM = [e1 for e1 in E_REM if (r_sel.E).index(e1) != (r_sel.E).index(e_sel)]
                                    continue
    
                    B_MAX_MAX = 0
                    e_p_sel = 0
                    for idx_e_p, e_p in enumerate(E_P_REM_SEARCH):
                        if B_MAX_MAX <= min(max(l.B_MAX) for l in L_pqi[E_P.index(e_p)]):
                            B_MAX_MAX = min(max(l.B_MAX) for l in L_pqi[E_P.index(e_p)])
                            e_p_sel = e_p
    
                    for l in L_pqi[E_P.index(e_p_sel)]:
                        s_sel = l.B_MAX.index(max(l.B_MAX))
                        z[reqs.index(r_sel)][(r_sel.E).index(e_sel)][L.index(l)][s_sel] = 1
    
                    if r_sel.gamma == 2:
                        E_P_DEL.append(e_p_sel)
                    E_REM = [e for e in E_REM if (r_sel.E).index(e) != (r_sel.E).index(e_sel)]
                E_P_REM = [e_p for e_p in E_P_REM if (e_p in E_P_DEL) == 0]

    # print(f"x={x}")
    # print(f"x={y}")
    # print(f"x={z}")

    ############## 5G-INS ##############
    ## Decision Variables
    # Main Variables
    #print(len_reqs)

    #print("c=",c)
    
    c.append([[m.addVar(name=f"c_{len_reqs-1}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS) for idx_p in range(len_V_P_S)] for idx_v in range(len_vservers)])
    b.append([[[[m.addVar(name=f"b_{len_reqs-1}_{idx_e}_{idx_l}_{pqi}_{s}", vtype=gp.GRB.CONTINUOUS) for s in range(S_MAX)] for pqi in range(len_L_pqi)] for idx_l in range(len_L)] for idx_e in range(len_vpaths)])

    m.update()
    
    # Set parameters to improve performance
    m.setParam('Threads', 16)

    # variable_names = [v.varName for v in m.getVars()]
    # print(variable_names)
    
    ## Constraints
    ###################################### Node Mapping Constraints ######################################
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

    # Eq. 36 (Simplified Eq. 8)
    h_VM_0 = [sum(x[idx_r][idx_v][idx_p]
                  for idx_r, r in enumerate(reqs)
                  if  (r.gamma == 0) and (r.kappa == 0)
                  for idx_v, v in enumerate(r.V_S)
                  for xi       in range(1,v.Xi_REQ)
                  if  v.Chi_REQ[xi] == (sys.CHI_MAX - 1)
                 ) / p.Xi_MAX[0] + sum(max(((v.Chi_REQ[xi] == chi) * x[idx_r][idx_v][idx_p] / p.Xi_MAX[0]
                                           for idx_r, r in enumerate(reqs)
                                           if (r.gamma == 0) and (r.kappa == 0)
                                           for idx_v, v in enumerate(r.V_S)
                                           for xi in range(v.Xi_REQ))
                                          , default=0)
                                       for chi in range(sys.CHI_MAX)
                                      ) + sum(v.Xi_REQ * x[idx_r][idx_v][idx_p] / p.Xi_MAX[0]
                                              for idx_r, r in enumerate(reqs)
                                              if (r.gamma == 0) and (r.kappa == 1)
                                              for idx_v, v in enumerate(r.V_S)
                                             ) + 1 ## Plus 1 is the simplification of the ceiling function
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
            ) + (sys.C_CON + sys.C_GOS) * h_VM_0[idx_p] + sys.C_HHO * max(x[idx_r][idx_v][idx_p]*(r.gamma <= 1)
              for idx_r, r in enumerate(reqs)
              for idx_v, v in enumerate(r.V_S)
             ) + sys.C_GOS * sum(
                v.Xi_REQ * x[idx_r][idx_v][idx_p] * (r.gamma == 1)
                for idx_r, r in enumerate(reqs)
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


    # Eq. 15
    for idx_e, e in enumerate(r_t.E):
        for idx_l, l in enumerate(L):
            for s in range(len(l.B_MAX)):
                m.addConstr(
                    epsilon * z[len_reqs-1][idx_e][idx_l][s] <= gp.quicksum(
                        b[len_reqs-1][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s]
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
    h_B_1 = [[1 - sum(min(x[idx_r][(r.V_S).index(e.v)][idx_p], x[idx_r][(r.V_S).index(e.w)][idx_p])
                      for idx_p, p in enumerate(V_P_S)
                     )
              if  isinstance(e.v, vserver) and isinstance(e.w, vserver) else 0
              for idx_e, e in enumerate(r.E)
             ]
             for idx_r, r in enumerate(reqs)
            ]
    h_B_2 = [[1 - sum(min(sum(y[idx_r][(r.V_R).index(e.v)][idx_q][f][k]
                              for f in range(len(q.Pi_MAX))
                              for k in range((e.v).K_REQ + 1)
                             ),
                          sum(y[idx_r][r.V_R.index(e.w)][idx_q] 
                              for f in range(len(q.Pi_MAX))
                              for k in range(1,(e.w).K_REQ + 1)
                             )
                         )
                      for idx_q, q in enumerate(V_P_R)
                     )
              if  isinstance(e.v, ru) and isinstance(e.w, ru) else 0
              for idx_e, e in enumerate(r.E)
             ]
             for idx_r, r in enumerate(reqs)
            ]

    # Eq. 19
    h_B_h_1 = [
        [
            (sys.Psi_HDR * (r.gamma == 0) - 1) * gp.quicksum(
                b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(L_pqi[idx_e_p][0])][s]
                for idx_e_p, e_p in enumerate(E_P)
                if isinstance(e_p.p, pserver) and isinstance(e_p.q, pserver)
                for s in range(len(L_pqi[idx_e_p][0].B_MAX))
            ) + e.B_REQ * h_B_1[idx_r][idx_e]
            for idx_e, e in enumerate(r.E)
        ]
        for idx_r, r in enumerate(reqs)
    ]

    h_B_h_2 = [
        [
            (sys.Psi_HDR * (r.gamma == 0) - 1) * gp.quicksum(
                b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(L_pqi[idx_e_p][0])][s]
                for idx_e_p, e_p in enumerate(E_P)
                if (e_p.p in V_P_R) and (e_p.q in V_P_R)
                for s in range(len(L_pqi[idx_e_p][0].B_MAX))
            ) + e.B_REQ * h_B_2[idx_r][idx_e]
            for idx_e, e in enumerate(r.E)
        ]
        for idx_r, r in enumerate(reqs)
    ]

    h_B_h_3 = [
        [
            (sys.Psi_HDR * (r.gamma == 0) - 1) * gp.quicksum(
                b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(L_pqi[idx_e_p][0])][s]
                for idx_e_p, e_p in enumerate(E_P)
                if (e_p.p in V_P_S) and (e_p.q in V_P_R)
                for s in range(len(L_pqi[idx_e_p][0].B_MAX))
            ) + e.B_REQ
            for idx_e, e in enumerate(r.E)
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
                    ) <= e.B_REQ * sum(
                        y[len_reqs-1][r_t.V_R.index(e.w)][idx_q][f][k]
                        for f in range(len(q.Pi_MAX))
                        for k in range(1, K_MAX)
                    ),
                    name=f"node_path_mapping_coordination_2_{len_reqs-1}_{idx_e}_{idx_q}"
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
                      ) + sum(k * y[idx_r][idx_w][idx_q][f][k] * r.Phi[idx_q]
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
    g_K = sum((r.rho_K * w.K_REQ) - (r.rho_K * sum(k*y[idx_r][idx_w][idx_q][f][k]
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
    g_D_1 = sum(r.rho_D * max(max(min(e_p.D_RTT*sum(z[idx_r][idx_e][L.index(l)][s]
                                                for s in range(len(l.B_MAX))
                                               ) - e.D_REQ - M*h_B_1[idx_r][idx_e]
                                  for idx_l, l in enumerate(L_pqi[idx_e_p])
                                 )
                              for idx_e_p, e_p in enumerate(E_P)
                             ), 0)
                for idx_r, r in enumerate(reqs)
                for idx_e, e in enumerate(r.E)
                if  (e.v in r.V_S) and (e.w in r.V_S)
               )
    g_D_2 = sum(r.rho_D * max(max(min(e_p.D_RTT*sum(z[idx_r][idx_e][L.index(l)][s]
                                                for s in range(len(l.B_MAX))
                                               ) - e.D_REQ - M*h_B_2[idx_r][idx_e]
                                  for idx_l, l in enumerate(L_pqi[idx_e_p])
                                 )
                              for idx_e_p, e_p in enumerate(E_P)
                             ), 0)
                for idx_r, r in enumerate(reqs)
                for idx_e, e in enumerate(r.E)
                if  (e.v in r.V_R) and (e.w in r.V_R)
               )
    g_D_3 = sum(r.rho_D * max(max(min(e_p.D_RTT*sum(z[idx_r][idx_e][L.index(l)][s]
                                                for s in range(len(l.B_MAX))
                                               ) - e.D_REQ
                                  for idx_l, l in enumerate(L_pqi[idx_e_p])
                                 )
                              for idx_e_p, e_p in enumerate(E_P)
                             ), 0)
                for idx_r, r in enumerate(reqs)
                for idx_e, e in enumerate(r.E)
                if  (e.v in r.V_S) and (e.w in r.V_R)
               )

    # Eq. 30
    g_vio = g_D_1 + g_D_2 + g_D_3 + g_C + g_K + g_B_1 + g_B_2 + g_B_3

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

        g_dep_opt = sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,idx_l,s)] * r.Theta[idx_e_p]
                     for idx_r, r     in enumerate(reqs)
                     for idx_e, e     in enumerate(r.E)
                     for idx_e_p, e_p in enumerate(E_P)
                     for idx_l, l     in enumerate(L_pqi[idx_e_p])
                     for s            in range(len(l.B_MAX))
                    ) + sum(vars_opt["c_{}_{}_{}".format(idx_r,idx_v,idx_p)] * r.Omega[idx_p]
                            for idx_r, r in enumerate(reqs)
                            for idx_v, v in enumerate(r.V_S)
                            for idx_p, p in enumerate(V_P_S)
                           ) + sum(k * y[idx_r][idx_w][idx_q][f][k] * r.Phi[idx_q]
                                   for idx_r, r in enumerate(reqs)
                                   for idx_w, w in enumerate(r.V_R)
                                   for idx_q, q in enumerate(V_P_R)
                                   for f in range(len(q.Pi_MAX))
                                   for k in range(w.K_REQ + 1)
                                  )
        
        g_C_opt = sum(r.rho_C * v.C_REQ - r.rho_C * sum(vars_opt["c_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                                                        for idx_p, p in enumerate(V_P_S)
                                                       )
                  for idx_r, r in enumerate(reqs)
                  for idx_v, v in enumerate(r.V_S)
                 )
        g_K_opt = g_K


        h_B_h_1 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                         for idx_e_p, e_p in enumerate(E_P)
                                                         if  (e_p.p in V_P_S) and (e_p.q in V_P_S)
                                                         #for idx_l, l     in enumerate(L_pqi[idx_e_p])
                                                         for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                        ) + e.B_REQ*h_B_1[idx_r][idx_e]
                    for idx_e, e in enumerate(r.E)
                    #if  (e.v in r.V_S) and (e.w in r.V_S)
                   ]
                   for idx_r, r in enumerate(reqs)
                  ]
        h_B_h_2 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                         for idx_e_p, e_p in enumerate(E_P)
                                                         if  (e_p.p in V_P_R) and (e_p.q in V_P_R)
                                                         for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                        ) + e.B_REQ*h_B_2[idx_r][idx_e]
                    for idx_e, e in enumerate(r.E)
                    #if  (e.v in r.V_R) and (e.w in r.V_R)
                   ]
                   for idx_r, r in enumerate(reqs)
                  ]
        h_B_h_3 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                         for idx_e_p, e_p in enumerate(E_P)
                                                         if  (e_p.p in V_P_S) and (e_p.q in V_P_R)
                                                         for s            in range(len(L_pqi[idx_e_p][0].B_MAX))
                                                        ) + e.B_REQ
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
        g_vio_opt = g_D_1 + g_D_2 + g_D_3 + g_C_opt + g_K_opt + g_B_1_opt + g_B_2_opt + g_B_3_opt

        g_mig_opt = g_mig

        print("Runtime:")
        print(timer)
        
        profit = m.objVal
        print("Delay, Radio, MIPS, and Bandwidth Violation Costs:")
        print(g_D_1, g_D_2, g_D_3, g_K_opt, g_C_opt, g_B_1_opt, g_B_2_opt, g_B_3_opt)
        print("Deployment, Violation, and Migration Costs:")
        print(g_dep_opt, g_vio_opt, g_mig_opt)
        print("Profit:")
        print(profit)

        n_mig_opt = sum(sum(x[idx_r][idx_v][idx_p]
                            for idx_p, p in enumerate(V_P_S)
                            if(len(X_t))
                            if(X_t[idx_r][idx_v][idx_p] == 0)
                           )
                        for idx_r, r in enumerate(reqs_lp_t)
                        for idx_v, v in enumerate(r.V_S)
                       ) + sum(sum(sum(y[idx_r][idx_w][idx_q][f][k]
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

#         # Print the optimal values of variables
#         for var_name, value in vars_opt.items():
#             print(f"{var_name}: {value}")

        X_t = [[[x[idx_r][idx_v][idx_p] for idx_p, p in enumerate(V_P_S)] for idx_v, v in enumerate(r.V_S)] for idx_r, r in enumerate(reqs)]
        Y_t = [[[[[y[idx_r][idx_w][idx_q][f][k] for k in range(K_MAX)] for f in range(F_MAX)] for idx_q, q in enumerate(V_P_R)] for idx_w, w in enumerate(r.V_R)] for idx_r, r in enumerate(reqs)]

        violat = g_vio_opt
        migrat = n_mig_opt
        deploy = g_dep_opt

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