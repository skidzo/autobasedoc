.. _installation:

Installation
============

PyPI
----

Install the published package with pip:

.. code-block:: bash

   pip install autobasedoc

Development Setup
-----------------

For local development from a checkout:

.. code-block:: bash

   git clone https://github.com/NuCOS/autobasedoc.git
   cd autobasedoc
   pip install -e .

Test Dependencies
-----------------

Install the optional test dependencies before running the full suite:

.. code-block:: bash

   pip install -e ".[test]"

Python Compatibility
--------------------

AutoBaseDoc currently requires Python 3.7 or newer.

Headless Test Runs
------------------

When running tests without a graphical desktop, set the Matplotlib backend
explicitly:

.. code-block:: bash

   MPLBACKEND=Agg pytest -q

Platforms
---------

The package is intended to be platform independent and is used primarily from
standard Python environments on Linux, macOS, and Windows.
