from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split


class ModelTrainingRepository:
    def train_and_export(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        output_path: Path,
        optimize: bool = False,
        n_trials: int = 50,
        optimization_profile: str = 'hourly',
        trial_callback=None,
    ) -> dict[str, object]:
        del optimization_profile
        self._validate_training_data(features, target)

        x_train, x_validation, x_test, y_train, y_validation, y_test = (
            self._split_data(features, target)
        )
        best_params = (
            self._optimize_params(
                x_train,
                y_train,
                x_validation,
                y_validation,
                n_trials,
                trial_callback=trial_callback,
            )
            if optimize
            else {}
        )
        training_mode = 'optuna' if optimize else 'catboost_default'
        diagnostic_model = self._fit_model(
            x_train,
            y_train,
            x_validation,
            y_validation,
            best_params,
        )
        train_metrics = self._calculate_metrics(
            y_train.to_numpy(dtype=np.float32),
            diagnostic_model.predict(x_train),
        )
        validation_metrics = self._calculate_metrics(
            y_validation.to_numpy(dtype=np.float32),
            diagnostic_model.predict(x_validation),
        )
        x_train_final = pd.concat([x_train, x_validation], axis=0)
        y_train_final = pd.concat([y_train, y_validation], axis=0)
        final_model = self._fit_final_model(
            x_train_final,
            y_train_final,
            best_params,
        )
        test_predictions = final_model.predict(x_test)
        test_metrics = self._calculate_metrics(
            y_test.to_numpy(dtype=np.float32),
            test_predictions,
        )
        overfitting = self._check_overfitting(
            train_metrics,
            validation_metrics,
            test_metrics,
        )
        self._export_onnx(final_model, output_path)

        return {
            'model_path': output_path,
            'train_rows': len(x_train),
            'validation_rows': len(x_validation),
            'test_rows': len(x_test),
            'best_params': best_params,
            'training_mode': training_mode,
            'metrics': test_metrics,
            'train_metrics': train_metrics,
            'validation_metrics': validation_metrics,
            'test_metrics': test_metrics,
            'overfitting': overfitting,
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
        features: pd.DataFrame,
        target: pd.Series
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        x_train, x_split, y_train, y_split = train_test_split(
            features,
            target,
            test_size=0.3,
            random_state=42,
            shuffle=False,
        )
        x_validation, x_test, y_validation, y_test = train_test_split(
            x_split,
            y_split,
            test_size=0.5,
            random_state=42,
            shuffle=False,
        )

        return x_train, x_validation, x_test, y_train, y_validation, y_test

    def _optimize_params(
        self,
        x_train: pd.DataFrame,
        y_train: pd.Series,
        x_validation: pd.DataFrame,
        y_validation: pd.Series,
        n_trials: int,
        trial_callback=None
    ) -> dict[str, int | float]:
        import optuna

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        def objective(trial):
            params = self._suggest_params(trial)
            model = self._fit_model(
                x_train,
                y_train,
                x_validation,
                y_validation,
                params,
            )
            predictions = model.predict(x_validation)
            return float(root_mean_squared_error(y_validation, predictions))

        study = optuna.create_study(direction='minimize')
        callbacks = []

        if trial_callback is not None:
            def on_trial_complete(study, trial) -> None:
                del trial
                best_value = (
                    float(study.best_value)
                    if study.best_trial is not None
                    else None
                )
                trial_callback(len(study.trials), n_trials, best_value)

            callbacks.append(on_trial_complete)

        study.optimize(objective, n_trials=n_trials, callbacks=callbacks)

        return study.best_params

    def _suggest_params(self, trial) -> dict[str, int | float]:
        return {
            'iterations': trial.suggest_int('iterations', 100, 1000),
            'learning_rate': trial.suggest_float(
                'learning_rate',
                1e-3,
                1.0,
                log=True,
            ),
            'depth': trial.suggest_int('depth', 3, 6),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bylevel': trial.suggest_float(
                'colsample_bylevel',
                0.5,
                1.0,
            ),
            'min_data_in_leaf': trial.suggest_int(
                'min_data_in_leaf',
                1,
                100,
            ),
        }

    def _fit_model(
        self,
        x_train: pd.DataFrame,
        y_train: pd.Series,
        x_validation: pd.DataFrame,
        y_validation: pd.Series,
        params: dict[str, int | float]
    ):
        import catboost as cb

        model = cb.CatBoostRegressor(
            loss_function='RMSE',
            random_seed=42,
            verbose=False,
            **params,
        )
        model.fit(
            x_train,
            y_train,
            eval_set=(x_validation, y_validation),
            use_best_model=True,
            early_stopping_rounds=50,
        )

        return model

    def _fit_final_model(
        self,
        x_train: pd.DataFrame,
        y_train: pd.Series,
        params: dict[str, int | float]
    ):
        import catboost as cb

        model = cb.CatBoostRegressor(
            loss_function='RMSE',
            random_seed=42,
            verbose=False,
            **params,
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
            'rmse': float(np.sqrt(mse)),
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
            'message': message,
        }

    def _export_onnx(self, model, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(output_path), format='onnx')
