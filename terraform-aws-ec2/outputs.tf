output "instance_id" {
  value       = aws_instance.instance.id
  description = "Amazon EC2 Instance id."
}

output "vpc_id" {
  value       = data.aws_vpc.default_vpc.id
  description = "Default Amazon VPC Id."
}

output "resource_region" {
  value       = data.aws_region.current.name
  description = "AWS Region name for Amazon EC2 instance."
}

output "resource_account_id" {
  value       = data.aws_caller_identity.current.account_id
  description = "AWS Account id for Amazon EC2 instance."
}
