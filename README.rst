Python Project Template
=======================

A template to quickstart work on python package development.

Getting Started
---------------

1. If you are developing on linux or mac, run ``make setup`` to set the package name and initial version. If you are developing on windows, alter every reference to python_package_template to your desired package name.
2. Modify ``setup.cfg`` so it contains the correct metadata for your python package.
3. It is recommended to develop within a virtual environment or conda environment. Set one up and activate the environment.
4. Perform an editable install of the package with development dependencies. ``pip install -e .[dev]``

Features
--------

The package version is single sourced at ``src/<package_name>/VERSION``. All other parts of the template reference this file
to discover the package version.

Makefile commands to make development easier on linux/mac systems.
The available commands range from running linting to building source distributions.

Run ``make help`` to see a list of available commands.

The following are tools made available to you under the ``dev`` extra and used by different makefile commands.

.. csv-table::

    Tool,Description,Purpose
    `black <https://github.com/psf/black>`_,code formatter,keep your code well formatted
    `pytest <https://docs.pytest.org/en/7.2.x/>`_,unit tests,write checks to run on your package code
    `ruff <https://github.com/charliermarsh/ruff>`_,linter,automated code analysis that can identify syntax or style errors


Limitations
-----------

This template is for standalone packages. It would need some slight modification in ``setup.cfg`` and to
the structure in src to work for namespace packages.
