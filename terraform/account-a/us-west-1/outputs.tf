output "instance_id" {
  value = module.ec2.instance_id
}

output "vpc_id" {
  value = module.ec2.vpc_id
}

output "resource_region" {
  value = module.ec2.resource_region
}

output "resource_account_id" {
  value = module.ec2.resource_account_id
}
