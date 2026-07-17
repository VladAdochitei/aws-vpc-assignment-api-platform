variable "table_name" {
  type = string
}

variable "hash_key" {
  type = string
}

variable "range_key" {
  type    = string
  default = null
}

variable "attributes" {
  description = "Key attributes only (not all item fields) — DynamoDB doesn't need non-key attributes declared"
  type = list(object({
    name = string
    type = string # S = string, N = number, B = binary
  }))
}

variable "global_secondary_indexes" {
  type = list(object({
    name            = string
    hash_key        = string
    range_key       = optional(string)
    projection_type = string # ALL, KEYS_ONLY, INCLUDE
  }))
  default = []
}

variable "billing_mode" {
  type    = string
  default = "PAY_PER_REQUEST"
}