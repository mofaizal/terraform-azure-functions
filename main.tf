
terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0, < 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.0, < 4.0.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# This ensures we have unique CAF compliant names for our resources.
module "naming" {
  source  = "Azure/naming/azurerm"
  version = "0.3.0"
  suffix  = ["afun"]
}


resource "azurerm_resource_group" "example" {
  name     = "${module.naming.resource_group.name}"
  location = "southeastasia"
}

resource "azurerm_storage_account" "example" {
  name                     = "${module.naming.storage_account.name_unique}"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "example" {
  name                = "${module.naming.app_service_plan.name_unique}"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name

  os_type             = "Linux"
  sku_name            = "S1"
}

resource "azurerm_linux_function_app" "example" {
  name                = "${module.naming.function_app.name_unique}"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  service_plan_id     = azurerm_service_plan.example.id

  storage_account_name       = azurerm_storage_account.example.name
  storage_account_access_key = azurerm_storage_account.example.primary_access_key

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.9"
    }
  }
}

resource "azurerm_function_app_function" "example" {
  name            = "${module.naming.function_app.name_unique}-function"
  function_app_id = azurerm_linux_function_app.example.id
   language        = "Python"

  file {
    name    = "__init__.py"
    content = file("__init__.py")
  }

  test_data = jsonencode({
    "name" = "Azure"
  })

  config_json = jsonencode({
    "bindings" = [
      {
        "authLevel" = "function"
        "direction" = "in"
        "methods" = [
          "get",
          "post",
        ]
        "name" = "req"
        "type" = "httpTrigger"
      },
      {
        "direction" = "out"
        "name"      = "$return"
        "type"      = "http"
      },
    ]
  })
}

# resource "azurerm_user_assigned_identity" "appag_umid" {
#   name                = module.naming.user_assigned_identity.name_unique
#   resource_group_name = azurerm_resource_group.example.name
#   location            = azurerm_resource_group.example.location

# }


resource "azurerm_function_app_function" "vmss" {
  name            = "${module.naming.function_app.name_unique}-vmss"
  function_app_id = azurerm_linux_function_app.example.id
   language        = "Python"

  file {
    name    = "vmss.py"
    content = file("vmss.py")
  }

  test_data = jsonencode({
    "name" = "Azure"
  })

  config_json = jsonencode({
    "bindings" = [
      {
        "authLevel" = "function"
        "direction" = "in"
        "methods" = [
          "get",
          "post",
        ]
        "name" = "req"
        "type" = "httpTrigger"
      },
      {
        "direction" = "out"
        "name"      = "$return"
        "type"      = "http"
      },
    ]
  })
}
