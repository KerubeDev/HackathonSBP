from typing import Any
import pandas as pd

SUPPORTED_CHARTS = (
    "table", "bar", "line", "area", "pie", "scatter", "radar", "heatmap",
    "funnel", "gauge", "treemap", "boxplot", "calendar",
)

def choose_chart(df: pd.DataFrame, requested: str | None = None) -> dict[str, Any]:
    if requested not in SUPPORTED_CHARTS:
        requested = "bar" if len(df.columns) >= 2 and not df.empty else "table"
    if requested == "table" or df.empty:
        return {"type": "table", "schema_version": "1.0", "fallback": "table",
                "accessibility": {"description": "Use the accessible results table."}}
    x = str(df.columns[0])
    numeric = list(df.select_dtypes(include="number").columns)
    y = str(numeric[0] if numeric else df.columns[-1])
    labels = df[x].astype(str).tolist()
    values = df[y].tolist()
    series_type = "line" if requested in {"line", "area", "calendar"} else requested
    series: dict[str, Any] = {"type": series_type, "name": y, "data": values}
    if requested == "area":
        series["areaStyle"] = {}
    option: dict[str, Any] = {
        "type": requested, "title": f"{y} by {x}", "description": f"{requested} chart of {y} by {x}.",
        "x_field": x, "y_fields": [y], "encoding": {"x": "category", "y": "value"},
        "series": [series], "schema_version": "1.0", "fallback": "table",
        "accessibility": {"description": f"Accessible table and {requested} chart for {y} by {x}."},
    }
    if requested == "pie":
        option["series"] = [{"type": "pie", "name": y, "data": [{"name": k, "value": v} for k, v in zip(labels, values)]}]
    elif requested == "gauge":
        option["series"] = [{"type": "gauge", "data": [{"value": values[-1] if values else 0, "name": y}]}]
    elif requested in {"treemap", "funnel"}:
        option["series"] = [{"type": requested, "data": [{"name": k, "value": v} for k, v in zip(labels, values)]}]
    elif requested == "scatter":
        option["series"] = [{"type": "scatter", "data": [[i, v] for i, v in enumerate(values)]}]
    elif requested == "radar":
        option["radar"] = {"indicator": [{"name": k, "max": max(values or [1])} for k in labels]}
        option["series"] = [{"type": "radar", "data": [{"value": values, "name": y}]}]
    else:
        option["xAxis"] = {"type": "category", "data": labels}
        option["yAxis"] = {"type": "value"}
    return option
