from libraries import *

def run_opt(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t, Y_t):
    result["opt"] = opt_iter(profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, 1, X_t, Y_t)

def run_iar(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t, Y_t):
    result["iar"] = iar_iter(profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, 1, X_t, Y_t)

def run_dtr(result, LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t, Y_t):
    result["dtr"] = dtr_iter(LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, 1, X_t, Y_t)

def run_rnr(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t, Y_t):
    result["rnr"] = rnr_iter(profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, 1, X_t, Y_t)

def run_in_process(target_function, result, *args):
    target_function(result, *args)

def fgr_iter(LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t, Y_t):
    algs   = ["opt", "iar", "dtr", "rnr"]
    result = {}

    X_t_copy = [copy.deepcopy(X_t) for _ in range(4)]
    Y_t_copy = [copy.deepcopy(Y_t) for _ in range(4)]

    ################ Multi-processing only works on Linux ################

    # manager = multiprocessing.Manager()
    # result = manager.dict()  # Shared dictionary for storing results

    # # Create processes
    # processes = [
    #     multiprocessing.Process(target=run_opt, args=(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t_copy[0], Y_t_copy[0])),
    #     multiprocessing.Process(target=run_iar, args=(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t_copy[1], Y_t_copy[1])),
    #     multiprocessing.Process(target=run_dtr, args=(result, LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, X_t_copy[2], Y_t_copy[2])),
    #     multiprocessing.Process(target=run_rnr, args=(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t_copy[3], Y_t_copy[3]))
    # ]

    # # Start processes
    # for process in processes:
    #     process.start()

    # # Wait for processes to complete with a timeout
    # start_time = time.perf_counter()
    # for process in processes:
    #     remaining_time = r_t.timeout - (time.perf_counter() - start_time)
    #     if remaining_time > 0:
    #         process.join(timeout=remaining_time)
    # end_time = time.perf_counter()
    # print(end_time-start_time)

    # # Ensure processes are terminated if they exceed timeout
    # for process in processes:
    #     if process.is_alive():
    #         process.terminate()
    #         process.join()

    ## For the sake of simulation
    run_opt(result, profit_prev,        iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t_copy[0], Y_t_copy[0])
    run_iar(result, profit_prev,        iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t_copy[1], Y_t_copy[1])
    run_dtr(result, LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t_copy[2], Y_t_copy[2])
    run_rnr(result, profit_prev,        iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, X_t_copy[3], Y_t_copy[3])
        
    ## Profit considering feasibility
    # arr = np.array([result["opt"][0][0],
    #                 result["iar"][0][0],
    #                 result["dtr"][0][0],
    #                 result["rnr"][0][0]])
    arr = np.array([result["opt"][0][0] if result["opt"][0][9]==0 else -math.inf,
                    result["iar"][0][0] if result["iar"][0][9]==0 else -math.inf,
                    result["dtr"][0][0] if result["dtr"][0][9]==0 else -math.inf,
                    result["rnr"][0][0] if result["rnr"][0][9]==0 else -math.inf])

    arr = np.round(arr, 4)  # Round each element to 4 decimal places to avoid numerical errors

    print(f"arr:{arr}")
    print(f"timeout:{result['opt'][0][9]}")
    
    # Create the preference list
    preference_order = [0, 1, 2, 3] #[sorted_indices[val] for val in time_list]

    max_value = np.max(arr)
    max_indices = np.where(arr == max_value)[0]  # Find all indices with max value

    if result['opt'][0][9] == 0: ## OPT hasn't timedout
        alg_idx = 0
        alg     = "opt"
    else:
        # Select the preferred index based on the predefined order
        alg_idx = min(max_indices, key=lambda x: preference_order[x])
        alg     = algs[alg_idx]

    print(f"arr:{arr}")

    result[alg][0][7] = max(result[a][0][7] for a in algs) ## 5Guard should wait for all solutions to become available.

    if result[alg][0][8]: # Feasible
        data = [
            ["Algorithm", alg],
            ["Request Isolation Level", f"({r_t.gamma}, {r_t.kappa})"],
            ["Profit", result[alg][0][0]],
            ["Allocation Time", result[alg][0][7]],
        ]
        if any(result[alg][1]):
            data.append(["Violation Cost", f"{result[alg][0][1][0]}, {result[alg][0][1][1]}, {result[alg][0][1][2]}, {result[alg][0][1][3]}"])
        if result[alg][0][2]:
            data.append(["Migration Cost", result[alg][0][2]])
        if any(result[alg][0][4]):
            data.append(["Overhead Cost",  f"{result[alg][0][4][0]}, {result[alg][0][4][1]}, {result[alg][0][4][2]}, {result[alg][0][4][3]}"])

        data.append(["Deployment Cost", f"{result[alg][0][3][0]}, {result[alg][0][3][1]}, {result[alg][0][3][2]}, {result[alg][0][3][3]}"])
        data.append(["Revenue", r_t.R])

        ## We wait until all the algorithms reach the results (which is bounded by the timeout in their algorithm implementation for 5Guard)
        result[alg][0][7] = max(result[a][0][7] for a in algs)
    else: # Infeasible
        data = [
            ["Algorithm", alg],
            ["Request Isolation Level", f"({r_t.gamma}, {r_t.kappa})"],
            ["Allocation Time", result[alg][0][7]],
            ["Feasible", result[alg][0][8]],
            ["Timeout", result[alg][0][9]]
        ]

    print(tabulate(data, headers=["Category", "Value"], tablefmt="grid"))

    return result[alg][0], alg_idx, result[alg][1], result[alg][2]