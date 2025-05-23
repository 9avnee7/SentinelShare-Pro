variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "aws_s3_bucket_name" {
  description = "S3 bucket name"
  default     = "sentinelsharesbucket"
}

variable "lambda_function_name" {
  description = "Lambda function name"
  default     = "ClamavYaraScanner"
}

variable "azure_location" {
  description = "Azure region"
  default     = "East US"
}

variable "azure_resource_group" {
  description = "Azure Resource Group"
  default     = "sentinelshare-rg"
}

variable "azure_storage_account" {
  description = "Azure Storage Account name"
  default     = "sentinelsharestorage"
}

variable "azure_container_name" {
  description = "Azure Blob Container name"
  default     = "files"
}
