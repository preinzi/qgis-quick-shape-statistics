# coding=utf-8
"""DockWidget test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'stephan@libergis.at'
__date__ = '2026-08-12'
__copyright__ = 'Copyright 2026, preinzi (LiberGIS)'

import unittest

from qgis.PyQt.QtWidgets import QDockWidget

from quick_shape_statistics_dockwidget import QuickShapeStatisticsDockWidget

from utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class QuickShapeStatisticsDockWidgetTest(unittest.TestCase):
    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        self.dockwidget = QuickShapeStatisticsDockWidget(None)

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_ok(self):
        """Test the dockwidget is a QDockWidget and exposes its closing signal."""
        self.assertIsInstance(self.dockwidget, QDockWidget)
        self.assertTrue(hasattr(self.dockwidget, 'closingPlugin'))

if __name__ == "__main__":
    suite = unittest.makeSuite(QuickShapeStatisticsDockWidgetTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

