# Research: SBP 2026 Local Uploads and Exports

## Scope

Primary-source research for the refined SBP template. No code was changed by this
research step.

## Findings

- [FastAPI request files](https://fastapi.tiangolo.com/tutorial/request-files/): use
  `UploadFile`; it uses a spooled file, exposes metadata, and avoids loading large
  uploads entirely into memory.
- [pandas.read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html):
  supports explicit `dtype`, `encoding`, `decimal`, bad-line handling, and `chunksize`.
  These are required to preserve SBP codes and process large files safely.
- [openpyxl documentation](https://openpyxl.readthedocs.io/en/stable/): provides XLSX
  read/write support for the Excel export requirement.
- [ReportLab introduction](https://docs.reportlab.com/reportlab/userguide/ch1_intro/):
  directly generates PDF documents, tables, and charts from Python.
- [Apache ECharts examples](https://echarts.apache.org/examples/en/index.html): remains
  the primary reference for dashboard chart options.

## Decisions

Use bounded `UploadFile` ingestion, explicit pandas text dtypes and chunking, openpyxl
for XLSX, ReportLab for PDF, and ECharts for frontend visualization.
