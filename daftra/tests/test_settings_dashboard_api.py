# Copyright (c) 2026, Galaxy Labs and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase

from daftra.api import dashboard_api, settings_api


class TestSettingsDashboardAPI(FrappeTestCase):
    def test_settings_catalog_and_plugins_have_daftra_groups(self):
        settings_groups = settings_api.get_settings_catalog()
        plugin_catalog = settings_api.get_plugin_catalog()

        keys = {row["key"] for row in settings_groups}
        plugin_keys = {row["key"] for row in plugin_catalog}

        self.assertIn("sales_settings", keys)
        self.assertIn("tax_settings", keys)
        self.assertIn("system_settings", keys)
        self.assertIn("sales", plugin_keys)
        self.assertIn("accounting", plugin_keys)
        self.assertIn("settings", plugin_keys)

    def test_dashboard_blueprint_and_overview_include_reports_settings_and_readiness(self):
        blueprint = dashboard_api.get_dashboard_blueprint()
        overview = dashboard_api.get_dashboard_overview()
        section_keys = {row["key"] for row in blueprint["sections"]}

        self.assertIn("overview", section_keys)
        self.assertIn("reports", section_keys)
        self.assertIn("settings", section_keys)
        self.assertIn("plugins", section_keys)
        self.assertIn("reports", overview)
        self.assertIn("settings", overview)
        self.assertIn("plugins", overview)
        self.assertIn("readiness", overview)
        self.assertIn("booking_service_ready", overview["readiness"])
        self.assertIn("zatca_ready", overview["readiness"])
