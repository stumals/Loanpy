#%%
import pandas as pd

from econ.fred_econ import FRED
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import TimeSeriesSplit, KFold
import sklearn.metrics as metrics
import statsmodels.api as sm

# %%

class Models:
    def __init__(self, x: pd.DataFrame, y: pd.Series) -> None:
        self.x = x
        self.y = y
        self.model = None

    def regression_metrics(self) -> None:
        pass
    
    
class LinReg(Models):
    def __init__(self, x: pd.DataFrame, y: pd.Series, time_series_split: bool=True,
                 k_cv: int=5, num_splits: int=5) -> None:
        
        super().__init__(x, y)
        self.k_cv = k_cv
        self.num_splits = num_splits
        self.time_series_split = time_series_split
        self.x = sm.add_constant(x)
    
    def test(self) -> pd.DataFrame:
        if self.time_series_split:
            data_split = TimeSeriesSplit(self.num_splits)
        else:
            data_split = KFold(self.num_splits)
        data = {}
        folds = []
        ms_errors_train = []
        ms_errors_test = []
        r2 = []
        for i, (train_index, test_index) in enumerate(data_split.split(self.x)):
            x_train = self.x.iloc[train_index,:]
            x_test = self.x.iloc[test_index,:]
            y_train = self.y.iloc[train_index]
            y_test = self.y.iloc[test_index]

            lm = sm.OLS(y_train, x_train).fit()
            preds_train = lm.predict(x_train)
            preds_test = lm.predict(x_test)
            mse_train = metrics.mean_squared_error(y_train, preds_train)
            mse_test = metrics.mean_squared_error(y_test, preds_test)
            r2_model = lm.rsquared_adj
            folds.append(i)
            ms_errors_train.append(mse_train)
            ms_errors_test.append(mse_test)
            r2.append(r2_model)
        data['folds'] = folds
        data['MSE_train'] = ms_errors_train
        data['MSE_test'] = ms_errors_test
        data['R-Squared Adj'] = r2
        df = pd.DataFrame(data)
        avg_row = {'folds': 'Avg', 'MSE_train': df['MSE_train'].mean(),
                   'MSE_test': df['MSE_test'].mean(), 'R-Squared Adj': df['R-Squared Adj'].mean()}
        df = pd.concat([df, pd.DataFrame(avg_row, index=[0])], ignore_index=True)
        return df
        

    def train(self) -> None:
        lm = sm.OLS(self.y, self.x).fit()
        self.model = lm
    
    def predict(self, x_new: pd.DataFrame, alpha: float=.05) -> pd.DataFrame:
        preds = self.model.get_prediction(x_new).summary_frame(alpha=alpha)
        return preds[['mean', 'obs_ci_lower', 'obs_ci_upper']]

    def gof_plots(self):
        # plt.scatter(df['ffr'], df['mgt_rate'])
        # plt.scatter(df['cpi'], df['mgt_rate'])
        # metrics.PredictionErrorDisplay(y_true=y_train, y_pred=preds).plot()
        # plt.hist(resids, bins=10)
        # sm.qqplot(resids, fit=True, line='45')
        pass

