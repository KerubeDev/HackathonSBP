"""Generic REA graph: Reason -> Execute -> Iterate, with ask-to NL-to-SQL seam."""
from typing import Any, TypedDict
import json, re
import pandas as pd
from sqlalchemy import create_engine, text
from langgraph.graph import StateGraph, END
from .config import settings
from .visualizations import choose_chart

class AgentState(TypedDict, total=False):
    request: str; schema: str; sql: str; rows: list[dict[str, Any]]; summary: str
    chart_config: dict[str, Any]; error: str; attempts: int; provider: str; requested_chart_types: list[str]

engine = create_engine(settings.readonly_database_url, pool_pre_ping=True)

def schema_context() -> str:
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' ORDER BY table_name, ordinal_position"
        )).all()
    if not rows:
        return "No public tables are available."
    return "\n".join(f"{table}.{column}: {kind}" for table, column, kind in rows)

def safe_sql(sql: str) -> str:
    sql = sql.strip().removeprefix('```sql').removesuffix('```').strip().rstrip(';')
    if not re.match(r'(?is)^(select|with)\b', sql) or ";" in sql or re.search(r'(?is)\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|execute)\b', sql):
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
    prompt = f"Return only SQL. User question: {request}\nSchema:\n{schema}"
    if settings.llm_provider == "openrouter":
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=settings.openrouter_model, api_key=settings.openrouter_api_key, base_url='https://openrouter.ai/api/v1', temperature=0)
        return safe_sql(llm.invoke(prompt).content), 'openrouter'
    if settings.llm_provider in {"ollama", "qvac"}:
        import httpx
        if settings.llm_provider == "ollama":
            url, payload, model = f'{settings.ollama_base_url}/api/generate', {'model': settings.local_model, 'prompt': prompt, 'stream': False}, settings.local_model
            r = httpx.post(url, json=payload, timeout=20)
            r.raise_for_status()
            return safe_sql(r.json()['response']), f'ollama:{model}'
        url = f'{settings.qvac_base_url}/v1/chat/completions'
        r = httpx.post(url, json={'model': settings.qvac_model, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0}, timeout=20)
        r.raise_for_status(); return safe_sql(r.json()['choices'][0]['message']['content']), f'qvac:{settings.qvac_model}'
    if settings.llm_provider == "deterministic" and settings.allow_deterministic_fallback:
        return _fallback_sql(request), 'deterministic-fallback'
    raise ValueError(f"Unsupported or disabled LLM_PROVIDER: {settings.llm_provider}")

def build_chart(df: pd.DataFrame, requested: str | None = None) -> dict[str, Any]:
    return choose_chart(df, requested)

def analysis_node(state: AgentState) -> AgentState:
    try:
        sql, provider = _ask_to_sql(state['request'], state['schema'])
        with engine.connect() as conn:
            conn.execute(text(f"SET statement_timeout = {int(settings.statement_timeout_ms)}"))
            df = pd.read_sql(text(sql), conn).head(min(settings.agent_max_rows, settings.max_request_rows))
        rows = json.loads(df.to_json(orient='records', date_format='iso'))
        requested = next(iter(state.get("requested_chart_types", [])), None)
        chart = build_chart(df, requested)
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

def run_agent(request: str, schema: str | None = None, requested_chart_types: list[str] | None = None) -> dict[str, Any]:
    state = REA_GRAPH.invoke({'request': request, 'schema': schema or '', 'requested_chart_types': requested_chart_types or []})
    if state.get('error') and state.get('attempts', 0) < 2:
        state = output_node(analysis_node(state))
    return {'api_version': 'v1', 'summary': state.get('summary',''), 'sql_query': state.get('sql',''), 'data': state.get('rows',[]), 'chart_config': state.get('chart_config',{}), 'provider': state.get('provider'), 'model': settings.openrouter_model if settings.llm_provider == 'openrouter' else (settings.local_model if settings.llm_provider == 'ollama' else settings.qvac_model), 'execution_mode': settings.execution_mode, 'status': 'failed' if state.get('error') else 'completed', 'metadata': {'row_count': len(state.get('rows', [])), 'truncated': len(state.get('rows', [])) >= settings.agent_max_rows}, 'warnings': ['Result may be truncated.'] if len(state.get('rows', [])) >= settings.agent_max_rows else [], 'error': state.get('error')}
