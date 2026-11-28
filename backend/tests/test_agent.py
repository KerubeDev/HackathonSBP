from app.agent import safe_sql, build_chart
import pandas as pd
import pytest
def test_safe_sql_accepts_select(): assert safe_sql('SELECT 1;') == 'SELECT 1'
@pytest.mark.parametrize('query',['DROP TABLE sample_metrics','UPDATE sample_metrics SET value=1','DELETE FROM sample_metrics'])
def test_safe_sql_rejects_mutation(query):
    with pytest.raises(ValueError): safe_sql(query)

def test_safe_sql_accepts_with_and_rejects_multiple_statements():
    assert safe_sql("WITH x AS (SELECT 1) SELECT * FROM x") == "WITH x AS (SELECT 1) SELECT * FROM x"
    with pytest.raises(ValueError): safe_sql("SELECT 1; SELECT 2")

def test_chart_has_echarts_and_accessibility_contract():
    chart = build_chart(pd.DataFrame({"region": ["North"], "total": [3]}))
    assert chart["type"] == "bar"
    assert chart["series"][0]["data"] == [3]
    assert "accessibility" in chart and chart["fallback"] == "table"

def test_requested_chart_types_are_supported():
    frame = pd.DataFrame({"region": ["North"], "total": [3]})
    assert build_chart(frame, "line")["series"][0]["type"] == "line"
    assert build_chart(frame, "pie")["series"][0]["type"] == "pie"
    assert build_chart(frame, "not-a-chart")["type"] == "bar"
