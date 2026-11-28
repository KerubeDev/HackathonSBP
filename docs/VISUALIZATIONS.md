# Visualization Catalog

## Purpose

The dashboard uses Apache ECharts. The official examples are the visual and
technical reference:

<https://echarts.apache.org/examples/en/index.html>

The catalog is an extensible set of adapters. A chart is never the only
representation: the result must remain understandable through a table.

## Hackathon catalog

The planned baseline catalog supports:

- table;
- bar;
- line;
- area;
- pie/donut;
- scatter;
- radar;
- heatmap;
- funnel;
- gauge;
- treemap;
- boxplot;
- calendar.

Sankey, graph, sunburst, parallel coordinates, maps, 3D, and candlestick are
roadmap adapters. Specialized charts require explicit configuration and stricter
limits.

## Selection and safety

Deterministic rules inspect column types, cardinality, series count, nulls, and
data shape. A model may suggest a chart only from the allowed catalog; the backend
validates the suggestion before rendering. If validation fails, the analysis still
returns its table and a sanitized warning.

The versioned `chart_config` contract should include `type`, `title`, `description`,
`x_field`, `y_fields`, `series`, `encoding`, `accessibility`, `confidence`,
`fallback`, and `schema_version`.

Initial display limits are configurable: 1,000 points per series, 20 series, and
50 visible categories. Exceeding a limit requires aggregation, sampling, or
truncation with a warning and a table/pagination fallback.

## Accessibility

Every adapter must provide an accessible title or description, sufficient contrast,
colorblind-safe palettes, legends for multiple series, and a non-visual table
alternative. Tooltips and color must not be the only way to understand a result.
Keyboard support is required where the interaction supports it.

## Adapter contract

Each adapter declares its name and version, compatible data types, cardinality
limits, deterministic selection rule, ECharts generator, validator, accessibility
requirements, fallback, fixtures, and tests. No adapter is complete without unit,
configuration, empty/null/overflow, accessibility, and visual checks.
