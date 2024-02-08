# Import the needed credential and management objects from the libraries.
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import OrchestrationMode
import os

print(f"Provisioning a virtual machine scale set...some operations might take a minute or two.")

# Acquire a credential object using CLI-based authentication.
credential = AzureCliCredential()

# Retrieve subscription ID from environment variable.
subscription_id = "XXXX"


# Step 1: Provision a resource group

# Obtain the management object for resources, using the credentials from the CLI login.
resource_client = ResourceManagementClient(credential, subscription_id)

# Constants we need in multiple places: the resource group name and the region
# in which we provision resources. You can change these values however you want.
RESOURCE_GROUP_NAME = "PythonAzureExample7"
LOCATION = "westus2"

# Provision the resource group.
rg_result = resource_client.resource_groups.create_or_update(RESOURCE_GROUP_NAME,
    {
        "location": LOCATION
    }
)

print(f"Provisioned resource group {rg_result.name} in the {rg_result.location} region")

# For details on the previous code, see Example: Provision a resource group
# at https://docs.microsoft.com/azure/developer/python/azure-sdk-example-resource-group


# Step 2: provision a virtual network

# A virtual machine requires a network interface client (NIC). A NIC requires
# a virtual network and subnet along with an IP address. Therefore we must provision
# these downstream components first, then provision the NIC, after which we
# can provision the VM.

# Network and IP address names
VNET_NAME = "python-example-vnet"
SUBNET_NAME = "python-example-subnet"
IP_NAME = "python-example-ip"
IP_CONFIG_NAME = "python-example-ip-config"
NIC_NAME = "python-example-nic"

# Obtain the management object for networks
network_client = NetworkManagementClient(credential, subscription_id)

# Provision the virtual network and wait for completion
poller = network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP_NAME,
    VNET_NAME,
    {
        "location": LOCATION,
        "address_space": {
            "address_prefixes": ["10.0.0.0/16"]
        }
    }
)

vnet_result = poller.result()

print(f"Provisioned virtual network {vnet_result.name} with address prefixes {vnet_result.address_space.address_prefixes}")

# Step 3: Provision the subnet and wait for completion
poller = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, 
    VNET_NAME, SUBNET_NAME,
    { "address_prefix": "10.0.0.0/18" }
)
subnet_result = poller.result()

print(f"Provisioned virtual subnet {subnet_result.name} with address prefix {subnet_result.address_prefix}")

# Obtain the management object for virtual machines
compute_client = ComputeManagementClient(credential, subscription_id)
VMSS_NAME = "myVmss"
VMSS_INSTANCE_COUNT = 2

print(f"Start VMSS Provisioning {VMSS_NAME}, instance count {VMSS_INSTANCE_COUNT}")

poller = compute_client.virtual_machine_scale_sets.begin_create_or_update(RESOURCE_GROUP_NAME,
    VMSS_NAME,
    {
        'location': LOCATION,
        'single_placement_group': False,
        'platform_fault_domain_count': 1,
        'orchestration_mode': 'Flexible',
        'sku': {
            'name': 'Standard_d2s_v3',
            'capacity': VMSS_INSTANCE_COUNT
            },
        'virtual_machine_profile': {   
            'priority': 'Spot',
            'os_profile': {
                'computer_name_prefix': 'myVM',
                'admin_username': 'AzureUser',
                'admin_password': 'This!$@T3rr!bleP@ssw0rd'
            },
            'storage_profile': {
                'image_reference': {
                "publisher": 'Canonical',
                "offer": "0001-com-ubuntu-server-focal",
                "sku": "20_04-lts-gen2",
                "version": "latest"
                },
                "os_disk": {
                    "os_type": "Linux",
                    "create_option": "FromImage",
                    "caching": "ReadWrite",
                    "managed_disk": {
                        "storage_account_type": "Premium_LRS"
                    },
                    "disk_size_gb": 30
                }
            },
            'network_profile': {
                'network_api_version': '2020-11-01',
                'network_interface_configurations': [
                    {
                        'name':'mynic',
                        'primary': True,
                        'ip_configurations': [
                            {
                                'name':'myipconfig',
                                'subnet': {
                                    'id': subnet_result.id
                                },
                                'primary': True,
                                'public_ip_address_configuration': {
                                    'name': 'myPIP',
                                    'sku': {
                                        'name': 'Standard'
                                    },
                                    'idle_timeout_in_minutes': 15,
                                    'public_ip_address_version': 'IPv4'
                                    
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }
)

# Wait for the operation to complete. You could, of course, omit this and poll from another process
vmss_result = poller.result()

print (vmss_result)

vmList = [vm for vm in compute_client.virtual_machines.list_all (
    filter=f"'virtualMachineScaleSet/id' eq '{vmss_result.id}'", expand="instanceview"
)]

for vm in vmList:
    print (vm.name)
    for status in vm.instance_view.statuses:
        print (status.display_status, status.code)