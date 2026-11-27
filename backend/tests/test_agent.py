from app.agent import safe_sql
import pytest
def test_safe_sql_accepts_select(): assert safe_sql('SELECT 1;') == 'SELECT 1'
@pytest.mark.parametrize('query',['DROP TABLE sample_metrics','UPDATE sample_metrics SET value=1','DELETE FROM sample_metrics'])
def test_safe_sql_rejects_mutation(query):
    with pytest.raises(ValueError): safe_sql(query)
