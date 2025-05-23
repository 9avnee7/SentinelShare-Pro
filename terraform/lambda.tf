resource "aws_lambda_function" "clamav_yara_scanner" {
  function_name = var.lambda_function_name
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_role.arn

  filename         = "lambda_function_payload.zip"
  source_code_hash = filebase64sha256("lambda_function_payload.zip")


  layers = [
    "arn:aws:lambda:ap-south-1:146646728425:layer:yara-4:1",
    "arn:aws:lambda:ap-south-1:146646728425:layer:customYaraLayer-2:8"
  ]

  environment {
    variables = {
      S3_BUCKET = var.aws_s3_bucket_name
    }
  }
}
