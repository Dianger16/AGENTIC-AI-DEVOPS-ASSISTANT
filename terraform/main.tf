# terraform/main.tf
# Provisions: VPC → EKS Cluster → Node Group (2x t3.small)
# Cost: ~$0.10/hr (cluster) + ~$0.042/hr (2x t3.small) = ~$0.14/hr
# DESTROY WHEN DONE: terraform destroy

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = { Project = "agentic-devops", ManagedBy = "Terraform" }
  }
}

# ── Variables ────────────────────────────────────────────────────────────────
variable "aws_region"    { default = "us-east-1" }
variable "cluster_name"  { default = "agentic-devops" }
variable "instance_type" { default = "t3.small" }   # 2GB RAM, cheap
variable "node_count"    { default = 2 }

# ── VPC (using AWS VPC module for simplicity) ─────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway   = true    # required for private subnets
  single_nat_gateway   = true    # one NAT = cheaper (~$33/mo vs $66)
  enable_dns_hostnames = true

  public_subnet_tags  = { "kubernetes.io/role/elb" = "1" }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = "1" }
}

# ── EKS Cluster ───────────────────────────────────────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.31"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true   # access from your machine

  # Node group
  eks_managed_node_groups = {
    main = {
      instance_types = [var.instance_type]
      min_size       = 1
      max_size       = 3
      desired_size   = var.node_count
    }
  }
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "cluster_name"     { value = module.eks.cluster_name }
output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "configure_kubectl" {
  value = "aws eks update-kubeconfig --region ${var.aws_region} --name ${var.cluster_name}"
}
output "cost_warning" {
  value = "EKS costs ~$0.14/hr (~$3.36/day). Run terraform destroy when done!"
}
