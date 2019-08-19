import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsapi

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score

import warnings
warnings.filterwarnings('ignore')

import datetime
import glob
import os

# Retreive correct data files 

yesterday = (datetime.datetime.today() - datetime.timedelta(days = 1)).strftime("%m_%d_%Y")
today = datetime.datetime.today().strftime("%m_%d_%Y")

data_files = glob.glob("data/player_stats/*.csv")
data_files.sort(key=os.path.getmtime)
last_7_generated = data_files[-9:-2]

print("Getting data...")

hits = pd.concat([pd.read_csv(f) for f in last_7_generated], sort=False)
hits.dropna(inplace=True)
hits.set_index(np.arange(len(hits)), inplace=True)
hits['player_got_hit'] = hits['player_got_hit'].apply(float)

data = hits.iloc[:, 3:-1]
labels = hits.iloc[:, -1]

hits_test = pd.read_csv("data/player_stats/player_stats_{}.csv".format(today))
data_test = hits_test.iloc[:, 3:]

data_train, data_val, labels_train, labels_val = train_test_split(data, labels, test_size=0.2)

print("Data retrieved.")

# LOGISTIC REGRESSION

# Default params
print("Training logistic regression...")
logreg = LogisticRegression(penalty='l2').fit(data_train, labels_train)
print("Finished training!")

# ADABOOST

from sklearn.ensemble import AdaBoostClassifier
from sklearn.model_selection import GridSearchCV

print("Finding best hyperparameters for AdaBoost...")
param_grid = [
    {'n_estimators': [50, 75, 100, 125, 150]}
]

ada_cv = GridSearchCV(AdaBoostClassifier(), param_grid, cv=4)
ada_cv.fit(data_train, labels_train)

print("Training AdaBoost...")
boosted_dt = AdaBoostClassifier(n_estimators=ada_cv.best_params_['n_estimators'])
boosted_dt.fit(data_train, labels_train)
print("Finished training!")

# RANDOM FORESTS

from sklearn.ensemble import RandomForestClassifier

print("Finding best hyperparamters for random forests...")
param_grid = [
    {'criterion': ['gini'], 'max_depth': [20], 'min_samples_leaf': [4, 10, 20, 30],
    'n_estimators': [50, 75, 100, 125, 150]}
]

rf_cv = GridSearchCV(RandomForestClassifier(), param_grid, cv=4)
rf_cv.fit(data_train, labels_train)
best_rf_params = rf_cv.best_params_

print("Training random forests...")
rf_classifier = RandomForestClassifier(n_estimators=best_rf_params['n_estimators'], criterion=best_rf_params['criterion'], 
                                       max_depth=best_rf_params['max_depth'], min_samples_leaf=best_rf_params['n_estimators'])
rf_classifier.fit(data_train, labels_train)
print("Finished training!")

# Get model summaries

acc_logreg = np.mean(logreg.predict(data_val) == labels_val)
prec_logreg = precision_score(labels_val, logreg.predict(data_val))
rec_logreg = recall_score(labels_val, logreg.predict(data_val))
f1_logreg = f1_score(labels_val, logreg.predict(data_val))

acc_rf = np.mean(rf_classifier.predict(data_val) == labels_val)
prec_rf = precision_score(labels_val, rf_classifier.predict(data_val))
rec_rf = recall_score(labels_val, rf_classifier.predict(data_val))
f1_rf = f1_score(labels_val, rf_classifier.predict(data_val))

acc_ada = np.mean(boosted_dt.predict(data_val) == labels_val)
prec_ada = precision_score(labels_val, boosted_dt.predict(data_val))
rec_ada = recall_score(labels_val, boosted_dt.predict(data_val))
f1_ada = f1_score(labels_val, boosted_dt.predict(data_val))

performance = pd.DataFrame([['Logreg', acc_logreg, prec_logreg, rec_logreg, f1_logreg],
             ['Random Forests', acc_rf, prec_rf, rec_rf, f1_rf],
             ['AdaBoost', acc_ada, prec_ada, rec_ada, f1_ada]], 
             columns=['Model', 'Accuracy', 'Precision', 'Recall', "F1 Score"])
print("Model performance summary on validation set: \n", performance)

performance.to_csv("data/model_stats/performance_{}.csv".format(today))

models_dict = {'Logreg': logreg, 'Random Forests': rf_classifier, 'AdaBoost': boosted_dt}
best_model = models_dict[performance.sort_values('F1 Score', ascending=False).iloc[0]['Model']]

# Make predictions

predictions = hits_test.take(np.argsort(best_model.predict_proba(data_test)[:, 1])[::-1][:10])[['Name', 'Team']].reset_index().iloc[:, 1:]
predictions.columns = ["name", "team_id"]
predictions["team_name"] = predictions['team_id'].apply(lambda x: statsapi.lookup_team(x)[0]['name'])
predictions["hit_probability"] = np.sort(rf_classifier.predict_proba(data_test)[:, 1])[::-1][:10]
predictions.to_csv("data/predictions/predictions_{}.csv".format(today))

print("Predictions for today: \n", predictions)

