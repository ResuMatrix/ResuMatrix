from xgboost import XGBClassifier


def train_xgboost(X_train, y_train):
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)

    return model


def predict_xgboost(data, model):
    return model.predict(data)

