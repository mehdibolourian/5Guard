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

    # # Create processes for each function
    # processes = [
    #     multiprocessing.Process(target=run_in_process, args=(run_opt, result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)),
    #     multiprocessing.Process(target=run_in_process, args=(run_iar, result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)),
    #     multiprocessing.Process(target=run_in_process, args=(run_dtr, result, LIMIT, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)),
    #     multiprocessing.Process(target=run_in_process, args=(run_rnr, result, profit_prev, iter, t, r_t, R_t, V_P_S, V_P_R, E_P, E_P_l, L, L_pqi)),
    # ]

    # # Start all processes
    # for process in processes:
    #     process.start()

    # # Wait for processes to finish, checking time elapsed
    # start_time = time.time()
    # while time.time() - start_time < r_t.timeout:
    #     if all(not process.is_alive() for process in processes):
    #         break  # If all processes have finished
    #     time.sleep(0.1)  # Check every 0.1 seconds

    # # Force terminate any remaining processes after the deadline
    # for process in processes:
    #     if process.is_alive():
    #         print(f"Terminating {process.name} as it exceeded the deadline.")
    #         process.terminate()
    #         process.join()  # Ensure process cleanup

    # print(result)
        
    ## Profit * Feasibility
    arr     = np.array([result["opt"][0] * result["opt"][9],
                        result["iar"][0] * result["iar"][9],
                        result["dtr"][0] * result["dtr"][9],
                        result["rnr"][0] * result["rnr"][9]])
    alg_idx = np.argmax(arr)  # Returns the index of the max value
    alg     = algs[alg_idx]

    return result[alg]