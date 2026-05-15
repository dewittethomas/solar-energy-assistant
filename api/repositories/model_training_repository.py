from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

class ModelTrainingRepository:
    def train_and_export(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        output_path: Path,
        optimize: bool = False,
        n_trials: int = 50,
        optimization_profile: str = 'hourly'
    ) -> dict[str, object]:
        self._validate_training_data(features, target)

        x = features.to_numpy(dtype=np.float32)
        y = target.to_numpy(dtype=np.float32)
        x_train, x_validation, x_test, y_train, y_validation, y_test = (
            self._split_data(x, y)
        )
        best_params = (
            self._optimize_params(
                x_train,
                y_train,
                x_validation,
                y_validation,
                n_trials,
                optimization_profile
            )
            if optimize
            else {}
        )
        training_mode = 'optuna' if optimize else 'xgboost_default'
        model = self._fit_model(x_train, y_train, best_params)
        train_metrics = self._calculate_metrics(y_train, model.predict(x_train))
        validation_metrics = self._calculate_metrics(
            y_validation,
            model.predict(x_validation)
        )
        test_metrics = self._calculate_metrics(
            y_test,
            model.predict(x_test)
        )
        overfitting = self._check_overfitting(
            train_metrics,
            validation_metrics,
            test_metrics
        )
        self._export_onnx(model, output_path, features.shape[1])

        return {
            'model_path': output_path,
            'train_rows': len(x_train),
            'validation_rows': len(x_validation),
            'test_rows': len(x_test),
            'best_params': best_params,
            'training_mode': training_mode,
            'metrics': self._calculate_public_metrics(
                train_metrics,
                validation_metrics,
                test_metrics
            ),
            'train_metrics': train_metrics,
            'validation_metrics': validation_metrics,
            'test_metrics': test_metrics,
            'overfitting': overfitting
        }

    def _validate_training_data(
        self,
        features: pd.DataFrame,
        target: pd.Series
    ) -> None:
        if len(features) < 10:
            raise ValueError('At least 10 matched training rows are required')

        if len(features) != len(target):
            raise ValueError('Feature and target row counts do not match')

    def _split_data(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        x_train, x_split, y_train, y_split = train_test_split(
            x,
            y,
            test_size=0.3,
            random_state=42,
            shuffle=False
        )
        x_validation, x_test, y_validation, y_test = train_test_split(
            x_split,
            y_split,
            test_size=0.5,
            random_state=42,
            shuffle=False
        )

        return x_train, x_validation, x_test, y_train, y_validation, y_test

    def _optimize_params(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_validation: np.ndarray,
        y_validation: np.ndarray,
        n_trials: int,
        optimization_profile: str
    ) -> dict[str, int | float]:
        import optuna

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        def objective(trial):
            params = self._suggest_params(trial, optimization_profile)
            model = self._fit_model(x_train, y_train, params)
            predictions = model.predict(x_validation)

            return mean_absolute_error(y_validation, predictions)

        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials)

        return study.best_params

    def _suggest_params(
        self,
        trial,
        optimization_profile: str
    ) -> dict[str, int | float]:
        if optimization_profile == 'monthly':
            return {
                'max_depth': trial.suggest_int('max_depth', 2, 4),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.15),
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'subsample': trial.suggest_float('subsample', 0.7, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 1.0),
                'min_child_weight': trial.suggest_float('min_child_weight', 2.0, 12.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-3, 2.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 2.0, 15.0),
                'gamma': trial.suggest_float('gamma', 0.0, 2.0)
            }

        return {
            'max_depth': trial.suggest_int('max_depth', 3, 6),
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.2),
            'n_estimators': trial.suggest_int('n_estimators', 100, 700),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_float('min_child_weight', 1.0, 10.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-4, 1.0, log=True),
            'reg_lambda': trial.suggest_float('reg_lambda', 1.0, 10.0),
            'gamma': trial.suggest_float('gamma', 0.0, 1.0)
        }

    def _fit_model(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        params: dict[str, int | float]
    ):
        from xgboost import XGBRegressor

        model = XGBRegressor(
            random_state=42,
            objective='reg:squarederror',
            n_jobs=2,
            **params
        )
        model.fit(x_train, y_train)

        return model

    def _calculate_metrics(
        self,
        actual: np.ndarray,
        predicted: np.ndarray
    ) -> dict[str, float]:
        mse = mean_squared_error(actual, predicted)

        return {
            'r2': float(r2_score(actual, predicted)),
            'mae': float(mean_absolute_error(actual, predicted)),
            'mse': float(mse),
            'rmse': float(np.sqrt(mse))
        }

    def _calculate_public_metrics(
        self,
        train_metrics: dict[str, float],
        validation_metrics: dict[str, float],
        test_metrics: dict[str, float]
    ) -> dict[str, float]:
        metric_names = ['r2', 'mae', 'mse', 'rmse']

        return {
            name: float(
                np.mean([
                    train_metrics[name],
                    validation_metrics[name],
                    test_metrics[name]
                ])
            )
            for name in metric_names
        }

    def _check_overfitting(
        self,
        train_metrics: dict[str, float],
        validation_metrics: dict[str, float],
        test_metrics: dict[str, float]
    ) -> dict[str, float | str]:
        train_validation_r2_gap = (
            train_metrics['r2'] - validation_metrics['r2']
        )
        train_test_r2_gap = train_metrics['r2'] - test_metrics['r2']
        validation_test_r2_gap = validation_metrics['r2'] - test_metrics['r2']
        train_validation_mae_ratio = (
            validation_metrics['mae'] / train_metrics['mae']
            if train_metrics['mae'] > 0
            else float('inf')
        )
        train_test_mae_ratio = (
            test_metrics['mae'] / train_metrics['mae']
            if train_metrics['mae'] > 0
            else float('inf')
        )
        likely_validation_gap = (
            train_validation_r2_gap >= 0.20
            or (
                train_validation_mae_ratio >= 1.75
                and train_validation_r2_gap >= 0.05
            )
        )
        likely_test_gap = (
            train_test_r2_gap >= 0.20
            or (
                train_test_mae_ratio >= 1.75
                and train_test_r2_gap >= 0.05
            )
        )
        possible_validation_gap = (
            train_validation_r2_gap >= 0.10
            or (
                train_validation_mae_ratio >= 1.35
                and train_validation_r2_gap >= 0.05
            )
        )
        possible_test_gap = (
            train_test_r2_gap >= 0.10
            or (
                train_test_mae_ratio >= 1.35
                and train_test_r2_gap >= 0.05
            )
        )

        if (
            (likely_validation_gap and possible_test_gap)
            or (possible_validation_gap and likely_test_gap)
        ):
            status = 'likely_overfitting'
            message = (
                'Training performance is much better than validation and test performance.'
            )
        elif possible_validation_gap and possible_test_gap:
            status = 'possible_overfitting'
            message = (
                'Training performance is noticeably better than validation and test performance.'
            )
        elif possible_validation_gap:
            status = 'no_clear_overfitting'
            message = (
                'Validation performance is weaker than training performance, '
                'but test performance stays close; no clear overfitting.'
            )
        else:
            status = 'no_clear_overfitting'
            message = (
                'Train, validation, and test performance are reasonably close.'
            )

        if validation_test_r2_gap > 0.10:
            if status == 'no_clear_overfitting':
                status = 'possible_distribution_shift'
                message = (
                    'Test performance is weaker than validation performance; '
                    'check whether the latest time period differs from training data.'
                )
            else:
                message = (
                    f'{message} Test performance is also weaker than validation '
                    'performance, so check whether the latest time period differs.'
                )

        return {
            'status': status,
            'train_validation_r2_gap': float(train_validation_r2_gap),
            'train_test_r2_gap': float(train_test_r2_gap),
            'validation_test_r2_gap': float(validation_test_r2_gap),
            'train_validation_mae_ratio': float(train_validation_mae_ratio),
            'train_test_mae_ratio': float(train_test_mae_ratio),
            'message': message
        }

    def _export_onnx(
        self,
        model,
        output_path: Path,
        feature_count: int
    ) -> None:
        import onnxmltools
        from onnxconverter_common.data_types import FloatTensorType

        output_path.parent.mkdir(parents=True, exist_ok=True)
        onnx_model = onnxmltools.convert_xgboost(
            model,
            initial_types=[('input', FloatTensorType([None, feature_count]))]
        )
        output_path.write_bytes(onnx_model.SerializeToString())
