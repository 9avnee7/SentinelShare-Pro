output "aws_s3_bucket_name" {
  value = aws_s3_bucket.sentinelsharesbucket.id
}

output "lambda_function_name" {
  value = aws_lambda_function.clamav_yara_scanner.function_name
}

output "azure_storage_account" {
  value = azurerm_storage_account.sentinelsharestorage.name
}

output "azure_blob_container" {
  value = azurerm_storage_container.files.name
}
