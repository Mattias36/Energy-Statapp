from collections import defaultdict
import numpy as np

def predict_future_usage(data, years_to_predict=5, zero_threshold=0.001):
    """
    return:    dict: {source_name: {future_year: predicted_value, ...}, ...}
    Values below zero_threshold == 0.
    """
    source_data = defaultdict(list)
    for d in data:
        source_data[d.source.name].append((d.year, d.value))

    predictions = {}
    for source, values in source_data.items():
        values = sorted(values, key=lambda x: x[0])
        years = np.array([v[0] for v in values])
        vals = np.array([v[1] for v in values])

        if len(years) < 2:
            continue

        # macierz A, każda kolumna to: [rok, 1]
        #  łączy listy years i jedynek w pionie
        A = np.vstack([years, np.ones(len(years))]).T
        # wsp y = a*rok + b
        # równanie A * [a,b] = vals metodą least squares
        a, b = np.linalg.lstsq(A, vals, rcond=None)[0]
        last_year = years[-1]
        future_preds = {}

        for i in range(1, years_to_predict + 1):
            year = last_year + i
            pred_val = a * year + b
            pred_val = max(pred_val, 0)  # no negatives
            if pred_val < zero_threshold:
                pred_val = 0
            future_preds[year] = round(pred_val, 3)

        predictions[source] = future_preds

    return predictions


def format_future_usage(data):
    raw_predictions = predict_future_usage(data)
    formatted = {}

    for source, preds in raw_predictions.items():
        if all(val == 0 for val in preds.values()):
            continue

        tooltip = "\n".join(f"{year}: {val:.3f} Mtoe" for year, val in preds.items())
        formatted[source] = {
            "predictions": preds,
            "tooltip": tooltip
        }

    return formatted
