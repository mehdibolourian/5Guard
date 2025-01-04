from libraries import *

def fguard(slice_list):
    X_t = []
    Y_t = []

    reqs_lp_t = []
    reqs      = []

    profit_arr_bst = np.zeros(SIMULATION_INTERVAL)
    violat_arr_bst = np.zeros(SIMULATION_INTERVAL)
    migrat_arr_bst = np.zeros(SIMULATION_INTERVAL)
    deploy_arr_bst = np.zeros(SIMULATION_INTERVAL)
    reject_arr_bst = np.zeros(SIMULATION_INTERVAL)
    time_arr_bst   = np.zeros(SIMULATION_INTERVAL)
    
    file_path = 'time.pkl'

    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            loaded_lists = pickle.load(file)
            X_t = loaded_lists[2]
            Y_t = loaded_lists[3]
        
            reqs_lp_t = loaded_lists[1]
            reqs      = reqs_lp_t.copy()
    else:
        loaded_lists = [0, reqs_lp_t, X_t, Y_t]

    profit = 0
    for t in range(loaded_lists[0], SIMULATION_INTERVAL):
        print("Time", t)
        r_t = copy.copy(slice_list[t])
        reqs.append(r_t)

        profit_opt, violat_opt, migrat_opt, deploy_opt, reject_opt, time_opt, X_t_opt, Y_t_opt, m_opt = optimal_iter(t, r_t, reqs, reqs_lp_t, X_t, Y_t, profit_arr_bst[t-int(loaded_lists[0])-1], "model_backup_opt.mps")
        profit_grd, violat_grd, migrat_grd, deploy_grd, reject_grd, time_grd, X_t_grd, Y_t_grd, m_grd = ia_ranking_iter(t, r_t, reqs, reqs_lp_t, X_t, Y_t, profit_arr_bst[t-int(loaded_lists[0])-1], "model_backup_grd.mps")
        profit_lpr, violat_lpr, migrat_lpr, deploy_lpr, reject_lpr, time_lpr, X_t_lpr, Y_t_lpr, m_lpr = lp_round_iter(t, r_t, reqs, reqs_lp_t, X_t, Y_t, profit_arr_bst[t-int(loaded_lists[0])-1], "model_backup_lpr.mps")
        profit_rar, violat_rar, migrat_rar, deploy_rar, reject_rar, time_rar, X_t_rar, Y_t_rar, m_rar = random_round_iter(t, r_t, reqs, reqs_lp_t, X_t, Y_t, profit_arr_bst[t-int(loaded_lists[0])-1], "model_backup_rar.mps")

        if (time_opt < r_t.timeout) and (sum(reject_opt) == 0): ## optimal
            profit_arr_bst[t-int(loaded_lists[0])] = profit_opt
            violat_arr_bst[t-int(loaded_lists[0])] = violat_opt
            migrat_arr_bst[t-int(loaded_lists[0])] = migrat_opt
            deploy_arr_bst[t-int(loaded_lists[0])] = deploy_opt
            time_arr_bst[t-int(loaded_lists[0])]   = time_opt
            
            X_t = X_t_opt.copy()
            Y_t = Y_t_opt.copy()
            
            reqs_lp_t.append(r_t)

            m_opt.update()
            m_opt.write("model_backup_opt.mps")
            m_grd.update()
            m_grd.write("model_backup_grd.mps")
            m_lpr.update()
            m_lpr.write("model_backup_lpr.mps")
            m_rar.update()
            m_rar.write("model_backup_rar.mps")
        else: ## Suboptimal
            #print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
            if profit_grd*(time_grd < r_t.timeout)*(1-sum(reject_grd)) or profit_lpr*(time_lpr < r_t.timeout)*(1-sum(reject_lpr)) or profit_rar*(time_rar < r_t.timeout)*(1-sum(reject_rar)):
                a = np.argmax([profit_grd*(time_grd < r_t.timeout)*(1-sum(reject_grd)), profit_lpr*(time_lpr < r_t.timeout)*(1-sum(reject_lpr)), profit_rar*(time_rar < r_t.timeout)*(1-sum(reject_rar))])
                #print(a)
                if a == 0:
                    profit_arr_bst[t-int(loaded_lists[0])] = profit_grd
                    violat_arr_bst[t-int(loaded_lists[0])] = violat_grd
                    migrat_arr_bst[t-int(loaded_lists[0])] = migrat_grd
                    deploy_arr_bst[t-int(loaded_lists[0])] = deploy_grd
                    time_arr_bst[t-int(loaded_lists[0])]   = time_grd
                    
                    X_t = X_t_grd.copy()
                    Y_t = Y_t_grd.copy()

                    m_opt.update()
                    m_opt.write("model_backup_opt.mps")
                    m_grd.update()
                    m_grd.write("model_backup_grd.mps")
                    m_lpr.update()
                    m_lpr.write("model_backup_lpr.mps")
                    m_rar.update()
                    m_rar.write("model_backup_rar.mps")
                    #print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA---------------")
                elif a == 1:
                    profit_arr_bst[t-int(loaded_lists[0])] = profit_lpr
                    violat_arr_bst[t-int(loaded_lists[0])] = violat_lpr
                    migrat_arr_bst[t-int(loaded_lists[0])] = migrat_lpr
                    deploy_arr_bst[t-int(loaded_lists[0])] = deploy_lpr
                    time_arr_bst[t-int(loaded_lists[0])]   = time_lpr
                    
                    X_t = X_t_lpr.copy()
                    Y_t = Y_t_lpr.copy()

                    m_opt.update()
                    m_opt.write("model_backup_opt.mps")
                    m_grd.update()
                    m_grd.write("model_backup_grd.mps")
                    m_lpr.update()
                    m_lpr.write("model_backup_lpr.mps")
                    m_rar.update()
                    m_rar.write("model_backup_rar.mps")
                    #print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA---------------")
                elif a == 2:
                    profit_arr_bst[t-int(loaded_lists[0])] = profit_rar
                    violat_arr_bst[t-int(loaded_lists[0])] = violat_rar
                    migrat_arr_bst[t-int(loaded_lists[0])] = migrat_rar
                    deploy_arr_bst[t-int(loaded_lists[0])] = deploy_rar
                    time_arr_bst[t-int(loaded_lists[0])]   = time_rar
                    
                    X_t = X_t_rar.copy()
                    Y_t = Y_t_rar.copy()

                    m_opt.update()
                    m_opt.write("model_backup_opt.mps")
                    m_grd.update()
                    m_grd.write("model_backup_grd.mps")
                    m_lpr.update()
                    m_lpr.write("model_backup_lpr.mps")
                    m_rar.update()
                    m_rar.write("model_backup_rar.mps")
                    #print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA---------------")
                    
                reqs_lp_t.append(r_t)
            else:
                reqs.pop()
                profit_arr_bst[t-int(loaded_lists[0])] = profit_arr_bst[t-int(loaded_lists[0])-1]
                deploy_arr_bst[t-int(loaded_lists[0])] = deploy_arr_bst[t-int(loaded_lists[0])-1]
                if t != 0:
                    profit_arr_bst[t-int(loaded_lists[0])] = profit_arr_bst[t-int(loaded_lists[0])-1]
                    deploy_arr_bst[t-int(loaded_lists[0])] = deploy_arr_bst[t-int(loaded_lists[0])-1]
                    reject_arr_bst[t-int(loaded_lists[0])] = reject_arr_bst[t-int(loaded_lists[0])-1] + 1
                    if min(time_opt, time_grd, time_lpr, time_rar) > r_t.timeout:
                        time_arr_bst[t-int(loaded_lists[0])]   = r_t.timeout
                    else:
                        time_arr_bst[t-int(loaded_lists[0])]   = time_arr_bst[t-int(loaded_lists[0])-1]
                else:
                    reject_arr_bst[t-int(loaded_lists[0])] = 1
        # Save the lists to a file
    with open('time.pkl', 'wb') as file:
        pickle.dump([SIMULATION_INTERVAL, reqs_lp_t, X_t, Y_t], file)

    return profit_arr_bst, reject_arr_bst, violat_arr_bst, migrat_arr_bst, deploy_arr_bst, time_arr_bst