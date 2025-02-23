from libraries import *

def run_opt(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi):
    result["opt"] = opt_iter(profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, 1)

def run_iar(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi):
    result["iar"] = iar_iter(profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, 1)

def run_dtr(result, LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi):
    result["dtr"] = dtr_iter(LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, 1)

def run_rnr(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi):
    result["rnr"] = rnr_iter(profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi, 1)

def run_in_process(target_function, result, *args):
    target_function(result, *args)

def fgr_iter(LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi):
    algs   = ["opt", "iar", "dtr", "rnr"]
    result = {}

    # Create threads
    threads = [
        threading.Thread(target=run_opt, args=(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)),
        threading.Thread(target=run_iar, args=(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)),
        threading.Thread(target=run_dtr, args=(result, LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)),
        threading.Thread(target=run_rnr, args=(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi))
    ]
    
    # Start threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Wait for threads to finish, but with a timeout
    start_time = time.time()
    for thread in threads:
        remaining_time = r_t.timeout - (time.time() - start_time)
        if remaining_time > 0:
            thread.join(timeout=remaining_time)  # Wait for each thread up to the deadline

#     run_opt(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)
#     run_iar(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)
#     run_dtr(result, LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)
#     run_rnr(result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)
        
    ## Profit * Feasibility
    arr = np.array([result["opt"][0] * result["opt"][9],
                    result["iar"][0] * result["iar"][9],
                    result["dtr"][0] * result["dtr"][9],
                    result["rnr"][0] * result["rnr"][9]])

    arr = np.round(arr, 4)  # Round each element to 4 decimal places to avoid numerical errors

    # Define preference order (0: opt, 1: iar, 2: dtr, 3: rnr)
    preference_order = [0, 1, 2, 3]  # Adjust this based on your priority

    max_value = np.max(arr)
    max_indices = np.where(arr == max_value)[0]  # Find all indices with max value

    # Select the preferred index based on the predefined order
    alg_idx = min(max_indices, key=preference_order.index)
    alg = algs[alg_idx]
    print(f"arr:{arr}")
    print(f"alg:{alg}")

    return result[alg]