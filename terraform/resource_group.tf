resource "azurerm_resource_group" "sentinelshare" {
  name     = var.azure_resource_group
  location = var.azure_location
}
