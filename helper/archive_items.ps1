$xmlPath = "ai-docs/overview-features-bugs.xml"
[xml]$xml = Get-Content $xmlPath

# Items to archive
$itemsToArchive = @(17, 18, 22, 23, 24, 25, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42)

# Get the items and archive sections
$items = $xml.Documentelement.items
$archive = $xml.DocumentElement.archive

# Find and move items
$moved = 0
foreach ($id in $itemsToArchive) {
    $item = $items.SelectSingleNode("item[@id='$id']")
    if ($item) {
        # Add archived attribute
        $item.SetAttribute("archived", "2026-02-17")
        # Move to archive
        $items.RemoveChild($item) | Out-Null
        $archive.AppendChild($item) | Out-Null
        $moved++
    }
}

# Update metadata
$metadata = $xml.DocumentElement.metadata
$updated = $metadata.SelectSingleNode("updated")
if ($updated) {
    $updated.InnerText = "2026-02-17"
}

# Save
$xml.Save($xmlPath)
Write-Host "Moved $moved items to archive"
Write-Host "Updated $xmlPath"
