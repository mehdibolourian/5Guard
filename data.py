## Class entity definitions

class vserver():
    def __init__(self, C_REQ, Xi_REQ, Chi_REQ):
        self.C_REQ   = C_REQ   # Required MIPS
        self.Xi_REQ  = Xi_REQ  # Required number of VNFs
        self.Chi_REQ = Chi_REQ # Required set of VNF types for different instances
        
class ru():
    def __init__(self, K_REQ):
        self.K_REQ = K_REQ     # Required number of PRBs

class vpath():
    def __init__(self, v, w, j, B_REQ, D_REQ):
        self.v     = v         # End node 1
        self.w     = w         # End node 2
        self.j     = j         # Index of the vpath
        self.B_REQ = B_REQ     # Bandwidth request
        self.D_REQ = D_REQ     # Path RTT delay request
        
class link():
    def __init__(self, B_MAX,E_P):
        self.B_MAX = B_MAX     # Maximum bandwidth for the set of wavelength slots
        self.E_P   = E_P       # Set of paths using this link
        
class pserver():
    def __init__(self, C_MAX, Xi_MAX):
        self.C_MAX  = C_MAX    # MIPS limit
        self.Xi_MAX = Xi_MAX   # Maximum number of computing blocks at different isolation levels
        
class nr_bs():
    def __init__(self, Pi_MAX):
        self.Pi_MAX = Pi_MAX   # Maximum amount of radio resources on different frequency slots

class ppath():
    def __init__(self, p, q, i, D_RTT):
        self.p     = p         # End node 1
        self.q     = q         # End node 2
        self.i     = i         # Index of the edge
        self.D_RTT = D_RTT     # Ppath RTT delay
        
class request():
    def __init__(self, V_S, V_R, E, gamma, kappa, R, Omega, Phi, Theta, rho_B, rho_D, rho_C, rho_K, beta, timeout):
        self.V_S    = V_S      # Requested set of Vservers
        self.V_R    = V_R      # Requested set of RUs
        self.E      = E        # Requested virtual Vpaths
        self.gamma  = gamma    # E2E isolation level
        self.kappa  = kappa    # VNF sharing isolation sublevel
        self.R      = R        # Revenue
        self.Omega  = Omega    # Cost of a unit of MIPS on different Pservers
        self.Phi    = Phi      # Cost of a unit of radio resource on different NR-BSs
        self.Theta  = Theta    # Cost of a unit of bandwidth on different Ppaths
        self.rho_B  = rho_B    # Cost of a unit of QoS bandwidth violation
        self.rho_D  = rho_D    # Cost of a unit of QoS delay violation
        self.rho_C  = rho_C    # Cost of a unit of QoS MIPS violation
        self.rho_K  = rho_K    # Cost of a unit of QoS radio resource violation
        self.beta   = beta     # Cost of a unit of migration
        self.timeout= timeout  # Resource Allocation Deadline
        
class system():
    def __init__(self, Pi_PRB, N_FRM, C_HHO, C_CON, C_GOS, Pi_FGB, Psi_HDR, CHI_MAX, B_WSC, B_WGB):
        self.Pi_PRB  = Pi_PRB   # Radio resource consumed by a PRB
        self.N_FRM   = N_FRM    # Number of PRBs in a radio frame
        self.C_HHO   = C_HHO    # Capacity overhead of host OS and hypervisor
        self.C_CON   = C_CON    # Capacity overhead of docker controller
        self.C_GOS   = C_GOS    # Capacity overhead of guest OS
        self.Pi_FGB  = Pi_FGB   # Capacity overhead of frequency guard band
        self.Psi_HDR = Psi_HDR  # Percent of overhead imposed by the MPLS header
        self.CHI_MAX = CHI_MAX  # Maximum number of VNF types
        self.B_WSC   = B_WSC    # Bandwidth of the wavelength subcarrier
        self.B_WGB   = B_WGB    # Bandwidth guardband overhead