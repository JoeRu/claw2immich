#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Parse the XML files
features_file = "ai-docs/overview-features-bugs.xml"
tree = ET.parse(features_file)
root = tree.getroot()

# Items to archive (all DONE items)
items_to_archive = [17, 18, 22, 23, 24, 25, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42]

# Find and move items
items_section = root.find("items")
archive_section = root.find("archive")

if items_section is not None and archive_section is not None:
    # Find all items with matching IDs
    items_to_move = []
    for item in list(items_section.findall("item")):
        item_id_str = item.get("id")
        if item_id_str:
            try:
                item_id = int(item_id_str)
                if item_id in items_to_archive:
                    items_to_move.append((item_id, item))
            except ValueError:
                pass
    
    # Move items to archive
    for item_id, item in sorted(items_to_move, key=lambda x: x[0]):
        item.set("archived", "2026-02-17")
        items_section.remove(item)
        archive_section.append(item)
    
    print(f"Moved {len(items_to_move)} items to archive: {sorted([x[0] for x in items_to_move])}")
else:
    print("Error: Could not find items or archive section")

# Update metadata
metadata = root.find("metadata")
if metadata is not None:
    updated = metadata.find("updated")
    if updated is not None:
        updated.text = "2026-02-17"
        print("Updated metadata.updated to 2026-02-17")

# Write back with proper formatting
ET.indent(root, space="  ")  # Python 3.9+
tree.write(features_file, encoding="UTF-8", xml_declaration=True)
print(f"Saved {features_file}")
