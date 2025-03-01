from libraries import *

class TimeoutException(Exception):
    pass

def timeout_optimize(model):
    model.optimize()
    return model

def run_with_timeout(timeout, func, *args, **kwargs):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutException("Timeout reached!")

def iar_iter(profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, f_fgr, X_t, Y_t):
    reqs_lp_t = [r for r in R_t if r.beta < 1e4]
    reqs_hp_t = [r for r in R_t if r.beta >= 1e4]
    reqs      = R_t.copy()
    
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

    K_MAX = 101
    F_MAX = 1
    S_MAX = 1

    profit_opt = 0
    violat_opt = np.zeros(5) ## 5 for Total, Radio, Bandwidth, MIPS, and Delay
    migrat_opt = 0
    deploy_opt = np.zeros(4) ## 4 for Total, Radio, Bandwidth, and MIPS
    overhe_opt = np.zeros(4) ## 4 for Total, Radio, Bandwidth, and MIPS  --> Resource Overhead
    reseff_opt = np.zeros(4) ## 4 for Overal, Radio, Bandwidth, and MIPS --> Resource Efficiency
    reject_opt = np.zeros(3) ## 3 for 3 isolation levels
    time_opt   = 0           ## --> Allocation Time
    vars_opt   = {}
    feasible   = 1           ## Only for IAR to save lines of code
    timeout    = 0

    timer      = 0

    ############## 5G-INS ##############
    # Create Optimization Model
    if f_fgr:
        m = gp.read(f'saved_model/model_backup_fgr_iar_{iter}.mps')
    else:
        m = gp.read(f'saved_model/model_backup_iar_{iter}.mps')

    ##  Main Variables
    #   Only append the variable for the incoming SR and reuse the other variables from the last instance of the problem
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
        
    reqs.append(r_t)

    len_R    = len(reqs)
    len_E    = max(len(r.E)   for idx_r, r in enumerate(reqs))
    len_V_S  = max(len(r.V_S) for idx_r, r in enumerate(reqs))
    len_V_R  = max(len(r.V_R) for idx_r, r in enumerate(reqs))

    B_REQ_EFF = [[e.B_REQ if r.gamma != 1 else max(e.B_REQ, math.ceil(e.B_REQ * BANDWIDTH_SCALE / sys.B_WSC) * sys.B_WSC)
                  for e in r.E]
                 for r in reqs]
    K_REQ_EFF = [[w.K_REQ if r.gamma != 1 else max(w.K_REQ, math.ceil(w.K_REQ / sys.N_FRM) * sys.N_FRM)
                  for w in r.V_R]
                 for r in reqs]

    ## Only used for 5Guard: To handle infeasibility in the previous time step where the last SR is removed from the model.
    R_miss = [idx_r for idx_r, r in enumerate(reqs) if m.getVarByName(f"c_{idx_r}_{0}_{0}") is None]

    #######################################################
    
    ############## Binary Decision Variables ##############
    x = [[[0 for p in V_P_S]
          for v in r.V_S]
         for r in reqs]
    y = [[[[[0 for k in range(K_MAX)]
            for f in range(F_MAX)]
           for q in V_P_R]
          for w in r.V_R]
         for r in reqs]
    z = [[[[0 for s in range(S_MAX)]
           for l in L]
          for e in r.E]
         for r in reqs]
    
    ############## Greedy decisions ##############
    # Start the timer
    start_time1 = time.perf_counter()

    ## Keep previous mappings for HP SRs
    for r in reqs_hp_t:
        for idx_v, v in enumerate(r.V_S):
            for idx_p, p in enumerate(V_P_S):
                x[reqs.index(r)][idx_v][idx_p] = X_t[reqs.index(r)][idx_v][idx_p]

        for idx_w, w in enumerate(r.V_R):
            for idx_q, q in enumerate(V_P_R):
                for f in range(len(q.Pi_MAX)):
                    for k in range(1, K_REQ_EFF[reqs.index(r)][idx_w] + 1):
                        y[reqs.index(r)][idx_w][idx_q][f][k] = Y_t[reqs.index(r)][idx_w][idx_q][f][k]

    reqs_rem = reqs.copy()
    
    V_P_S_REM = V_P_S.copy()
    V_P_S_DEL = []
    
    V_P_R_REM = V_P_R.copy()
    V_P_R_DEL = []
    while len(reqs_rem):
        if len(reqs_rem) == 0 or feasible == 0:
            break

        r_sel = max(reqs_rem, key=lambda request: request.R * (request.gamma + 1) * (request.beta + 1))

        index_pop = reqs_rem.index(r_sel)
        reqs_rem.pop(index_pop)

        idx_r_sel = reqs.index(r_sel)

        if (reqs[idx_r_sel].beta < 1e4) or (reqs[idx_r_sel] == r_t):
            V_R_REM   = r_sel.V_R.copy()
            for w in V_R_REM:
                V_P_R_REM_TMP = V_P_R_REM.copy() ## Avoiding unintended behavior by making a copy of the remaining list
                w_sel = max(V_R_REM, key=lambda ru: K_REQ_EFF[idx_r_sel][r_sel.V_R.index(ru)])
    
                idx_w_sel = r_sel.V_R.index(w_sel)
    
                if r_sel.gamma == 2: ## Complete Isolation
                    V_P_R_REM_TMP = [q for q in V_P_R_REM_TMP 
                                     if sum(y[idx_r][idx_w][V_P_R.index(q)][f][k]
                                            for idx_r,r in enumerate(reqs)
                                            if idx_r != reqs.index(r_sel)
                                            for idx_w,w in enumerate(r.V_R)
                                            for f in range(F_MAX)
                                            for k in range(K_MAX)) == 0]
                else: ## Other isolation levels
                    V_P_R_REM_TMP = [q for q in V_P_R_REM_TMP 
                                     if sum(y[idx_r][idx_w][V_P_R.index(q)][f][k]
                                            for idx_r,r in enumerate(reqs)
                                            if idx_r != reqs.index(r_sel) and r.gamma == 2
                                            for idx_w,w in enumerate(r.V_R)
                                            for f in range(F_MAX)
                                            for k in range(K_MAX)) == 0]
                
                if len(V_P_R_REM_TMP) == 0:
                    print(f"infeasible: No remaining NR-BS for mapping RU {w_sel} of SR {r_sel}")
                    feasible = 0
                    reject_opt[r_t.gamma] = 1
                    break
    
                q_sel = 0
                f_sel = 0
                k_sel = 0
                
                found = 0
                for q in V_P_R_REM_TMP:
                    for f in range(len(q.Pi_MAX)):
                        for k in range(K_REQ_EFF[idx_r_sel][idx_w_sel], 0, -1):
                            pi_used = (sum(k1 * y[idx_r1][idx_w1][V_P_R.index(q)][f][k1]
                                            for idx_r1, r1 in enumerate(reqs)
                                            for idx_w1, w1 in enumerate(r1.V_R)
                                            for k1 in range(1, K_REQ_EFF[idx_r1][r1.V_R.index(w1)] + 1)
                                           ) * sys.Pi_PRB
                                      + sum(y[idx_r1][idx_w1][V_P_R.index(q)][f][k1]
                                            for idx_r1, r1 in enumerate(reqs)
                                            if (r1.gamma == 1)
                                            for idx_w1, w1 in enumerate(r1.V_R)
                                            for k1 in range(1, K_REQ_EFF[idx_r1][r1.V_R.index(w1)] + 1)
                                           ) * sys.Pi_FGB
                                       + k * sys.Pi_PRB
                                       + (r_sel.gamma == 1) * sys.Pi_FGB
                                      )
                            if pi_used <= q.Pi_MAX[f]:
                                q_sel = q
                                f_sel = f
                                k_sel = k
    
                                if r_sel.gamma == 2:
                                    V_P_R_DEL.append(q_sel)
    
                                found = 1
                                break
                            elif (q_sel == 0) and (k == 1) and (V_P_R_REM.index(q) == (len(V_P_R_REM) - 1)) and (f == (len(q.Pi_MAX) - 1)):
                                print(f"infeasible: Checked all possible NR-BSs. No remaining NR-BS for mapping RU {w_sel} of SR {r_sel}")
                                feasible = 0
                                reject_opt[r_t.gamma] = 1
                                break
                        if found:
                            break
                    if found:
                        break
                                
                V_R_REM = [w for w in V_R_REM if (r_sel.V_R).index(w) != (r_sel.V_R).index(w_sel)]    
                V_P_R_REM = [w for w in V_P_R_REM if w not in V_P_R_DEL]
                if feasible:
                    y[reqs.index(r_sel)][(r_sel.V_R).index(w_sel)][V_P_R.index(q_sel)][f_sel][k_sel] = 1
    
            ### Continue with mapping NFs if the previous step was successful
            if feasible:
                V_S_REM = r_sel.V_S.copy()
                
                for v in V_S_REM:
                    V_P_S_REM_TMP = V_P_S_REM.copy()
                    v_sel         = max(V_S_REM, key=lambda nf: nf.C_REQ)
                    
                    if r_sel.gamma == 2: ## Complete Isolation
                        V_P_S_REM_TMP = [p for p in V_P_S_REM
                                         if sum(x[idx_r][idx_v][V_P_S.index(p)]
                                                for idx_r,r in enumerate(reqs)
                                                if idx_r != reqs.index(r_sel)
                                                for idx_v,v in enumerate(r.V_S)) == 0]
                        
                    if len(V_P_S_REM_TMP) == 0:
                        print(f"infeasible: No remaining PS for mapping NF {v_sel} of SR {r_sel}")
                        feasible = 0
                        reject_opt[r_t.gamma] = 1
                        break
                        
                    P_list = [e_p.p for e_p in E_P
                              if e_p.q in V_P_R
                              if V_P_R.index(e_p.q) == V_P_R.index(q_sel)]
    
                    V_P_S_REM_TMP = [p for p in P_list if p in V_P_S_REM_TMP]
                    p_sel = max(V_P_S_REM_TMP, key=lambda ps: ps.C_MAX)
    
                    x[reqs.index(r_sel)][(r_sel.V_S).index(v_sel)][V_P_S.index(p_sel)] = 1
    
                    if r_sel.gamma == 2:
                        V_P_S_DEL.append(p_sel)
                    V_S_REM = [v for v in V_S_REM if (r_sel.V_S).index(v) != (r_sel.V_S).index(v_sel)]
                
                ## Remove that server for other slice requests
                V_P_S_REM = [p for p in V_P_S_REM if (p in V_P_S_DEL) == 0]
        else:
            v_sel = idx_r_sel

        ### Continue with mapping VPs if the previous step was successful
        if feasible:
            E_REM   = r_sel.E.copy()
            E_P_REM = E_P
            E_P_DEL = []
            for e in E_REM:
                e_sel   = max(r_sel.E, key=lambda vpath: B_REQ_EFF[idx_r_sel][r_sel.E.index(vpath)])
                
                v_e_sel = e_sel.v
                w_e_sel = e_sel.w

                p_e_sel = V_P_S[x[idx_r_sel][r_sel.V_S.index(e_sel.v)].index(1)]

                y_array = np.array(y[idx_r_sel][r_sel.V_R.index(e_sel.w)])
                index   = np.argwhere(y_array == 1)[0]
                q_e_sel = V_P_R[index[0]]
                
                E_P_REM_SEARCH = [e_p for e_p in E_P_REM
                                  if (e_p.p in V_P_S) and (e_p.q in V_P_R)]
                E_P_REM_SEARCH = [e_p for e_p in E_P_REM_SEARCH
                                  if (V_P_S.index(e_p.p) == V_P_S.index(p_e_sel)) and (V_P_R.index(e_p.q) == V_P_R.index(q_e_sel))]
                
                if len(E_P_REM_SEARCH) == 0:
                    print(f"infeasible: No remaining PP for mapping VP {v_e_sel} of SR {r_sel}")
                    feasible = 0
                    reject_opt[r_t.gamma] = 1
                    break

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
                                   for k in range(K_REQ_EFF[idx_r_sel][r_sel.V_R.index(e.v)] + 1)) == 1):
                                if(sum(y[reqs.index(r_sel)][(r_sel.V_R).index(e_sel.v)][V_P_R.index(q)][f][k]
                                       for f in range(len(q.Pi_MAX))
                                       for k in range(K_REQ_EFF[idx_r_sel][r_sel.V_R.index(e.v)] + 1)) == 1):
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

    end_time1 = time.perf_counter()

    print(f"end_time1-start_time1:{(end_time1-start_time1)}")
    
    #print(f"x={x}")
    #print(f"y={y}")
    #print(f"z={z}")

    if feasible:
    ############# 5G-INS ##############
        # Decision Variables
        ## Main Variables
        c.append([[m.addVar(name=f"c_{len_R-1}_{idx_v}_{idx_p}", vtype=gp.GRB.CONTINUOUS)
                   for idx_p in range(len_V_P_S)]
                  for idx_v in range(len_V_S)])
        b.append([[[[m.addVar(name=f"b_{len_R-1}_{idx_e}_{idx_e_p}_{idx_l}_{s}", vtype=gp.GRB.CONTINUOUS)
                     for s in range(S_MAX)]
                    for idx_l in range(len_L_pqi)]
                   for idx_e_p in range(len_E_P)]
                  for idx_e in range(len_E)])

        m.setParam('Threads', 4)
        
        m.update()

        # Constraints
        ###################################### Node Mapping Constraints ######################################
        # Eq. 13
        h_VM_L0 = [sum(x[idx_r][idx_v][idx_p]
                      for idx_r, r in enumerate(reqs)
                      for idx_v, v in enumerate(r.V_S)
                      for xi       in range(1,v.Xi_REQ)
                      if  (r.gamma == 0) and (r.kappa == 0) and (v.Chi_REQ[xi] == (sys.CHI_MAX - 1))
                     ) / p.Xi_MAX[0]
                  + sum(max(((v.Chi_REQ[xi] == chi) * x[idx_r][idx_v][idx_p]
                            for idx_r, r in enumerate(reqs)
                            if (r.gamma == 0) and (r.kappa == 0)
                            for idx_v, v in enumerate(r.V_S)
                            for xi in range(v.Xi_REQ))
                           , default=0)
                        for chi in range(sys.CHI_MAX)
                       ) / p.Xi_MAX[0]
                  + sum(v.Xi_REQ * x[idx_r][idx_v][idx_p]
                        for idx_r, r in enumerate(reqs)
                        if (r.gamma == 0) and (r.kappa == 1)
                        for idx_v, v in enumerate(r.V_S)
                       ) / p.Xi_MAX[0] + 1 ## Plus 1 is the simplification of the ceiling function
                  for idx_p, p in enumerate(V_P_S)
                 ]
        
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
    
        # Eq. 15
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
                + sys.C_HHO * max(x[idx_r][idx_v][idx_p] * (r.gamma <= 1)
                                  for idx_r, r in enumerate(reqs)
                                  for idx_v, v in enumerate(r.V_S)
                                 )
                + sys.C_GOS * sum(v.Xi_REQ * x[idx_r][idx_v][idx_p] * (r.gamma == 1)
                                  for idx_r, r in enumerate(reqs)
                                  for idx_v, v in enumerate(r.V_S)
                                 )
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
                h_VM_L0[idx_p]
                + gp.quicksum(v.Xi_REQ * x[idx_r][idx_v][idx_p]
                              for idx_r, r in enumerate(reqs)
                              if r.gamma == 1
                              for idx_v, v in enumerate(r.V_S)
                             )
                <= p.Xi_MAX[1],
                name=f"mips_max_limit_2_{idx_p}"
            )
    
        # Eq. 19
        for idx_q, q in enumerate(V_P_R):
            for f in range(len(q.Pi_MAX)):
                if len_R >= 2:
                    constraint_to_remove = m.getConstrByName(f"radio_max_limit_{idx_q}_{f}")
                    if constraint_to_remove is not None:
                        m.remove(constraint_to_remove)
                
                m.addConstr(
                    gp.quicksum(k * y[idx_r][idx_w][idx_q][f][k]
                                for idx_r, r in enumerate(reqs)
                                if r.beta < 1e6
                                for idx_w, w in enumerate(r.V_R)
                                for k in range(1, K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                               ) * sys.Pi_PRB
                    + gp.quicksum(y[idx_r][idx_w][idx_q][f][k]
                                  for idx_r, r in enumerate(reqs)
                                  if  r.gamma == 1
                                  for idx_w, w in enumerate(r.V_R)
                                  for k in range(1, K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                 ) * sys.Pi_FGB
                    <= q.Pi_MAX[f],
                    name=f"radio_max_limit_{idx_q}_{f}"
                )
    
        ###################################### Link Mapping Constraints ######################################
        ## Revisitation
        h_REV_1 = [[1 - sum(min(x[idx_r][(r.V_S).index(e.v)][idx_p], x[idx_r][(r.V_S).index(e.w)][idx_p])
                          for idx_p, p in enumerate(V_P_S)
                         )
                  if  isinstance(e.v, nf) and isinstance(e.w, nf) else 0
                  for idx_e, e in enumerate(r.E)
                 ]
                 for idx_r, r in enumerate(reqs)
                ]
        h_REV_2 = [[1 - sum(min(sum(y[idx_r][(r.V_R).index(e.v)][idx_q][f][k]
                                  for f in range(len(q.Pi_MAX))
                                  for k in range(K_REQ_EFF[idx_r][r.V_R.index(e.v)] + 1)
                                 ),
                              sum(y[idx_r][r.V_R.index(e.w)][idx_q][f][k]
                                  for f in range(len(q.Pi_MAX))
                                  for k in range(1,K_REQ_EFF[idx_r][r.V_R.index(e.w)] + 1)
                                 )
                             )
                          for idx_q, q in enumerate(V_P_R)
                         )
                  if  isinstance(e.v, ru) and isinstance(e.w, ru) else 0
                  for idx_e, e in enumerate(r.E)
                 ]
                 for idx_r, r in enumerate(reqs)
                ]
    
        # Eq. 27
        h_B_h_1 = [
            [
                (sys.Psi_HDR * (r.gamma == 0) - 1)
                * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                              for idx_e_p, e_p in enumerate(E_P)
                              if isinstance(e_p.p, ps) and isinstance(e_p.q, ps)
                              for s in range(S_MAX)
                             )
                + B_REQ_EFF[idx_r][idx_e] * h_REV_1[idx_r][idx_e]
                for idx_e, e in enumerate(r.E)
            ]
            for idx_r, r in enumerate(reqs)
        ]
        h_B_h_2 = [
            [
                (sys.Psi_HDR * (r.gamma == 0) - 1)
                * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                              for idx_e_p, e_p in enumerate(E_P)
                              if (e_p.p in V_P_R) and (e_p.q in V_P_R)
                              for s in range(S_MAX)
                             )
                + B_REQ_EFF[idx_r][idx_e] * h_REV_2[idx_r][idx_e]
                for idx_e, e in enumerate(r.E)
            ]
            for idx_r, r in enumerate(reqs)
        ]  
        h_B_h_3 = [
            [
                (sys.Psi_HDR * (r.gamma == 0) - 1)
                * gp.quicksum(b[idx_r][idx_e][idx_e_p][0][s]
                              for idx_e_p, e_p in enumerate(E_P)
                              if (e_p.p in V_P_S) and (e_p.q in V_P_R)
                              for s in range(S_MAX)
                             )
                + B_REQ_EFF[idx_r][idx_e]
                for idx_e, e in enumerate(r.E)
            ]
            for idx_r, r in enumerate(reqs)
        ]

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
                            (1 - sys.Psi_HDR * (reqs[idx_r].gamma == 0))
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
                            (1 - sys.Psi_HDR * (reqs[idx_r].gamma == 0))
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
                            (1 - sys.Psi_HDR * (reqs[idx_r].gamma == 0))
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
                            (1 - sys.Psi_HDR * (reqs[idx_r].gamma == 0))
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
                            (1 - sys.Psi_HDR * (reqs[idx_r].gamma == 0))
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
                    gp.quicksum(z[idx_r][idx_e][idx_l][s] * sys.B_WGB
                                for idx_r, r in enumerate(reqs)
                                if  r.gamma == 1
                                for idx_e, e in enumerate(r.E)
                                for idx_e_p, e_p in enumerate(E_P)
                                if e_p in E_P_l[idx_l]
                    )
                    + gp.quicksum(b[idx_r][idx_e][idx_e_p][L_pqi[idx_e_p].index(l)][s]
                                  for idx_r, r in enumerate(reqs)
                                  for idx_e, e in enumerate(r.E)
                                  for idx_e_p, e_p in enumerate(E_P)
                                  if e_p in E_P_l[idx_l]
                    ) <= l.B_MAX[s],
                    name=f"bandwidth_max_limit_{idx_l}_{s}"
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
        g_D_1 = sum(r.rho_D * max(max(min(e_p.D_RTT * sum(z[idx_r][idx_e][idx_l][s]
                                                    for s in range(len(l.B_MAX))
                                                   ) - e.D_REQ - M * h_REV_1[idx_r][idx_e]
                                      for idx_l, l in enumerate(L)
                                     )
                                  for idx_e_p, e_p in enumerate(E_P)
                                 ), 0)
                    for idx_r, r in enumerate(reqs)
                    for idx_e, e in enumerate(r.E)
                    if  (e.v in r.V_S) and (e.w in r.V_S)
                   )
        g_D_2 = sum(r.rho_D * max(max(min(e_p.D_RTT * sum(z[idx_r][idx_e][idx_l][s]
                                                    for s in range(len(l.B_MAX))
                                                   ) - e.D_REQ - M * h_REV_2[idx_r][idx_e]
                                      for idx_l, l in enumerate(L)
                                     )
                                  for idx_e_p, e_p in enumerate(E_P)
                                 ), 0)
                    for idx_r, r in enumerate(reqs)
                    for idx_e, e in enumerate(r.E)
                    if  (e.v in r.V_R) and (e.w in r.V_R)
                   )
        g_D_3 = sum(r.rho_D * max(max(min(e_p.D_RTT * sum(z[idx_r][idx_e][idx_l][s]
                                                          for s in range(len(l.B_MAX))
                                                         ) - e.D_REQ
                                      for idx_l, l in enumerate(L)
                                     )
                                  for idx_e_p, e_p in enumerate(E_P)
                                 ), 0)
                    for idx_r, r in enumerate(reqs)
                    for idx_e, e in enumerate(r.E)
                    if  (e.v in r.V_S) and (e.w in r.V_R)
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
        g_K = sum(r.rho_K * (K_REQ_EFF[idx_r][r.V_R.index(w)] - sum(k * y[idx_r][idx_w][idx_q][f][k]
                                           for idx_q, q in enumerate(V_P_R)
                                           for f in range(len(q.Pi_MAX))
                                           for k in range(K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                          )
                            )
                  for idx_r, r in enumerate(reqs)
                  for idx_w, w in enumerate(r.V_R)
                 )

        # Violation Cost
        g_vio = g_D_1 + g_D_2 + g_D_3 + g_C + g_K + g_B_1 + g_B_2 + g_B_3
        
        # Deployment Costs
        g_dep = ( sys.Theta * gp.quicksum(b[idx_r][idx_e][idx_e_p][idx_l][s]
                                          for idx_r, r     in enumerate(reqs)
                                          if  r.gamma < 2
                                          for idx_e, e     in enumerate(r.E)
                                          for idx_e_p, e_p in enumerate(E_P)
                                          for idx_l, l     in enumerate(L_pqi[idx_e_p])
                                          for s            in range(S_MAX)
                                         )
                + sys.Omega * gp.quicksum(c[idx_r][idx_v][idx_p]
                                          for idx_r, r in enumerate(reqs)
                                          if  r.gamma < 2
                                          for idx_v, v in enumerate(r.V_S)
                                          for idx_p, p in enumerate(V_P_S)
                                         )
                + sys.Phi   * sum(k * y[idx_r][idx_w][idx_q][f][k]
                                  for idx_r, r in enumerate(reqs)
                                  if  r.gamma < 2
                                  for idx_w, w in enumerate(r.V_R)
                                  for idx_q, q in enumerate(V_P_R)
                                  for f in range(len(q.Pi_MAX))
                                  for k in range(K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                 )
                + sys.Theta * sum(l.B_MAX[0] * max((sum(z[idx_r][idx_e][idx_l][s]
                                                        for s in range(S_MAX))
                                                   for idx_e, e in enumerate(r.E))
                                                  , default=0)
                                  for idx_r, r in enumerate(reqs)
                                  if r.gamma == 2
                                  for idx_l, l in enumerate(L)
                                 )

                + sys.Omega * sum(p.C_MAX * max((x[idx_r][idx_v][idx_p]
                                                for idx_v, v in enumerate(r.V_S))
                                               , default=0)
                                  for idx_r, r in enumerate(reqs)
                                  if  r.gamma == 2
                                  for idx_p, p in enumerate(V_P_S)
                                 )
                + sys.Phi * sum(q.Pi_MAX[0] / sys.Pi_PRB * max((sum(y[idx_r][idx_w][idx_q][f][k]
                                                                   for f in range(len(q.Pi_MAX))
                                                                   for k in range(K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                                                  )
                                                               for idx_w, w in enumerate(r.V_R))
                                                              , default=0)
                                for idx_r, r in enumerate(reqs)
                                if  r.gamma == 2
                                for idx_q, q in enumerate(V_P_R)
                               )
                )

        # Eq. 31
        g_mig = (sum(sum(r.beta * x[idx_r][idx_v][idx_p]
                         for idx_p, p in enumerate(V_P_S)
                         if(len(X_t))
                         if(X_t[idx_r][idx_v][idx_p] == 0)
                        )
                     for idx_r, r in enumerate(R_t)
                     for idx_v, v in enumerate(r.V_S)
                    )
                + sum(sum(r.beta * sum(y[idx_r][idx_w][idx_q][f][k]
                                       for f in range(len(q.Pi_MAX))
                                       for k in range(1, K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                      )
                          for idx_q, q in enumerate(V_P_R)
                          if(len(Y_t))
                          if(sum(Y_t[idx_r][idx_w][idx_q][f][k]
                                 for f in range(len(q.Pi_MAX))
                                 for k in range(1, K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                ) == 0)
                         )
                      for idx_r, r in enumerate(R_t)
                      for idx_w, w in enumerate(r.V_R)
                     )
                )

        # Overhead Cost
        g_ovh = ( sys.Theta * sum(z[idx_r][idx_e][idx_l][s] * sys.B_WGB
                                  for idx_r, r in enumerate(reqs)
                                  if r.gamma == 1
                                  for idx_e, e in enumerate(r.E)
                                  for idx_l, l in enumerate(L)
                                  for s in range(S_MAX)
                                 )
                + sys.Omega * gp.quicksum((sys.C_K8S + sys.C_GOS) * (h_VM_L0[idx_p] - 1)
                                           + sys.C_HHO * max((x[idx_r][idx_v][idx_p] * (r.gamma <= 1)
                                                             for idx_r, r in enumerate(reqs)
                                                             for idx_v, v in enumerate(r.V_S))
                                                            , default=0)
                                           + sys.C_GOS * gp.quicksum(v.Xi_REQ * x[idx_r][idx_v][idx_p]
                                                                     for idx_r, r in enumerate(reqs)
                                                                     if r.gamma == 1
                                                                     for idx_v, v in enumerate(r.V_S)
                                                                    )
                                          for idx_p, p in enumerate(V_P_S)
                                         )
                + sys.Phi   * sum(sys.Pi_FGB * y[idx_r][idx_w][idx_q][f][k]
                                  for idx_r, r in enumerate(reqs)
                                  if  r.gamma == 1
                                  for idx_w, w in enumerate(r.V_R)
                                  for idx_q, q in enumerate(V_P_R)
                                  for f in range(len(q.Pi_MAX))
                                  for k in range(K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                 )
                )

        if len_R >= 2:
            constraint_to_remove = m.getConstrByName(f"minimum_profit")
            if constraint_to_remove is not None:
                m.remove(constraint_to_remove)

        # Eq. 32
        m.addConstr(
            (
                (sum(r.R for r in reqs) - g_dep - g_vio - g_mig - g_ovh - profit_prev) >= P_min
            ), name="minimum_profit"
        )
    
        m.update()

        m.setObjective(sum(r.R for r in reqs) - g_dep - g_vio - g_mig - g_ovh, GRB.MAXIMIZE)
    
        # Start the timer
        start_time2 = time.perf_counter()
        
        timeout = 0
        try:
            m = run_with_timeout(r_t.timeout, timeout_optimize, m)
        except TimeoutException as e:
            timeout = 1
        
        # Stop the timer
        end_time2 = time.perf_counter()
        timer = (end_time2 - start_time2) + (end_time1 - start_time1)
    
        status = m.status

        # Determine feasibility based on the status
        if (status == gp.GRB.OPTIMAL) and (timeout == 0):
            feasible = 1
    
            # Get the optimal values of variables
            vars_opt = {var.varName: var.x for var in m.getVars()}

            h_B_h_1 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                             for idx_e_p, e_p in enumerate(E_P)
                                                             if  (e_p.p in V_P_S) and (e_p.q in V_P_S)
                                                             #for idx_l, l     in enumerate(L_pqi[idx_e_p])
                                                             for s            in range(S_MAX)
                                                            ) + B_REQ_EFF[idx_r][idx_e] * h_REV_1[idx_r][idx_e]
                        for idx_e, e in enumerate(r.E)
                        #if  (e.v in r.V_S) and (e.w in r.V_S)
                       ]
                       for idx_r, r in enumerate(reqs)
                      ]
            h_B_h_2 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                             for idx_e_p, e_p in enumerate(E_P)
                                                             if  (e_p.p in V_P_R) and (e_p.q in V_P_R)
                                                             for s            in range(S_MAX)
                                                            ) + B_REQ_EFF[idx_r][idx_e] * h_REV_2[idx_r][idx_e]
                        for idx_e, e in enumerate(r.E)
                        #if  (e.v in r.V_R) and (e.w in r.V_R)
                       ]
                       for idx_r, r in enumerate(reqs)
                      ]
            h_B_h_3 = [[(sys.Psi_HDR*(r.gamma == 0) - 1)*sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                                             for idx_e_p, e_p in enumerate(E_P)
                                                             if  (e_p.p in V_P_S) and (e_p.q in V_P_R)
                                                             for s            in range(S_MAX)
                                                            ) + B_REQ_EFF[idx_r][idx_e]
                        for idx_e, e in enumerate(r.E)
                        #if  (e.v in r.V_S) and (e.w in r.V_R)
                       ]
                       for idx_r, r in enumerate(reqs)
                      ]

            h_B_h_3_tmp = [[sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,0,s)]
                                 for idx_e_p, e_p in enumerate(E_P)
                                 if  (e_p.p in V_P_S) and (e_p.q in V_P_R)
                                 for s            in range(S_MAX)
                                )
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
            g_B_3_opt = sum(h_B_h_3[idx_r][idx_e]
                            for idx_r, r in enumerate(reqs)
                            for idx_e, e in enumerate(r.E)
                            if (e.v in r.V_S) and (e.w in r.V_R)
                           )

            g_B_opt = g_B_1_opt + g_B_2_opt + g_B_3_opt

            g_C_opt = sum(r.rho_C * (v.C_REQ - sum(vars_opt["c_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                                                   for idx_p, p in enumerate(V_P_S)
                                                  )
                                    )
                      for idx_r, r in enumerate(reqs)
                      for idx_v, v in enumerate(r.V_S)
                     )

            g_D_opt = g_D_1 + g_D_2 + g_D_3

            g_K_opt = g_K
    
            # Violation Cost
            g_vio_opt = g_D_opt + g_C_opt + g_K_opt + g_B_opt


            g_dep_K_opt = (sys.Phi * sum(k * y[idx_r][idx_w][idx_q][f][k]
                                        for idx_r, r in enumerate(reqs)
                                        if  r.gamma < 2
                                        for idx_w, w in enumerate(r.V_R)
                                        for idx_q, q in enumerate(V_P_R)
                                        for f in range(len(q.Pi_MAX))
                                        for k in range(K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                       )
                        + sys.Phi * sum(q.Pi_MAX[0] / sys.Pi_PRB * max((sum(y[idx_r][idx_w][idx_q][f][k]
                                                                            for f in range(len(q.Pi_MAX))
                                                                            for k in range(K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                                                           )
                                                                       for idx_w, w in enumerate(r.V_R))
                                                                      , default=0)
                                        for idx_r, r in enumerate(reqs)
                                        if  r.gamma == 2
                                        for idx_q, q in enumerate(V_P_R)
                                       )
                        )

            g_dep_B_opt = (sys.Theta * sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,idx_l,s)]
                                         for idx_r, r     in enumerate(reqs)
                                         if  r.gamma < 2
                                         for idx_e, e     in enumerate(r.E)
                                         for idx_e_p, e_p in enumerate(E_P)
                                         for idx_l, l     in enumerate(L_pqi[idx_e_p])
                                         for s            in range(len(l.B_MAX))
                                        )
                        + sys.Theta * sum(l.B_MAX[0] * max((sum(z[idx_r][idx_e][idx_l][s]
                                                                for s in range(S_MAX))
                                                           for idx_e, e in enumerate(r.E))
                                                          , default=0)
                                          for idx_r, r in enumerate(reqs)
                                          if r.gamma == 2
                                          for idx_l, l in enumerate(L)
                                         )
                        )

            g_dep_C_opt = (sys.Omega * sum(vars_opt["c_{}_{}_{}".format(idx_r,idx_v,idx_p)]
                                          for idx_r, r in enumerate(reqs)
                                          if  r.gamma < 2
                                          for idx_v, v in enumerate(r.V_S)
                                          for idx_p, p in enumerate(V_P_S)
                                         )
                        + sys.Omega * sum(p.C_MAX * max((x[idx_r][idx_v][idx_p]
                                                        for idx_v, v in enumerate(r.V_S))
                                                       , default=0)
                                          for idx_r, r in enumerate(reqs)
                                          if  r.gamma == 2
                                          for idx_p, p in enumerate(V_P_S)
                                         )
                        )
            
            g_dep_opt = g_dep_K_opt + g_dep_B_opt + g_dep_C_opt

            g_ovh_C_opt = ( sys.Omega * gp.quicksum((sys.C_K8S + sys.C_GOS) * h_VM_L0[idx_p]
                                                   + sys.C_HHO * max((x[idx_r][idx_v][idx_p] * (r.gamma <= 1)
                                                                     for idx_r, r in enumerate(reqs)
                                                                     for idx_v, v in enumerate(r.V_S))
                                                                    , default=0)
                                                   + sys.C_GOS * gp.quicksum(v.Xi_REQ * x[idx_r][idx_v][idx_p]
                                                                             for idx_r, r in enumerate(reqs)
                                                                             if r.gamma == 1
                                                                             for idx_v, v in enumerate(r.V_S)
                                                                            )
                                                  for idx_p, p in enumerate(V_P_S)
                                                 )
                         )

            g_ovh_K_opt = ( sys.Phi * sum(sys.Pi_FGB * y[idx_r][idx_w][idx_q][f][k]
                                          for idx_r, r in enumerate(reqs)
                                          if  r.gamma == 1
                                          for idx_w, w in enumerate(r.V_R)
                                          for idx_q, q in enumerate(V_P_R)
                                          for f in range(len(q.Pi_MAX))
                                          for k in range(K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                         )
                          )

            g_ovh_B_opt = ( sys.Theta * sum(z[idx_r][idx_e][idx_l][s] * sys.B_WGB
                                                for idx_r, r in enumerate(reqs)
                                                if r.gamma == 1
                                                for idx_e, e in enumerate(r.E)
                                                for idx_l, l in enumerate(L)
                                                for s in range(S_MAX)
                                               )
                              )
    
            g_mig_opt = g_mig

            ############################## Overhead Costs ##############################
            h_VM_L0 = [math.ceil(sum(x[idx_r][idx_v][idx_p]
                          for idx_r, r in enumerate(reqs)
                          for idx_v, v in enumerate(r.V_S)
                          for xi       in range(1,v.Xi_REQ)
                          if  (r.gamma == 0) and (r.kappa == 0) and (v.Chi_REQ[xi] == (sys.CHI_MAX - 1))
                         ) / p.Xi_MAX[0]
                      + sum(max(((v.Chi_REQ[xi] == chi) * x[idx_r][idx_v][idx_p]
                                for idx_r, r in enumerate(reqs)
                                if (r.gamma == 0) and (r.kappa == 0)
                                for idx_v, v in enumerate(r.V_S)
                                for xi in range(v.Xi_REQ))
                               , default=0)
                            for chi in range(sys.CHI_MAX)
                           ) / p.Xi_MAX[0]
                      + sum(v.Xi_REQ * x[idx_r][idx_v][idx_p]
                            for idx_r, r in enumerate(reqs)
                            if (r.gamma == 0) and (r.kappa == 1)
                            for idx_v, v in enumerate(r.V_S)
                           ) / p.Xi_MAX[0]) 
                      for idx_p, p in enumerate(V_P_S)
                     ]
    
            g_ovh_K_opt = (sys.Phi   * sum(sys.Pi_FGB * y[idx_r][idx_w][idx_q][f][k]
                                          for idx_r, r in enumerate(reqs)
                                          if  r.gamma == 1
                                          for idx_w, w in enumerate(r.V_R)
                                          for idx_q, q in enumerate(V_P_R)
                                          for f in range(len(q.Pi_MAX))
                                          for k in range(K_REQ_EFF[idx_r][idx_w] + 1)
                                         )
                        )
    
            g_ovh_B_opt = ( sys.Theta * sum(z[idx_r][idx_e][idx_l][s] * sys.B_WGB
                                          for idx_r, r in enumerate(reqs)
                                          if  r.gamma == 1
                                          for idx_e, e in enumerate(r.E)
                                          for idx_l, l in enumerate(L)
                                          for s in range(S_MAX)
                                         )
                        )

            g_ovh_C_opt = ( sys.Omega * sum((sys.C_K8S + sys.C_GOS) * h_VM_L0[idx_p]
                                           + sys.C_HHO * max((x[idx_r][idx_v][idx_p] * (r.gamma <= 1)
                                                             for idx_r, r in enumerate(reqs)
                                                             for idx_v, v in enumerate(r.V_S))
                                                            , default=0)
                                           + sys.C_GOS * sum(v.Xi_REQ * x[idx_r][idx_v][idx_p]
                                                             for idx_r, r in enumerate(reqs)
                                                             if r.gamma == 1
                                                             for idx_v, v in enumerate(r.V_S)
                                                            )
                                          for idx_p, p in enumerate(V_P_S)
                                         )
                         )
    
            g_ovh_opt = g_ovh_K_opt + g_ovh_B_opt + g_ovh_C_opt
    
            ############################## Resource Efficiency ##############################
            sum_K_REQ = sum(K_REQ_EFF[idx_r][idx_w]
                            for idx_r, r in enumerate(reqs)
                            for idx_w, w in enumerate(r.V_R)
                           ) * sys.Phi
            g_res_K_opt = min([sum_K_REQ / (g_dep_K_opt + g_ovh_K_opt), 1]) * 100
    
            sum_B_REQ = sum(B_REQ_EFF[idx_r][idx_e]
                            for idx_r, r     in enumerate(reqs)
                            for idx_e, e     in enumerate(r.E)
                            if sum(vars_opt["b_{}_{}_{}_{}_{}".format(idx_r,idx_e,idx_e_p,idx_l,s)]
                                   for idx_e_p, e_p in enumerate(E_P)
                                   for idx_l, l     in enumerate(L_pqi[idx_e_p])
                                   for s            in range(len(l.B_MAX))
                                  ) != 0
                               ) * sys.Theta
            g_res_B_opt = min([sum_B_REQ / (g_dep_B_opt + g_ovh_B_opt), 1]) * 100
    
            sum_C_REQ = sum(v.C_REQ
                            for idx_r, r in enumerate(reqs)
                            for idx_v, v in enumerate(r.V_S)
                           ) * sys.Omega
            g_res_C_opt = min([sum_C_REQ / (g_dep_C_opt + g_ovh_C_opt), 1]) * 100
            
            g_res_opt = (g_res_K_opt + g_res_B_opt + g_res_C_opt) / 3

            profit = sum(r.R for r in reqs) - g_dep_opt - g_vio_opt - g_mig_opt - g_ovh_opt #m.objVal
    
            n_mig_opt = (sum(sum(x[idx_r][idx_v][idx_p]
                                for idx_p, p in enumerate(V_P_S)
                                if(len(X_t))
                                if(X_t[idx_r][idx_v][idx_p] == 0)
                               )
                            for idx_r, r in enumerate(R_t)
                            for idx_v, v in enumerate(r.V_S)
                           )
                        + sum(sum(sum(y[idx_r][idx_w][idx_q][f][k]
                                      for f in range(len(q.Pi_MAX))
                                      for k in range(1, K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                      )
                                       for idx_q, q in enumerate(V_P_R)
                                       if(len(Y_t))
                                       if(sum(Y_t[idx_r][idx_w][idx_q][f][k]
                                              for f in range(len(q.Pi_MAX))
                                              for k in range(1, K_REQ_EFF[idx_r][r.V_R.index(w)] + 1)
                                             ) == 0
                                         )
                                      )
                                   for idx_r, r in enumerate(R_t)
                                   for idx_w, w in enumerate(r.V_R)
                                  ))
    
            X_t = [[[x[idx_r][idx_v][idx_p]
                     for idx_p, p in enumerate(V_P_S)]
                    for idx_v, v in enumerate(r.V_S)]
                   for idx_r, r in enumerate(reqs)]
            Y_t = [[[[[y[idx_r][idx_w][idx_q][f][k]
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
            reqs.pop()
            len_R = len(reqs)

            if f_fgr:
                m = gp.read(f'saved_model/model_backup_fgr_iar_{iter}.mps')
            else:
                m = gp.read(f'saved_model/model_backup_iar_{iter}.mps')
            m.update()
            
            reject_opt[r_t.gamma] = 1
            feasible = 0

    else:
        print("Infeasible Problem")
        
        reqs.pop()
        len_R = len(reqs)

        if f_fgr:
            m = gp.read(f'saved_model/model_backup_fgr_iar_{iter}.mps')
        else:
            m = gp.read(f'saved_model/model_backup_iar_{iter}.mps')
        m.update()
        
        reject_opt[r_t.gamma] = 1
        feasible = 0

    # Stop the timer
    time_opt = timer

    if time_opt > r_t.timeout:
        timeout  = 1
        feasible = 0
        reject_opt[r_t.gamma] = 1

        if len(reqs):
            reqs.pop()
            len_R = len(reqs)
            
            if f_fgr:
                m = gp.read(f'saved_model/model_backup_fgr_iar_{iter}.mps')
            else:
                m = gp.read(f'saved_model/model_backup_iar_{iter}.mps')
            m.update()

    if f_fgr == 0:
        if feasible:
            data = [
                ["Algorithm", "IAR"],
                ["Request Isolation Level", f"({r_t.gamma}, {r_t.kappa})"],
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
                ["Algorithm", "IAR"],
                ["Request Isolation Level", f"({r_t.gamma}, {r_t.kappa})"],
                ["Allocation Time", time_opt],
                ["Feasible", feasible],
                ["Timeout", timeout]
            ]
    
        print(tabulate(data, headers=["Category", "Value"], tablefmt="grid"))

    m.update()
    if f_fgr:
        m.write(f'saved_model/model_backup_fgr_iar_{iter}.mps')
    else:
        m.write(f'saved_model/model_backup_iar_{iter}.mps')
    
    return [profit_opt, violat_opt, migrat_opt, deploy_opt, overhe_opt, reseff_opt, reject_opt.T, time_opt, vars_opt, feasible, timeout, reqs], X_t, Y_t