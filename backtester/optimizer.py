"""
backtester/optimizer.py
Grid search and walk-forward optimisation for strategy parameters.
"""
from __future__ import annotations

import itertools
import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from backtester.engine import BacktestEngine, BacktestConfig

logger = logging.getLogger(__name__)


@dataclass
class OptimisationResult:
    best_params:  dict
    best_metric:  float
    all_results:  pd.DataFrame
    metric_name:  str


class StrategyOptimizer:
    """
    Grid search and walk-forward strategy parameter optimisation.
    """

    def __init__(
        self,
        strategy_class,
        data: Dict[str, pd.DataFrame],
        config: BacktestConfig,
        n_jobs: int = -1,
    ) -> None:
        self.strategy_class = strategy_class
        self.data    = data
        self.config  = config
        self.n_jobs  = n_jobs

    # ──────────────────────────────────────────
    # Grid Search
    # ──────────────────────────────────────────

    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        metric: str = "sharpe",
        maximize: bool = True,
    ) -> OptimisationResult:
        """
        Exhaustive grid search over *param_grid*.

        Parameters
        ----------
        param_grid : {param_name: [value1, value2, ...]}
        metric     : performance metric to optimise (e.g. "sharpe", "calmar")
        maximize   : True to maximise metric, False to minimise

        Returns
        -------
        OptimisationResult with best params and all results DataFrame
        """
        keys   = list(param_grid.keys())
        values = list(param_grid.values())
        combos = list(itertools.product(*values))
        logger.info("Grid search: %d parameter combinations", len(combos))

        def _run(combo: tuple) -> Optional[Dict]:
            params = dict(zip(keys, combo))
            try:
                strategy = self.strategy_class(params=params)
                engine   = BacktestEngine(strategy, self.data, deepcopy(self.config))
                result   = engine.run()
                row = {**params, metric: result.performance.get(metric, np.nan)}
                row["sharpe"]  = result.performance.get("sharpe", np.nan)
                row["calmar"]  = result.performance.get("calmar", np.nan)
                row["cagr"]    = result.performance.get("cagr", np.nan)
                row["max_drawdown"] = result.performance.get("max_drawdown", np.nan)
                return row
            except Exception as exc:
                logger.debug("Combo %s failed: %s", params, exc)
                return None

        rows = Parallel(n_jobs=self.n_jobs)(delayed(_run)(c) for c in combos)
        rows = [r for r in rows if r is not None]

        if not rows:
            raise RuntimeError("All parameter combinations failed")

        df = pd.DataFrame(rows)
        best_idx = df[metric].idxmax() if maximize else df[metric].idxmin()
        best_row = df.loc[best_idx]

        return OptimisationResult(
            best_params  = {k: best_row[k] for k in keys},
            best_metric  = float(best_row[metric]),
            all_results  = df.sort_values(metric, ascending=not maximize).reset_index(drop=True),
            metric_name  = metric,
        )

    # ──────────────────────────────────────────
    # Walk-Forward Optimisation
    # ──────────────────────────────────────────

    def walk_forward(
        self,
        param_grid: Dict[str, List[Any]],
        train_years: int = 3,
        test_years:  int = 1,
        metric:      str = "sharpe",
    ) -> pd.DataFrame:
        """
        Walk-forward analysis: roll a train/test window through history.

        Returns DataFrame of out-of-sample results per fold.
        """
        # Determine date range from data
        all_dates: List[pd.Timestamp] = []
        for df in self.data.values():
            all_dates.extend(df.index.tolist())
        all_dates = sorted(set(all_dates))
        if not all_dates:
            return pd.DataFrame()

        start = all_dates[0]
        end   = all_dates[-1]

        train_td = pd.DateOffset(years=train_years)
        test_td  = pd.DateOffset(years=test_years)

        fold_results = []
        fold_start   = start

        while True:
            train_end = fold_start + train_td
            test_end  = train_end  + test_td
            if test_end > end:
                break

            # In-sample optimisation
            in_config = deepcopy(self.config)
            in_config.start_date = str(fold_start.date())
            in_config.end_date   = str(train_end.date())
            in_optimizer = StrategyOptimizer(
                self.strategy_class, self.data, in_config, self.n_jobs
            )
            try:
                opt_result = in_optimizer.grid_search(param_grid, metric)
                best_params = opt_result.best_params
            except Exception as exc:
                logger.warning("Walk-forward fold failed: %s", exc)
                fold_start += test_td
                continue

            # Out-of-sample evaluation
            oos_config = deepcopy(self.config)
            oos_config.start_date = str(train_end.date())
            oos_config.end_date   = str(test_end.date())
            strategy = self.strategy_class(params=best_params)
            engine   = BacktestEngine(strategy, self.data, oos_config)
            result   = engine.run()

            row = {
                "fold_start":  fold_start.date(),
                "train_end":   train_end.date(),
                "test_end":    test_end.date(),
                **best_params,
                "oos_sharpe":  result.performance.get("sharpe", np.nan),
                "oos_cagr":    result.performance.get("cagr", np.nan),
                "oos_mdd":     result.performance.get("max_drawdown", np.nan),
                "oos_calmar":  result.performance.get("calmar", np.nan),
            }
            fold_results.append(row)
            logger.info("WF fold %s → %s: OOS sharpe=%.2f",
                        fold_start.date(), test_end.date(), row["oos_sharpe"])
            fold_start += test_td

        return pd.DataFrame(fold_results)
