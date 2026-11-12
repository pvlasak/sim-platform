provider "aws" {
    region = var.region
    default_tags {
        tags = {
            component = "hpc"
            managedBy = "terraform"
        }
    }
}

provider "aws-parallelcluster" {
  region = var.region
  api_stack_name = var.api_stack_name
  use_user_role = true
}