from libraries import *

MIPS_SCALE          = 1e-4
BANDWIDTH_SCALE     = 1e-6
LATENCY_SCALE       = 1e6
SIMULATION_INTERVAL = 80

## Pi_PRB  = 15 * 12 = 180 --> Subcarrier spacing options: 15 kHz (1 ms), 30 kHz (0.5 ms), 60 kHz (0.25 ms), 120 kHz (0.125 ms), 240 kHz (0.0625 ms)
## N_FRM   = 10            --> Frame is 10ms --> 10, 20, 40, 80, 160  -- 3GPP TS 38.211
## C_HHO   = 100,000       --> 10% of AMD EPYC 9684X 1,000,545 MFOps
## C_CON   = 25,000        --> 2.5% of AMD EPYC 9684X 1,000,545 MFOps
## C_GOS   = 25,000        --> 2.5% of AMD EPYC 9684X 1,000,545 MFOps
## Pi_FGB  = 693           --> 692.5kHz*1ms = 693 -- 3GPP TS 38.104
## Psi_HDR = 0.005         --> 32bits/65535bits --> Payload/Header
## CHI_MAX = 6             --> 6 high-level types
## B_WSC   = 12.5 GHz      --> ITU-T G.698.2
## B_WGB   = 12.5 GHz      --> 1 subcarrier spacing (Typically 1-2 SCS)
sys = system(180,10,100000*MIPS_SCALE,25000*MIPS_SCALE,25000*MIPS_SCALE,693,0.005,6,12.5e9*BANDWIDTH_SCALE,12.5e9*BANDWIDTH_SCALE) # 0.005

def init_setup_synth():
    global P_min, BETA_HP, epsilon, delta, M, N, SIMULATION_INTERVAL
    global ITER, coef, TIMEOUT, ScaleFlag, NumericFocus

    MIPS_SCALE      = 1e-4
    LATENCY_SCALE   = 1e6
    BANDWIDTH_SCALE = 1e-6
    
    # Process each node
    V_P_S   = []
    V_P_R   = []
    E_P     = []
    E_P_l   = []
    L       = []
    L_pqi   = []
    
    NUM_P_S = 5
    V_P_S.append(pserver(1000000 * MIPS_SCALE, [110, 60, 1]))  # AMD EPYC 9684X
    V_P_S.append(pserver(1000000 * MIPS_SCALE, [110, 60, 1]))  # AMD EPYC 9684X
    V_P_S.append(pserver(10000000 * MIPS_SCALE, [1100, 600, 1]))  # AMD EPYC 9684X * 10
    
    NUM_P_R = 2
    V_P_R   = [nr_bs([500000]) for _ in range(NUM_P_R)]  # 50MHz channel bandwidth --> 50MHz * 1ms = 50000
        
    E_P.append(ppath(V_P_S[0], V_P_R[0], 0, 1e-4 * LATENCY_SCALE))
    E_P.append(ppath(V_P_S[0], V_P_R[1], 0, 1e-4 * LATENCY_SCALE))
    E_P.append(ppath(V_P_S[1], V_P_R[0], 0, 2e-6 * LATENCY_SCALE))
    E_P.append(ppath(V_P_S[1], V_P_R[1], 0, 2e-6 * LATENCY_SCALE))
    E_P.append(ppath(V_P_S[2], V_P_R[0], 0, 1e-3 * LATENCY_SCALE))
    E_P.append(ppath(V_P_S[2], V_P_R[1], 0, 1e-3 * LATENCY_SCALE))
    E_P.append(ppath(V_P_S[0], V_P_S[2], 0, 1e-3 * LATENCY_SCALE))
    E_P.append(ppath(V_P_S[1], V_P_S[2], 0, 1e-3 * LATENCY_SCALE))
    
    for i in range(8):
        L.append(link([4.8e12 * BANDWIDTH_SCALE], [E_P[i]]))  # 4.8 THz link bandwidth
    
    L_pqi = [[l for l in L if e_p in l.E_P] for e_p in E_P]
    E_P_l = [[p for p in l.E_P] for l in L]
    
    P_min               = 0
    BETA_HP             = (1e6) - 1
    epsilon             = 1e-2
    delta               = 1e-2
    M                   = 100
    N                   = 1000
    ITER                = 2
    coef                = 1000
    TIMEOUT             = 200
    ScaleFlag           = 0
    NumericFocus        = 1

    return V_P_S, V_P_R, E_P, E_P_l, L, L_pqi


def init_setup_brain():
    global P_min, BETA_HP, epsilon, delta, M, N, SIMULATION_INTERVAL
    global ITER, coef, TIMEOUT, ScaleFlag, NumericFocus
    
    # Topology from https://sndlib.put.poznan.pl/home.action
    namespace = {'ns': 'http://sndlib.zib.de/network'}
    
    # Parse the XML file
    tree = ET.parse('brain.xml')
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
    
    for node in nodes.findall('ns:node', namespace):
        node_id = node.attrib['id']
        # Cloud servers:
        if (node_id == 'UP') or (node_id == 'TU') or (node_id == 'CVK') or (node_id == 'HU') or (node_id == 'HTW') or (node_id == 'ADH') or (node_id == 'ZIB') or (node_id == 'SPK') or (node_id == 'WIAS'):
            V_P_S.append(pserver(10000000*MIPS_SCALE, [1100,600,1])) ## AMD EPYC 9684X * 10
        else:
            V_P_S.append(pserver(1000000*MIPS_SCALE, [110,60,1])) ## AMD EPYC 9684X
            V_P_R.append(nr_bs([500000]))                          ## 50MHz channel bandwidth --> 50MHz * 1ms = 50000
            E_P.append(ppath(V_P_S[-1], V_P_R[-1], 0, 2e-6*LATENCY_SCALE))
            L.append(link([4.8e12*BANDWIDTH_SCALE], [E_P[-1]])) ## 4.8 THz (191.3 THz to 196.1 THz, 1565 nm to 1570 nm) = roughly 320 subcarriers
    
    # Process each link
    for link1 in links:
        link_id = link1.attrib['id']
        source = link1.find('ns:source', namespace).text
        target = link1.find('ns:target', namespace).text
    
        source_idx = 0
        target_idx = 0
        idx = 0
        for node in nodes.findall('ns:node', namespace):
            node_id = node.attrib['id']
            if node_id == source:
                source_idx = idx
            if node_id == target:
                target_idx = idx
            idx +=1
                
        E_P.append(ppath(V_P_S[source_idx], V_P_S[target_idx], 0, 2e-6*LATENCY_SCALE))
        L.append(link([4e12*BANDWIDTH_SCALE], [E_P[-1]])) ## 4 THz (191.3 THz to 196.1 THz, 1565 nm to 1570 nm) = roughly 320 subcarriers
    
    L_pqi = [[l for l in L if e_p in l.E_P] for e_p in E_P]
    E_P_l = [[p for p in l.E_P] for l in L]
    
    P_min               = 100
    BETA_HP             = float("inf")
    epsilon             = 1e-2
    delta               = 1e-2
    M                   = 100
    N                   = 1000
    ITER                = 1
    coef                = 1000
    TIMEOUT             = 120

    return V_P_S, V_P_R, E_P, E_P_l, L, L_pqi