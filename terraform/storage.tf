resource "azurerm_storage_account" "sentinelsharestorage" {
  name                     = var.azure_storage_account
  resource_group_name      = azurerm_resource_group.sentinelshare.name
  location                 = azurerm_resource_group.sentinelshare.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

}

resource "azurerm_storage_container" "files" {
  name                  = var.azure_container_name
  storage_account_name  = azurerm_storage_account.sentinelsharestorage.name
  container_access_type = "private"
}
