Tutorials
=========

Tutorial 1: First Document
--------------------------

Start with the minimal document example from :doc:`Basic_Usage` and build a PDF
with a title page and table of contents.

Tutorial 2: Multi-column Layouts
--------------------------------

``AutoDocTemplate`` can create multi-column page templates by passing a page
callback together with a frame count:

.. code-block:: python

   from autobasedoc import autorpt as ar

   doc = ar.AutoDocTemplate(
       "multi_column.pdf",
       onFirstPage=(ar.drawFirstLandscape, 1),
       onLaterPages=(ar.drawLaterLandscape, 2),
       pagesize=ar.landscape(ar.A4),
   )

Tutorial 3: Headers and Footers
-------------------------------

Page metadata is attached with ``addPageInfo``:

.. code-block:: python

   doc.addPageInfo(typ="header", pos="l", text="My Company")
   doc.addPageInfo(typ="header", pos="r", text="Quarterly Report")
   doc.addPageInfo(typ="footer", pos="c", text="Page ", addPageNumber=True)

Tutorial 4: Plot Flowables
--------------------------

For plot examples, use the tested snippets from ``tests/example.py``:

.. literalinclude:: ../tests/example.py
   :language: python
   :start-after: ## Example 2 adding matplotlib plot
   :end-before: ## Example 3 adding matplotlib plot and legend
   :caption: Single-image plot flowable
