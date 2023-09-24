import sys, getopt
import base64
import requests

# Add project parameters
PERSONAL_ACCESS_TOKEN = ''
PROJECT_NAME = ''
ORGANIZATION_NAME = ''
BASE_URL = 'https://dev.azure.com'

#Encode PAT to base64
PERSONAL_ACCESS_TOKEN_BASE64 = base64.b64encode(f":{PERSONAL_ACCESS_TOKEN}".encode()).decode()


# Handle input variables
variable_group_filter = ''
user_or_group_name = ''

def set_up_parameters(argv):
    global variable_group_filter
    global user_or_group_name
    opts, args = getopt.getopt(argv,"hf:n:",["filter=","user_or_group_name="])
    for opt, arg in opts:
        if opt == '-h':
            print ('python3 add_permission.py -f <filter> -n <user_or_group_name>')
            sys.exit()
        elif opt in ("-f", "--filter"):
            variable_group_filter = arg
        elif opt in ("-n", "--user_or_group_name"):
            user_or_group_name = arg
    if variable_group_filter == '' or user_or_group_name == '':
        print("Necessary values haven't been provided. Please check \"python3 add_permission.py -h\"")
        sys.exit(1)

# Get projectId by PROJECT_NAME function
# https://learn.microsoft.com/en-us/rest/api/azure/devops/core/projects/list?view=azure-devops-rest-7.0&tabs=HTTP
def get_project_id():
    url = f"{BASE_URL}/{ORGANIZATION_NAME}/_apis/projects?api-version=7.0"
    headers = {"Authorization": f"Basic {PERSONAL_ACCESS_TOKEN_BASE64}"}
    response = requests.get(url, headers=headers)

    projects_list = response.json()
    project_id = ''

    for project in projects_list["value"]:
        if project["name"] == PROJECT_NAME:
            project_id = project["id"]
            break
    
    if project_id == '':
        print(f"Project {PROJECT_NAME} in {ORGANIZATION_NAME} not found")
        sys.exit(1)
    return project_id

# Get userId or groupId
# https://learn.microsoft.com/en-us/rest/api/azure/devops/memberentitlementmanagement/user-entitlements/get-user-entitlements?view=azure-devops-rest-5.1#userentitlement
# https://learn.microsoft.com/en-us/rest/api/azure/devops/graph/groups/list?view=azure-devops-rest-7.0&tabs=HTTP
def get_user_or_group_id(user_or_group_name):
    url_users  = f"https://vsaex.dev.azure.com/{ORGANIZATION_NAME}/_apis/userentitlements?api-version=5.1-preview.2"
    url_groups = f"https://vssps.dev.azure.com/{ORGANIZATION_NAME}/_apis/graph/groups?api-version=7.0-preview.1"
    headers    = {"Authorization": f"Basic {PERSONAL_ACCESS_TOKEN_BASE64}"}
    

    result_id = ''

    if '@' in user_or_group_name:
        response = requests.get(url_users, headers=headers)
        users_list = response.json()

        for user in users_list["members"]:
            if user["user"]["principalName"] == user_or_group_name:
                result_id = user["id"]
                break
    else:
        response = requests.get(url_groups, headers=headers)
        groups_list = response.json()

        for group in groups_list["value"]:
            if group["displayName"] == user_or_group_name:
                result_id = group["originId"]
                break

    if result_id == '':
        print(f"User or group {user_or_group_name} not found in organization {ORGANIZATION_NAME}")
        sys.exit(1)
    return result_id

# Assign permission to user or group
# https://learn.microsoft.com/en-us/rest/api/azure/devops/securityroles/roleassignments/set-role-assignments?view=azure-devops-rest-7.0&tabs=HTTP
def assign_permissions(user_or_group_id, project_id, variable_group_id):
    url = f"{BASE_URL}/{ORGANIZATION_NAME}/_apis/securityroles/scopes/distributedtask.variablegroup/roleassignments/resources/{project_id}${variable_group_id}?api-version=7.0-preview.1"
    headers = {"Authorization": f"Basic {PERSONAL_ACCESS_TOKEN_BASE64}"}
    data = [
        {
            "userId": user_or_group_id,
            "roleName": "Administrator"
        }
    ]
    response = requests.put(url, headers=headers, json=data)
    return response.status_code


# Get list of variable groups
#https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/variablegroups/get-variable-groups?view=azure-devops-rest-7.0&tabs=HTTP
def get_variable_groups():
    url = f"{BASE_URL}/{ORGANIZATION_NAME}/{PROJECT_NAME}/_apis/distributedtask/variablegroups?api-version=7.0"
    headers = {"Authorization": f"Basic {PERSONAL_ACCESS_TOKEN_BASE64}"}
    response = requests.get(url, headers=headers)
    return response.json()


# Main logic
set_up_parameters(sys.argv[1:])
project_id = get_project_id()
user_or_group_id = get_user_or_group_id(user_or_group_name)
variable_groups_list = get_variable_groups()


for group in variable_groups_list["value"]:
    if variable_group_filter.lower() in group["name"].lower():
        variable_group_id = group["id"]
        status_code = assign_permissions(user_or_group_id=user_or_group_id, project_id=project_id, variable_group_id=variable_group_id)
        if status_code >= 400:
            print(f"Assignment permissions for variable group {group['name']} FAILED (Status code: {status_code})")
        else:
            print(f"Administrator permissions to {user_or_group_name} for variable group {group['name']} has been assigned successfully")