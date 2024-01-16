#%%
import pandas as pd

from .fred_econ import FRED
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import TimeSeriesSplit, KFold
import sklearn.metrics as metrics

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
    
    def test(self) -> pd.DataFrame:
        if self.time_series_split:
            data_split = TimeSeriesSplit(self.num_splits)
        else:
            data_split = KFold(self.num_splits)
        data = {}
        folds = []
        ms_errors_train = []
        ms_errors_test = []
        for i, (train_index, test_index) in enumerate(data_split.split(self.x)):
            if len(self.x.shape) == 1:
                x_train = self.x.iloc[train_index].to_numpy().reshape(-1,1)
                x_test = self.x.iloc[test_index].to_numpy().reshape(-1,1)
            else:
                x_train = self.x.iloc[train_index].to_numpy()
                x_test = self.x.iloc[test_index].to_numpy()
            y_train = self.y.iloc[train_index]
            y_test = self.y.iloc[test_index]
            lm = LinearRegression().fit(x_train, y_train)
            preds_train = lm.predict(x_train)
            preds_test = lm.predict(x_test)
            mse_train = metrics.mean_squared_error(y_train, preds_train)
            mse_test = metrics.mean_squared_error(y_test, preds_test)
            folds.append(i)
            ms_errors_train.append(mse_train)
            ms_errors_test.append(mse_test)
        data['folds'] = folds
        data['MSE_train'] = ms_errors_train
        data['MSE_test'] = ms_errors_test
        df = pd.DataFrame(data)
        avg_row = {'folds': 'Avg', 'MSE_train': df['MSE_train'].mean(), 'MSE_test': df['MSE_test'].mean()}
        df = pd.concat([df, pd.DataFrame(avg_row, index=[0])], ignore_index=True)
        return df
        

    def train(self) -> None:
        lm = LinearRegression().fit(self.x, self.y)
        self.model = lm

