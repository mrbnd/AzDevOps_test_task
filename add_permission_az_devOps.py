import sys, getopt, os
import subprocess
import json
import base64
import requests

# Get connection parameters
PERSONAL_ACCESS_TOKEN = os.getenv('AZURE_DEVOPS_EXT_PAT')
BASE_URL = os.getenv('BASE_URL')
PROJECT_NAME = os.getenv('PROJECT_NAME')


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
            print ('python3 add_permission_azure_devOps.py -f <filter> -n <user_or_group_name>')
            sys.exit()
        elif opt in ("-f", "--filter"):
            variable_group_filter = arg
        elif opt in ("-n", "--user_or_group_name"):
            user_or_group_name = arg
    if variable_group_filter == '' or user_or_group_name == '':
        print("Necessary values haven't been provided. Please check \"python3 add_permission_azure_devOps.py -h\"")
        sys.exit(1)

#Get input variables
set_up_parameters(sys.argv[1:])

# Shell commands
get_project_id_shell_command = f"az devops project show -p {PROJECT_NAME} --org={BASE_URL} | jq -r .id"
get_user_id_shell_command = f"az devops user list | jq -r '.items[] | select(.user.mailAddress | test(\"{user_or_group_name}\"; \"i\")) | .id'"
get_security_group_id_shell_command = f"az devops security group list --scope organization  | jq -r  '.graphGroups[] | select(.displayName | ascii_downcase == \"{user_or_group_name.lower()}\") | .originId'"
get_variable_group_shell_command = f"az pipelines variable-group list | jq -r '[.[] | select(.name | test(\"{variable_group_filter}\"; \"i\"))]'"

# Run shell command
def run_shell_command(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.stderr != '':
        print(f"Command \"{cmd}\" failed:")
        print(result.stderr)
        sys.exit(1)
    return((result.stdout).strip())

# Get user or group id by name
def get_user_or_group_id():
    result_id = ''
    # Email must contain '@' whereas groups can't contain '@' in the name
    if '@' in user_or_group_name:
        result_id = run_shell_command(get_user_id_shell_command)
    else:
        result_id = run_shell_command(get_security_group_id_shell_command)

    if result_id == '':
        print(f"User or group {user_or_group_name} not found")
        sys.exit(1)
    return result_id

# Assign permission to user or group
# https://learn.microsoft.com/en-us/rest/api/azure/devops/securityroles/roleassignments/set-role-assignments?view=azure-devops-rest-7.0&tabs=HTTP
def assign_permissions(user_or_group_id, project_id, variable_group_id):
    url = f"{BASE_URL}/_apis/securityroles/scopes/distributedtask.variablegroup/roleassignments/resources/{project_id}${variable_group_id}?api-version=7.0-preview.1"
    headers = {"Authorization": f"Basic {PERSONAL_ACCESS_TOKEN_BASE64}"}
    data = [
        {
            "userId": user_or_group_id,
            "roleName": "Administrator"
        }
    ]
    response = requests.put(url, headers=headers, json=data)
    return response.status_code


#Main logic
project_id = run_shell_command(get_project_id_shell_command)
user_or_group_id = get_user_or_group_id()
variable_groups_list = json.loads(run_shell_command(get_variable_group_shell_command))

if len(variable_groups_list) == 0:
    print(f"Provided mask \"{variable_group_filter}\" doesn't match any variable group name")
    sys.exit(1)
else:
    for group in variable_groups_list:
        variable_group_id = group["id"]
        status_code = assign_permissions(user_or_group_id=user_or_group_id, project_id=project_id, variable_group_id=variable_group_id)
        if status_code >= 400:
            print(f"Assignment permissions for variable group {group['name']} FAILED (Status code: {status_code})")
        else:
            print(f"Administrator permissions to {user_or_group_name} for variable group {group['name']} has been assigned successfully")