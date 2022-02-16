#%%
from feature_eng import Feature_Engineering
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error
import time

np.random.seed(2)

#%%
feature_eng = Feature_Engineering()
df = feature_eng.get_data()
#%%
df.columns.tolist()
#%%
# testing with a subset of features to start with.. 
X = df[['HomeTeam_Attack_Coeff', 'HomeTeam_Defense_Coeff', 'AwayTeam_Attack_Coeff', 'AwayTeam_Defense_Coeff', 'Round', 'Match_Result']]
#%%
# make match result numeric 
def f(x):
    if x == 'H':
        return 1
    else: 
        return -1 if x == 'A' else 0

X['Match_Result_num'] = (X['Match_Result']).apply(lambda x: f(x))
#%%
# remove rows in round 1 - 5 as past 5 matches are used to create features
X = X[X['Round']>5]#%%
#%%
# X.drop(labels=['Match_Result', 'Round'], axis=1, inplace=True)
#%%
X, y = X[['HomeTeam_Attack_Coeff', 'HomeTeam_Defense_Coeff', 'AwayTeam_Attack_Coeff', 'AwayTeam_Defense_Coeff']].to_numpy(), X['Match_Result_num'].to_numpy()
#%%
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)
#%%
print(f"Number of samples in dataset: {len(X)}")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

X_test, X_validation, y_test, y_validation = train_test_split(X_test, y_test, test_size=0.3)

print("Number of samples in:")
print(f"    Training: {len(y_train)}")
print(f"    Validation: {len(y_validation)}")
print(f"    Testing: {len(y_test)}")
#%%
models = [LogisticRegression(max_iter= 1000, multi_class = 'multinomial'),
KNeighborsClassifier(), RandomForestClassifier(), GradientBoostingClassifier()]


names = ['Logistic Regression', 'KNN', 'Random Forest', 'Gradient Boost']
#%%
for model, name in zip(models, names):
    start = time.time()
    model.fit(X_train, y_train)
    y_train_pred = model.predict(X_train)
    y_validation_pred = model.predict(X_validation)
    y_test_pred = model.predict(X_test)

    train_loss = mean_squared_error(y_train, y_train_pred)
    validation_loss = mean_squared_error(y_validation, y_validation_pred)
    test_loss = mean_squared_error(y_test, y_test_pred)

    print(
        f"{name}: ",
        f"\nTrain Loss: {train_loss} | Validation Loss: {validation_loss} | "
        f"Test Loss: {test_loss}",
        f"\nTime taken: {time.time() - start}",
        f"\nModel score: {model.score(X_test, y_test)}"
        )
    print(confusion_matrix(y_test, y_test_pred))
   
#%%
X = df[['HomeTeam_Attack_Coeff', 'HomeTeam_Defense_Coeff', 'AwayTeam_Attack_Coeff', 'AwayTeam_Defense_Coeff', 'Round', 'Match_Result']]
X, y = X[['HomeTeam_Attack_Coeff', 'HomeTeam_Defense_Coeff', 'AwayTeam_Attack_Coeff', 'AwayTeam_Defense_Coeff']].to_numpy(), X['Match_Result_num'].to_numpy()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)    
for model, name in zip(models, names):
    start = time.time()    
    scores = cross_val_score(model, X_train, y_train ,scoring= 'accuracy', cv=5)
    print(name, ":", "%0.3f, +- %0.3f" % (scores.mean(), scores.std()), " - Time taken: ", time.time() - start)
    
###
# todo: run models for all other features incl scraped features(go back and scrape historical elo
# Scale features first, plot best fits, categorical vars -> use pd.get_dummies().
#plot results of classifier training 
# ideas: get winning odds, scrape probs and compare with model probs, simulate betting winning

    
    
    
    
    
    



