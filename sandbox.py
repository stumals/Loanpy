#%%
from utils.utils import expected_value_cagr
import numpy as np
import pandas as pd
import os
from econ.econ_data import EconData
import requests
import numpy_financial as npf
from datetime import date
from dateutil.relativedelta import relativedelta
import json
from dotenv import load_dotenv, find_dotenv
load_dotenv()

from loan.loan_input import LoanInput
from loan.core import Loan
from econ.fred_econ import FRED
from utils.utils import expected_value_cagr, affordability_calc

#%%
affordability_calc(100000, )