from libraries import *

MIPS_SCALE          = 1e-4
BANDWIDTH_SCALE     = 1e-6 #1e-9
LATENCY_SCALE       = 1e4

P_min               = 0
BETA_HP             = (1e6) - 1
epsilon             = 1e-2
delta               = 1e-2
M                   = 100
N                   = 1000

THREADS             = 64

K_MAX = 11
F_MAX = 1
S_MAX = 1

C_MAX_MEC_BRAIN     = 1000545
C_MAX_CLD_BRAIN     = C_MAX_MEC_BRAIN * 10
Pi_MAX_BRAIN        = 500040
B_MAX_BRAIN         = 4.8e12


## Pi_PRB  = 15 * 12 = 180        --> 12 subcarriers with 15 kHz spacing for 1 ms interval
## N_FRM   = 10                   --> Frame is 10ms --> 10, 20, 40, 80, 160  -- 3GPP TS 38.211
## C_HHO   = 100,000              --> 10% of AMD EPYC 9684X 1,000,545 MFOps
## C_K8S   = 25,000               --> 2.5% of AMD EPYC 9684X 1,000,545 MFOps
## C_GOS   = 25,000               --> 2.5% of AMD EPYC 9684X 1,000,545 MFOps
## Pi_FGB  = 693                  --> 692.5kHz*1ms = 693 --> 3GPP TS 38.104
## Psi_HDR = 0.005                --> 32bits/65535bits --> Payload/Header
## CHI_MAX = 6                    --> 6 high-level types
## B_WSC   = 12.5 GHz             --> ITU-T G.698.2
## B_WGB   = 12.5 GHz             --> 1 subcarrier spacing (Typically 1-2 SCS)
## Omega   = 1e-3/MIPS_SCALE      --> Cost of a unit of MIPS (0.001 $ per MIPS)
## Phi     = 0.01                 --> Cost of a unit of radio resource (0.01 $ per PRB)
## Theta   = 1e-9/BANDWIDTH_SCALE --> Cost of a unit of bandwidth (0.001 $ per MHz)
sys = system(180,10,100000*MIPS_SCALE,25000*MIPS_SCALE,25000*MIPS_SCALE,693,0.005,6,12.5e9*BANDWIDTH_SCALE,12.5e9*BANDWIDTH_SCALE,1e-4/MIPS_SCALE,1,1e-10/BANDWIDTH_SCALE) # 0.005

def init_setup_synth():
    global P_min, BETA_HP, epsilon, delta, M, N, SIMULATION_INTERVAL
    global ITER, TIMEOUT

    # Process each node
    V_P_S   = []
    V_P_R   = []
    E_P     = []
    E_P_l   = []
    L       = []
    L_pqi   = []
    
    NUM_P_S = 5
    V_P_S.append(ps(C_MAX_MEC_BRAIN/5  * MIPS_SCALE, [110, 60, 1]))    # AMD EPYC 9684X
    V_P_S.append(ps(C_MAX_MEC_BRAIN/5  * MIPS_SCALE, [110, 60, 1]))    # AMD EPYC 9684X
    V_P_S.append(ps(C_MAX_CLD_BRAIN/5 * MIPS_SCALE, [1100, 600, 1]))  # AMD EPYC 9684X * 10
    
    NUM_P_R = 2
    V_P_R   = [nr_bs([Pi_MAX_BRAIN/5]) for _ in range(NUM_P_R)]  # 50MHz channel bandwidth --> 50MHz * 10ms/5 = 500040/5 --> 2778/5 PRBs-sec.
        
    E_P.append(pp(V_P_S[0], V_P_R[0], 0, 1e-4 * LATENCY_SCALE))
    E_P.append(pp(V_P_S[0], V_P_R[1], 0, 1e-4 * LATENCY_SCALE))
    E_P.append(pp(V_P_S[1], V_P_R[0], 0, 2e-6 * LATENCY_SCALE))
    E_P.append(pp(V_P_S[1], V_P_R[1], 0, 2e-6 * LATENCY_SCALE))
    E_P.append(pp(V_P_S[2], V_P_R[0], 0, 1e-3 * LATENCY_SCALE))
    E_P.append(pp(V_P_S[2], V_P_R[1], 0, 1e-3 * LATENCY_SCALE))
    E_P.append(pp(V_P_S[0], V_P_S[2], 0, 1e-3 * LATENCY_SCALE))
    E_P.append(pp(V_P_S[1], V_P_S[2], 0, 1e-3 * LATENCY_SCALE))
    
    for i in range(8):
        L.append(link([B_MAX_BRAIN/5 * BANDWIDTH_SCALE], [E_P[i]]))  # 4.8 THz link bandwidth
    
    L_pqi = [[l for l in L if e_p in l.E_P] for e_p in E_P]
    E_P_l = [[e_p for e_p in l.E_P] for l in L]

    return V_P_S, V_P_R, E_P, E_P_l, L, L_pqi


def init_setup_brain():
    global P_min, BETA_HP, epsilon, delta, M, N, SIMULATION_INTERVAL
    global ITER, coef, TIMEOUT
    
    # Topology from https://sndlib.put.poznan.pl/home.action
    namespace = {'ns': 'http://sndlib.zib.de/network'}
    
    # Parse the XML file
    tree = ET.parse('dataset/brain.xml')
    root = tree.getroot()
    
    # Find nodes under networkStructure
    nodes = root.find('ns:networkStructure/ns:nodes', namespace)
    links = root.findall('ns:networkStructure/ns:links/ns:link', namespace)
    
    # Process each node
    V_P_S   = []
    V_P_R   = []
    E_P     = []
    E_P_l   = []
    L       = []
    L_pqi   = []

    cloud_list = ['UP', 'TU', 'CVK']
    node_list  = []
    for node in nodes.findall('ns:node', namespace):
        node_id = node.attrib['id']
        
        # Cloud servers:
        if node_id in cloud_list:
            V_P_S.append(ps(C_MAX_CLD_BRAIN*MIPS_SCALE, [1100,600,1])) ## AMD EPYC 9684X * 10
            node_list.append(node_id)
        else:
            if any((l.find('ns:source', namespace).text in cloud_list or
                   l.find('ns:target', namespace).text in cloud_list) and
                   (l.find('ns:source', namespace).text == node_id or
                   l.find('ns:target', namespace).text == node_id)
                   for l in links
                  ):
                node_list.append(node_id)
                V_P_S.append(ps(C_MAX_MEC_BRAIN*MIPS_SCALE, [110,60,1]))    ## AMD EPYC 9684X
                V_P_R.append(nr_bs([Pi_MAX_BRAIN]))                         # 50MHz channel bandwidth --> 50MHz * 10ms/5 = 500000/5 --> 2778/5 PRBs-sec.
                E_P.append(pp(V_P_S[-1], V_P_R[-1], 0, 2e-6*LATENCY_SCALE))
                L.append(link([B_MAX_BRAIN*BANDWIDTH_SCALE], [E_P[-1]])) ## 4.8 THz (191.3 THz to 196.1 THz, 1565 nm to 1570 nm) = roughly 320 subcarriers
    
    # Process each link
    for link1 in links:
        link_id = link1.attrib['id']
        source = link1.find('ns:source', namespace).text
        target = link1.find('ns:target', namespace).text

        if (source in cloud_list) or (target in cloud_list):
            source_idx = 0
            target_idx = 0
            idx = 0
                    
            E_P.append(pp(V_P_S[node_list.index(source)], V_P_S[node_list.index(target)], 0, 2e-6*LATENCY_SCALE))
            L.append(link([B_MAX_BRAIN*BANDWIDTH_SCALE], [E_P[-1]])) ## 4.8 THz (191.3 THz to 196.1 THz, 1565 nm to 1570 nm) = roughly 320 subcarriers
    
    # L_pqi = [[l for l in L if e_p in l.E_P] for e_p in E_P]
    # E_P_l = [[e_p for e_p in l.E_P] for l in L]
    
    # for node in nodes.findall('ns:node', namespace):
    #     node_id = node.attrib['id']
    #     # Cloud servers:
    #     if (node_id == 'UP') or (node_id == 'TU') or (node_id == 'CVK') or (node_id == 'HU') or (node_id == 'HTW') or (node_id == 'ADH') or (node_id == 'ZIB') or (node_id == 'SPK') or (node_id == 'WIAS'):
    #         V_P_S.append(ps(10005450*MIPS_SCALE, [1100,600,1])) ## AMD EPYC 9684X * 10
    #     else:
    #         V_P_S.append(ps(1000545*MIPS_SCALE, [110,60,1]))    ## AMD EPYC 9684X
    #         V_P_R.append(nr_bs([500040]))                       # 50MHz channel bandwidth --> 50MHz * 10ms/5 = 500000/5 --> 2778/5 PRBs-sec.
    #         E_P.append(pp(V_P_S[-1], V_P_R[-1], 0, 2e-6*LATENCY_SCALE))
    #         L.append(link([4.8e12*BANDWIDTH_SCALE], [E_P[-1]])) ## 4.8 THz (191.3 THz to 196.1 THz, 1565 nm to 1570 nm) = roughly 320 subcarriers
    
    # # Process each link
    # for link1 in links:
    #     link_id = link1.attrib['id']
    #     source = link1.find('ns:source', namespace).text
    #     target = link1.find('ns:target', namespace).text
    
    #     source_idx = 0
    #     target_idx = 0
    #     idx = 0
    #     for node in nodes.findall('ns:node', namespace):
    #         node_id = node.attrib['id']
    #         if node_id == source:
    #             source_idx = idx
    #         if node_id == target:
    #             target_idx = idx
    #         idx +=1
                
    #     E_P.append(pp(V_P_S[source_idx], V_P_S[target_idx], 0, 2e-6*LATENCY_SCALE))
    #     L.append(link([4e12*BANDWIDTH_SCALE], [E_P[-1]])) ## 4 THz (191.3 THz to 196.1 THz, 1565 nm to 1570 nm) = roughly 320 subcarriers
    
    L_pqi = [[l for l in L if e_p in l.E_P] for e_p in E_P]
    E_P_l = [[e_p for e_p in l.E_P] for l in L]
    
    # P_min               = 100
    # BETA_HP             = float("inf")
    # epsilon             = 1e-2
    # delta               = 1e-2

    return V_P_S, V_P_R, E_P, E_P_l, L, L_pqi

def create_sr_resources():
    """
    Create predefined slice resources and their configurations.
    Returns:
        sr_types (list): List of Slice Request (SR) types.
        sr_probs (list): Probabilities for each SR type.
    """

    offset = 0
    scale  = 5
    
    ######## Isolation Level 0:
    V_S_mmtc = [nf(4000 * MIPS_SCALE, 1, [0])]
    V_R_mmtc = [ru(10)]
    E_mmtc   = [vp(V_S_mmtc[0], V_R_mmtc[0], 0, 10e4 * BANDWIDTH_SCALE, 1e-3 * LATENCY_SCALE)]
    cost = ( sys.Theta  * sum(e.B_REQ for idx_e, e in enumerate(E_mmtc))
            + sys.Omega * sum(v.C_REQ + (sys.C_K8S + sys.C_GOS)*v.Xi_REQ/110 + sys.C_HHO*v.Xi_REQ/110/60 for idx_v, v in enumerate(V_S_mmtc))
            + sys.Phi   * sum(w.K_REQ for idx_w, w in enumerate(V_R_mmtc))
           )
    revenue = int(cost * scale) + offset #250 #int(cost * 50)
    r_mmtc = sr(
        V_S_mmtc, V_R_mmtc, E_mmtc, 0, 0, revenue,
        1e-1 / BANDWIDTH_SCALE, 10 / LATENCY_SCALE, 1e-1 / MIPS_SCALE, 10,
        1, 10
    )

    V_S_embb = [nf(6000 * MIPS_SCALE, 3, [0, 1, 2])]
    V_R_embb = [ru(1)]
    E_embb = [vp(V_S_embb[0], V_R_embb[0], 0, 10e9 * BANDWIDTH_SCALE, 1e-3 * LATENCY_SCALE)]
    cost = ( sys.Theta  * sum(e.B_REQ for idx_e, e in enumerate(E_embb))
            + sys.Omega * sum(v.C_REQ + (sys.C_K8S + sys.C_GOS)*v.Xi_REQ/110 + sys.C_HHO*v.Xi_REQ/110/60 for idx_v, v in enumerate(V_S_embb))
            + sys.Phi   * sum(w.K_REQ for idx_w, w in enumerate(V_R_embb))
           )
    revenue = int(cost * scale) + offset # 100 #int(cost * 50)
    r_embb = sr(
        V_S_embb, V_R_embb, E_embb, 0, 1, revenue,
        1e-7 / BANDWIDTH_SCALE, 10 / LATENCY_SCALE, 1e-2 / MIPS_SCALE, 0.1,
        1, 6
    )

    ######## Isolation Level 1:
    V_S_urll = [nf(10000 * MIPS_SCALE, 5, [0, 1, 2, 3, 4])]
    V_R_urll = [ru(1)] ## Will be rounded to the bandwidth of the wavelength subcarrier
    E_urll = [vp(V_S_urll[0], V_R_urll[0], 0, 10e6 * BANDWIDTH_SCALE, 1e-5 * LATENCY_SCALE)]
    cost = ( sys.Theta  * sum(max(e.B_REQ, math.ceil(e.B_REQ * BANDWIDTH_SCALE / sys.B_WSC) * sys.B_WSC) + sys.B_WGB for idx_e, e in enumerate(E_urll))
            + sys.Omega * sum(v.C_REQ + sys.C_GOS*v.Xi_REQ + sys.C_HHO*v.Xi_REQ/60 for idx_v, v in enumerate(V_S_urll))
            + sys.Phi   * sum(max(w.K_REQ, math.ceil(w.K_REQ / sys.N_FRM) * sys.N_FRM) + sys.Pi_FGB for idx_w, w in enumerate(V_R_urll))
           )
    revenue = int(cost * scale) + offset #1000 #int(cost * 50)
    r_urll = sr(
        V_S_urll, V_R_urll, E_urll, 1, 0, revenue,
        1e-6 / BANDWIDTH_SCALE, 100 / LATENCY_SCALE, 1 / MIPS_SCALE, 100,
        100, 4
    )

    ######## Isolation Level 2:
    V_S_mcri = [nf(16000 * MIPS_SCALE, 5, [0, 1, 2, 3, 4])]
    V_R_mcri = [ru(1)]
    E_mcri = [vp(V_S_mcri[0], V_R_mcri[0], 0, 10e9 * BANDWIDTH_SCALE, 1e-5 * LATENCY_SCALE)]
    cost = ( sys.Theta  * sum(B_MAX_BRAIN * BANDWIDTH_SCALE for idx_e, e in enumerate(E_mcri) )
            + sys.Omega * sum(C_MAX_MEC_BRAIN * MIPS_SCALE for idx_v, v in enumerate(V_S_mcri))
            + sys.Phi   * sum(Pi_MAX_BRAIN/sys.Pi_PRB for idx_w, w in enumerate(V_R_mcri))
           )
    revenue = int(cost * scale) + offset #2500 #int(cost * 50)
    r_mcri = sr(
        V_S_mcri, V_R_mcri, E_mcri, 2, 0, revenue,
        #1e6, 1e6, 1e6, 1e6,
        1e4, 1e4, 1e4, 1e4,
        1e4, 2
    )

    sr_types = [r_embb, r_urll, r_mmtc, r_mcri] # L01, L1, L00, L2

    for i, r in enumerate(sr_types):
        print(f"revenue of SR type {i} with isolation level {r.gamma} and sub-level {r.kappa}: {r.R}")

    return sr_types


def init_setup_sr(iterations, simulation_interval, sr_types, sr_probs):
    """Generates SR list based on probabilities and simulation intervals."""
    
    sr_list = []
    sr_type_list = []

    np.random.seed(42)  # Seed for reproducibility

    for _ in range(iterations):
        for _ in range(simulation_interval):
            selected_sr = np.random.choice(sr_types, p=sr_probs)
            sr_list.append(copy.deepcopy(selected_sr)) ## Ensure same types are located @ different addresses to make each instance is unique
            sr_type_list.append(sr_types.index(selected_sr))

    return sr_list, sr_type_list