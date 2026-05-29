#!/usr/bin/env python3
"""Check the state of rtk-rewrite plugin and Hermes gateway plugins."""

from hermes_cli.plugins import discover_plugins, get_plugin_manager
discover_plugins()
pm = get_plugin_manager()

print("=== PLUGINS REGISTRADOS ===")
for p in pm.list_plugins():
    print(f"  {p['name']:30s} enabled={p['enabled']} source={p['source']}")

# Check if rtk-rewrite exists at all
print("\n=== RTK EN PLUGINS ===")
found = any(p['name'] == 'rtk-rewrite' for p in pm.list_plugins())
print(f"rtk-rewrite registrado como plugin: {found}")

# Check how plugins are discovered
print("\n=== DISCOVERY PATHS ===")
print(pm.discovery_paths if hasattr(pm, 'discovery_paths') else 'N/A')

# Look for rtk in pip
print("\n=== PIP PACKAGES ===")
import pkg_resources
for pkg in pkg_resources.working_set:
    if 'rtk' in pkg.key.lower():
        print(f"  {pkg.key}=={pkg.version}")
