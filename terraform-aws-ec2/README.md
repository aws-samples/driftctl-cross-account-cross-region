# terraform-aws-ec2
This module creates a t2.micro Amazon Elastic Compute Cloud (Amazon EC2) instance in default Amazon Virtual Private Cloud (Amazon VPC), using Amazon Linux AMI.

<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_instance.instance](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance) | resource |
| [aws_ami.amazon_linux_ami](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ami) | data source |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |
| [aws_subnets.default_vpc_subnets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/subnets) | data source |
| [aws_vpc.default_vpc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/vpc) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_name"></a> [name](#input\_name) | Name for AWS EC2 instance. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_instance_id"></a> [instance\_id](#output\_instance\_id) | Amazon EC2 Instance id. |
| <a name="output_resource_account_id"></a> [resource\_account\_id](#output\_resource\_account\_id) | AWS Account id for Amazon EC2 instance. |
| <a name="output_resource_region"></a> [resource\_region](#output\_resource\_region) | AWS Region name for Amazon EC2 instance. |
| <a name="output_vpc_id"></a> [vpc\_id](#output\_vpc\_id) | Default Amazon VPC Id. |
<!-- END_TF_DOCS -->


####Disclaimer
This module should not be used for deploying resource in production environment, as this module was created for demo purpose only.
