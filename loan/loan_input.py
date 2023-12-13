from pydantic import BaseModel, confloat, conint

class LoanInput(BaseModel):
    '''
    Parameters for loan.core.Loan class

    asset_amt : value of property to get loan for
    rate_annual : annual rate of loan
    num_years : number of years of loan
    pmt_freq : number of payments per year
    down_pmt : down payment percentage on loan
    closing_cost : closing cost of loan
    closing_cost_finance : boolean if the closing cost is financied through loan or not
    prop_tax_rate : property tax rate
    pmi_rate : private mortgage insurance rate
    maint_rate : maintance rate
    home_value_appreciation : annual appreciation rate of property
    home_sale_percent : percent cost of sale of property
    '''

    asset_amt: confloat(ge=0)
    rate_annual: confloat(ge=0, lt=1)
    num_years: conint(ge=1)
    pmt_freq: conint(ge=1) = 12
    down_pmt: confloat(ge=0, lt=1) = 0
    closing_cost: confloat(ge=0) = 0
    closing_cost_finance: bool = False
    prop_tax_rate: confloat(ge=0, lt=1) = .01 
    pmi_rate: confloat(ge=0, lt=1) = .01
    maint_rate: confloat(ge=0, lt=1) = .01
    home_value_appreciation: confloat(ge=0, lt=1) = .03
    home_sale_percent: confloat(ge=0, lt=1) = .06