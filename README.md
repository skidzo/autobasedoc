# AutoBaseDoc

Automated PDF document generation on top of ReportLab with Matplotlib integration, reusable page templates, and helpers for tables, headers, footers, and table-of-contents handling.

![Documentation Status](https://readthedocs.org/projects/autobasedoc/badge/?version=latest)
![Current Version PyPI](https://img.shields.io/pypi/v/autobasedoc.svg)
![Python Version](https://img.shields.io/pypi/pyversions/autobasedoc.svg)
![License](https://img.shields.io/github/license/NuCOS/autobasedoc.svg)
![Test Coverage](./coverage.svg)

## Installation

```bash
pip install autobasedoc
```

Development setup:

```bash
git clone https://github.com/NuCOS/autobasedoc.git
cd autobasedoc
pip install -e .
pip install -e ".[test]"
```

Requirements:
- Python 3.7+
- ReportLab
- Matplotlib
- `svglib`, `pdfrw`, `img2pdf`

## Quick Start

```python
import os
from autobasedoc import autorpt as ar

outname = os.path.join(os.getcwd(), "MinimalExample.pdf")

doc = ar.AutoDocTemplate(
    outname,
    onFirstPage=ar.onFirstPage,
    onLaterPages=ar.onLaterPages,
    onLaterSPages=ar.onLaterSPages,
    leftMargin=0.5 * ar.cm,
    rightMargin=0.5 * ar.cm,
    topMargin=0.5 * ar.cm,
    bottomMargin=0.5 * ar.cm,
)

styles = ar.Styles()
styles.registerStyles()

content = []
content.append(ar.Paragraph("Minimal Example Title", styles.title))
content.append(ar.PageBreak())
content.append(ar.Paragraph("Table Of Contents", styles.h1))
content.append(ar.doTableOfContents())

doc.multiBuild(content)
```

## Matplotlib Integration

Use `autoPdfImg` when a plotting function should return a single ReportLab flowable:

```python
from autobasedoc import autoplot as ap

@ap.autoPdfImg
def create_chart(canvaswidth=5):
    fig, ax = ap.plt.subplots(figsize=(canvaswidth, canvaswidth))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    ax.set_title("Sample Chart")
    return fig

content.append(create_chart())
```

Use `autoPdfImage` when the plot and legend should be placed independently in the document:

```python
@ap.autoPdfImage
def create_chart_with_legend(canvaswidth=5):
    fig, ax = ap.plt.subplots(figsize=(canvaswidth, canvaswidth))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3], label="series")
    handles, labels = ax.get_legend_handles_labels()
    legend_fig = ap.plt.figure(figsize=(canvaswidth, 0.4))
    legend = legend_fig.legend(handles, labels, loc="center", frameon=False)
    return fig, legend_fig, legend

plot_img, legend_img = create_chart_with_legend()
content.extend([legend_img, plot_img])
```

## Table Layouts

For plain ReportLab tables, the standard `ar.Table` works well. For AutoBaseDoc-specific layout helpers, use `StyledTable` and finish with `layoutStyledTable()`:

```python
from autobasedoc.styledtable import StyledTable

styled = StyledTable(gridded=True)
styled.setTableData([
    ["Product", "Q1", "Q2"],
    ["Widget A", "100", "120"],
    ["Widget B", "80", "95"],
])
styled.addTableStyleCommand(("ALIGN", (0, 0), (-1, -1), "CENTER"))

table = styled.layoutStyledTable(colWidths=[4, 3, 3], rowHeights=[1.0, 0.8, 0.8])
content.append(table)
```

## Examples and Documentation

- Example script: `tests/example.py`
- Larger document example: `tests/example_document.py`
- Sphinx docs source: `sphinx_doc/`
- API docs: Read the generated Sphinx reference or inspect module docstrings

## Testing

Install test dependencies and run the suite:

```bash
pip install -e ".[test]"
MPLBACKEND=Agg pytest -q
```

Coverage run:

```bash
MPLBACKEND=Agg pytest --cov=autobasedoc --cov-report=term-missing
```

## Release Notes

Version `1.1.11` includes the current packaging cleanup, documentation fixes, and `rowHeights` forwarding support for styled table layout helpers.

## License

This project is licensed under the BSD-3-Clause License. See [LICENSE.md](LICENSE.md).

## Links

- Homepage: https://github.com/NuCOS/autobasedoc
- Package: https://pypi.org/project/autobasedoc/
- Documentation: http://autobasedoc.readthedocs.io/
- Issues: https://github.com/NuCOS/autobasedoc/issues
