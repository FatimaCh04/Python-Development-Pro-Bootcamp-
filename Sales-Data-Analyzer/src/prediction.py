import sys
import pandas as pd
import numpy as np
import pickle
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Ensure project root is on sys.path so `config` is importable
# whether this file is run directly or imported as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import CLEANED_DATA_FILE, MODEL_FILE, CHARTS_DIR

logger = logging.getLogger(__name__)

# Consistent plot style
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({'figure.dpi': 300, 'savefig.dpi': 300})


class SalesPredictor:
    """
    Trains a Linear Regression model on monthly aggregated sales data,
    evaluates its performance, and predicts future revenue.

    All predictions are derived exclusively from the loaded dataset —
    no hard-coded or dummy values are used anywhere.
    """

    def __init__(self, data_file=CLEANED_DATA_FILE, model_file=MODEL_FILE):
        self.data_file = Path(data_file)
        self.model_file = Path(model_file)
        self.charts_dir = Path(CHARTS_DIR)
        self.df = None
        self.monthly_sales = pd.DataFrame()
        self.model: LinearRegression | None = None
        self.metrics: dict = {}
        self.X_train = self.X_test = self.y_train = self.y_test = None

    # ------------------------------------------------------------------ #
    #  Data Loading                                                        #
    # ------------------------------------------------------------------ #

    def load_data(self) -> None:
        """Loads the cleaned dataset and aggregates it to monthly granularity."""
        try:
            self.df = pd.read_csv(self.data_file)
            self.df["Date"] = pd.to_datetime(self.df["Date"])

            # Aggregate to monthly total sales — sorted chronologically
            monthly = (
                self.df.set_index("Date")["Sales"]
                .resample("ME")
                .sum()
                .reset_index()
                .sort_values("Date")
            )
            # Month_Index is the only feature: integer position (0, 1, 2, …)
            monthly["Month_Index"] = np.arange(len(monthly))
            self.monthly_sales = monthly

            logger.info(
                f"Loaded {len(self.df):,} rows -> {len(monthly)} monthly periods "
                f"({monthly['Date'].min().date()} to {monthly['Date'].max().date()})"
            )
        except FileNotFoundError:
            logger.error(f"Cleaned data not found at {self.data_file}. Run cleaning first.")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading data: {e}")
            raise

    # ------------------------------------------------------------------ #
    #  Model Training                                                      #
    # ------------------------------------------------------------------ #

    def train_model(self) -> dict:
        """
        Trains a Linear Regression model using an 80/20 chronological
        train/test split (shuffle=False preserves time order).

        Returns
        -------
        dict
            MAE, RMSE, and R² score computed on the held-out test set.
        """
        if self.monthly_sales.empty:
            self.load_data()

        X = self.monthly_sales[["Month_Index"]].values
        y = self.monthly_sales["Sales"].values

        # Chronological split — no shuffle so future data never leaks into training
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.20, shuffle=False
        )

        self.model = LinearRegression()
        self.model.fit(self.X_train, self.y_train)

        # Evaluate on unseen test months
        y_pred_test = self.model.predict(self.X_test)
        mae  = mean_absolute_error(self.y_test, y_pred_test)
        rmse = float(np.sqrt(mean_squared_error(self.y_test, y_pred_test)))
        r2   = r2_score(self.y_test, y_pred_test)

        self.metrics = {"MAE": mae, "RMSE": rmse, "R2_Score": r2}

        logger.info(
            f"Model trained -- Train: {len(self.X_train)} months | "
            f"Test: {len(self.X_test)} months | "
            f"MAE: {mae:,.2f} | RMSE: {rmse:,.2f} | R2: {r2:.4f}"
        )

        # Persist model to disk
        self._save_model()

        # Generate evaluation charts
        self.plot_regression_line()
        self.plot_predictions_vs_actual()

        return self.metrics

    # ------------------------------------------------------------------ #
    #  Model Persistence                                                   #
    # ------------------------------------------------------------------ #

    def _save_model(self) -> None:
        """Serialises the trained model to disk using Pickle."""
        try:
            with open(self.model_file, "wb") as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {self.model_file}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def load_model(self) -> bool:
        """
        Loads a previously saved model from disk.

        Returns
        -------
        bool
            True if the model was loaded successfully, False otherwise.
        """
        if not self.model_file.exists():
            logger.warning(f"No saved model found at {self.model_file}.")
            return False
        try:
            with open(self.model_file, "rb") as f:
                self.model = pickle.load(f)
            logger.info(f"Pre-trained model loaded from {self.model_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    # ------------------------------------------------------------------ #
    #  Prediction                                                          #
    # ------------------------------------------------------------------ #

    def predict_future(self) -> dict:
        """
        Predicts next month's and next quarter's (3 months) total sales
        using the trained or loaded model.

        Returns
        -------
        dict
            'Next_Month_Sales' and 'Next_Quarter_Sales' (floats, in $).
        """
        if self.model is None:
            loaded = self.load_model()
            if not loaded:
                logger.info("No saved model found — training a new one.")
                self.train_model()

        if self.monthly_sales.empty:
            self.load_data()

        last_index = int(self.monthly_sales["Month_Index"].max())

        # Single future month
        next_month_idx  = np.array([[last_index + 1]])
        next_month_pred = float(self.model.predict(next_month_idx)[0])
        next_month_pred = max(next_month_pred, 0.0)   # clamp: sales can't be negative

        # Next quarter = sum of next 3 months
        next_quarter_indices = np.array([[last_index + i] for i in range(1, 4)])
        next_quarter_pred    = float(self.model.predict(next_quarter_indices).sum())
        next_quarter_pred    = max(next_quarter_pred, 0.0)

        predictions = {
            "Next_Month_Sales":   round(next_month_pred, 2),
            "Next_Quarter_Sales": round(next_quarter_pred, 2),
        }
        logger.info(
            f"Predictions -- Next Month: ${next_month_pred:,.2f} | "
            f"Next Quarter: ${next_quarter_pred:,.2f}"
        )
        return predictions

    # ------------------------------------------------------------------ #
    #  Display                                                             #
    # ------------------------------------------------------------------ #

    def display_metrics(self) -> None:
        """Prints the model performance metrics and train/test split info."""
        if not self.metrics:
            logger.warning("No metrics available. Train the model first.")
            return

        train_size = len(self.X_train) if self.X_train is not None else "N/A"
        test_size  = len(self.X_test)  if self.X_test  is not None else "N/A"

        print("\n" + "="*40)
        print("  MODEL EVALUATION METRICS")
        print("="*40)
        print(f"  Train / Test Split : {train_size} / {test_size} months")
        print(f"  MAE                : ${self.metrics['MAE']:>12,.2f}")
        print(f"  RMSE               : ${self.metrics['RMSE']:>12,.2f}")
        print(f"  R² Score           : {self.metrics['R2_Score']:>13.4f}")
        print("="*40 + "\n")

    # ------------------------------------------------------------------ #
    #  Visualisations                                                      #
    # ------------------------------------------------------------------ #

    def plot_regression_line(self) -> None:
        """Plots the full regression line overlaid on actual monthly sales."""
        if self.model is None or self.monthly_sales.empty:
            logger.warning("Model or data not ready — skipping regression line plot.")
            return

        X_all = self.monthly_sales[["Month_Index"]].values
        y_all = self.monthly_sales["Sales"].values
        y_fit = self.model.predict(X_all)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.scatter(X_all, y_all, color="#1f77b4", alpha=0.7, s=40, label="Actual Monthly Sales")
        ax.plot(X_all, y_fit, color="#d62728", linewidth=2.5, label="Regression Line")

        ax.set_title("Linear Regression — Monthly Sales Fit", fontsize=18)
        ax.set_xlabel("Month Index (0 = first month of data)", fontsize=13)
        ax.set_ylabel("Total Monthly Sales ($)", fontsize=13)
        ax.legend()

        self._save_chart(fig, "regression_line.png")

    def plot_predictions_vs_actual(self) -> None:
        """Plots actual vs predicted values on the held-out test set."""
        if self.X_test is None or self.model is None:
            logger.warning("Test data not available — skipping predictions chart.")
            return

        y_pred = self.model.predict(self.X_test)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.y_test, marker="o", linewidth=2, label="Actual Sales",    color="#2ca02c")
        ax.plot(y_pred,      marker="s", linewidth=2, label="Predicted Sales", color="#ff7f0e", linestyle="--")

        ax.set_title("Actual vs Predicted Sales — Test Set", fontsize=18)
        ax.set_xlabel("Test Month (sequential)", fontsize=13)
        ax.set_ylabel("Monthly Sales ($)", fontsize=13)
        ax.legend()

        self._save_chart(fig, "prediction_graph.png")

    def _save_chart(self, fig: plt.Figure, filename: str) -> None:
        """Helper to save a matplotlib figure to the charts directory."""
        filepath = self.charts_dir / filename
        try:
            fig.tight_layout()
            fig.savefig(filepath, bbox_inches="tight")
            plt.close(fig)
            logger.info(f"Chart saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save chart {filename}: {e}")
            plt.close(fig)


# ------------------------------------------------------------------ #
#  Standalone execution                                               #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    predictor = SalesPredictor()
    metrics   = predictor.train_model()
    predictor.display_metrics()

    future = predictor.predict_future()
    print(f"Next Month Predicted Sales   : ${future['Next_Month_Sales']:,.2f}")
    print(f"Next Quarter Predicted Sales : ${future['Next_Quarter_Sales']:,.2f}")
