locals {
  config_vars = {
    head_subnet    = module.hpc-vpc.public_subnets[0] # eu-central-1a
    compute_subnet = module.hpc-vpc.private_subnets[0]
    region         = var.cluster_region
  }
}