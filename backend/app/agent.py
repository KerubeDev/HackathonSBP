"""Generic REA graph: Reason -> Execute -> Iterate, with ask-to NL-to-SQL seam."""
from typing import Any, TypedDict
import json, re
import pandas as pd
from sqlalchemy import create_engine, text
from langgraph.graph import StateGraph, END
from .config import settings

class AgentState(TypedDict, total=False):
    request: str; schema: str; sql: str; rows: list[dict[str, Any]]; summary: str
    chart_config: dict[str, Any]; error: str; attempts: int; provider: str

engine = create_engine(settings.database_url, pool_pre_ping=True)

def schema_context() -> str:
    return """Tables: sample_metrics(metric_date DATE, category TEXT, value NUMERIC, region TEXT)."""

def safe_sql(sql: str) -> str:
    sql = sql.strip().removeprefix('```sql').removesuffix('```').strip().rstrip(';')
    if not re.match(r'(?is)^select\b', sql) or re.search(r'(?is)\b(insert|update|delete|drop|alter|truncate|create|grant|revoke)\b', sql):
        raise ValueError('Only read-only SELECT statements are allowed')
    return sql

def input_node(state: AgentState) -> AgentState:
    return {**state, 'schema': state.get('schema') or schema_context(), 'attempts': 0}

def _fallback_sql(request: str) -> str:
    q = request.lower()
    if 'region' in q: return 'SELECT region, SUM(value) AS total_value FROM sample_metrics GROUP BY region ORDER BY total_value DESC'
    if 'category' in q: return 'SELECT category, SUM(value) AS total_value FROM sample_metrics GROUP BY category ORDER BY total_value DESC'
    return 'SELECT metric_date, category, value, region FROM sample_metrics ORDER BY metric_date DESC LIMIT 100'

def _ask_to_sql(request: str, schema: str) -> tuple[str, str]:
    # Provider seam: OpenRouter first, Ollama fallback. Keeping the prompt generic is intentional.
    if settings.openrouter_api_key:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=settings.openrouter_model, api_key=settings.openrouter_api_key, base_url='https://openrouter.ai/api/v1', temperature=0)
        answer = llm.invoke(f"Return only SQL. User question: {request}\nSchema: {schema}")
        return safe_sql(answer.content), 'openrouter'
    try:
        import httpx
        r = httpx.post(f'{settings.ollama_base_url}/api/generate', json={'model': settings.local_model, 'prompt': f'Return only SQL. Question: {request}\nSchema: {schema}', 'stream': False}, timeout=20)
        r.raise_for_status(); return safe_sql(r.json()['response']), 'ollama'
    except Exception:
        return _fallback_sql(request), 'deterministic-fallback'

def analysis_node(state: AgentState) -> AgentState:
    try:
        sql, provider = _ask_to_sql(state['request'], state['schema'])
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn).head(settings.agent_max_rows)
        rows = json.loads(df.to_json(orient='records', date_format='iso'))
        chart = {'type': 'bar', 'data': {'labels': list(df.iloc[:,0].astype(str)) if len(df.columns) else [], 'datasets': [{'label': str(df.columns[-1]) if len(df.columns) else 'value', 'data': df.iloc[:,-1].tolist() if len(df.columns) else []}]}}
        return {**state, 'sql': sql, 'rows': rows, 'chart_config': chart, 'provider': provider, 'attempts': state.get('attempts',0)+1}
    except Exception as exc:
        if state.get('attempts', 0) < 1: return {**state, 'attempts': state.get('attempts',0)+1, 'error': str(exc)}
        return {**state, 'error': str(exc)}

def output_node(state: AgentState) -> AgentState:
    return {**state, 'summary': f"Returned {len(state.get('rows', []))} rows for the requested analysis."}

def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node('input_node', input_node)
    graph.add_node('analysis_node', analysis_node)
    graph.add_node('output_node', output_node)
    graph.set_entry_point('input_node')
    graph.add_edge('input_node', 'analysis_node')
    graph.add_edge('analysis_node', 'output_node')
    graph.add_edge('output_node', END)
    return graph.compile()

REA_GRAPH = _build_graph()

def run_agent(request: str, schema: str | None = None) -> dict[str, Any]:
    state = REA_GRAPH.invoke({'request': request, 'schema': schema or ''})
    if state.get('error') and state.get('attempts', 0) < 2:
        state = output_node(analysis_node(state))
    return {'summary': state.get('summary',''), 'sql_query': state.get('sql',''), 'data': state.get('rows',[]), 'chart_config': state.get('chart_config',{}), 'provider': state.get('provider'), 'error': state.get('error')}
