terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# --- S3: bucket privado y cifrado para logs de moderacion ---
resource "aws_s3_bucket" "avance2_bucket" {
  bucket = "avance2-hti-gescamilla"
}

resource "aws_s3_bucket_public_access_block" "avance2_bucket_block" {
  bucket = aws_s3_bucket.avance2_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "avance2_bucket_encryption" {
  bucket = aws_s3_bucket.avance2_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- RDS: PostgreSQL sin acceso publico, cifrado ---
resource "aws_db_instance" "avance2_db" {
  identifier             = "avance2-hti-db"
  engine                 = "postgres"
  engine_version         = "17"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  storage_type           = "gp2"
  db_name                = "postgres"
  username               = "postgres"
  password               = var.db_password
  publicly_accessible    = false
  storage_encrypted      = true
  skip_final_snapshot    = true
}

variable "db_password" {
  description = "Password maestro de la base de datos RDS"
  type        = string
  sensitive   = true
}
