data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_vpc" "default_vpc" {
  default = true
}

data "aws_subnets" "default_vpc_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default_vpc.id]
  }
}

data "aws_ami" "amazon_linux_ami" {
  owners      = ["amazon"]
  name_regex  = "amzn2-ami-*"
  most_recent = true
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  filter {
    name   = "block-device-mapping.volume-type"
    values = ["gp2"]
  }
  filter {
    name   = "image-type"
    values = ["machine"]
  }
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

resource "aws_instance" "instance" {
  ami           = data.aws_ami.amazon_linux_ami.id
  instance_type = "t2.micro"
  subnet_id     = data.aws_subnets.default_vpc_subnets.ids[0]
  metadata_options {
    http_endpoint = "disabled"
    http_tokens   = "required"
  }
  root_block_device {
    encrypted = true
  }
  associate_public_ip_address = false
  tags = {
    Name = var.name
  }
}
