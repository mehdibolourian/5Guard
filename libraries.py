#!/usr/bin/env python3.11

## General libraries
import time
import random
import threading
import multiprocessing
import concurrent.futures
import copy
import math
import pickle
import os
import numpy                 as     np
import gurobipy              as     gp
import matplotlib            as     mpl
import matplotlib.pyplot     as     plt
import matplotlib.patches    as     mpatches
import networkx              as     nx
import xml.etree.ElementTree as     ET
from   gurobipy              import GRB
from   collections           import Counter
from   matplotlib.ticker     import ScalarFormatter
from   tabulate              import tabulate
import matplotlib.ticker     as     ticker
from   itertools             import product

## Project library files
from data  import *
from setup import *
from plot  import *
from algorithms.dtr import *
from algorithms.iar import *
from algorithms.opt import *
from algorithms.rnr import *
from algorithms.fgr import *
from algorithms.nis import *
from algorithms.cis import *