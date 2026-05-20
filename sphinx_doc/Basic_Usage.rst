.. _basic_usage:

Basic Usage
===========

AutoBaseDoc primarily exposes two modules:

- ``autobasedoc.autorpt`` for document construction on top of ReportLab
- ``autobasedoc.autoplot`` for turning Matplotlib figures into PDF flowables

Minimal Document
----------------

.. code-block:: python

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

Keeping Fonts in Sync
---------------------

If you want matching fonts in ReportLab and Matplotlib output, configure the
bundled Calibri fonts once and reuse the resulting Matplotlib font properties:

.. literalinclude:: ../tests/example.py
   :language: python
   :start-after: ## Example prerequisites
   :end-before: styles = ar.Styles()

Plot Flowables
--------------

Use ``@ap.autoPdfImg`` for a single image flowable and ``@ap.autoPdfImage`` for
separate legend and plot flowables. The examples in ``tests/example.py`` show
both patterns.
