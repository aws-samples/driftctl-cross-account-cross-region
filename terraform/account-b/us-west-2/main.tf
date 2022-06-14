provider "aws" {
  profile = "driftctl-acc-b-usw2"
  region  = "us-west-2"
}

module "ec2" {
  source = "git::https://github.com/aws-samples/driftctl-cross-account-cross-region//terraform-aws-ec2?ref=terraform-module"
  name   = "driftctl-acc-b-usw2"
}
