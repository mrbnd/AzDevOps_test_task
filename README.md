  
# AzDevOps_test_task
## Task:
Assign a user or a group Administrator rights to variable groups that contain a specific string (mask).
This repo contains 2 versions of the solution:
1. add_permisson.py (should work on any machine with python3.8)
2. add_permission_az_devOps.py and azure-pipelines.yml (should work on Azure pipeline)

## Common prerequisites:
Generate Personal Access Token (PAT) [`link`](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows)
Solution was tested with (Scopes: Full access)
## First solution - add_permisson.py:
1. Add project your parameters to add_permisson.py
```python
PERSONAL_ACCESS_TOKEN = ''
PROJECT_NAME = ''
ORGANIZATION_NAME = ''
```
2. Usage syntax
```bash
python3 add_permission.py -f -n
```
3. Example (this script adds test@gmail.com permission to variable groups contains "test" in name). Case-insensitive.
```bash
python3 add_permission.py -f test -n test@gmail.com
```
## Second solution - add_permission_az_devOps.py:
This solution is a little bit adapted for the Azure DevOps pipeline.
### Prerequisites:
1. Create variable group AZURE_DEVOPS_TOKENS in your project. [`link`](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups?view=azure-devops&tabs=classic#create-a-variable-group)
2. Create AZURE_DEVOPS_EXT_PAT variable with PAT value in AZURE_DEVOPS_TOKENS group.
3. Customize azure-pipelines.yml for your project. All necessary lines have comments.
4. Use variable_group_filter and user_or_group_name in azure-pipelines.yml as input parameters for add_permission_az_devOps.py script.
5. Create Azure DevOps pipeline [`link`](https://learn.microsoft.com/en-us/azure/devops/pipelines/create-first-pipeline?view=azure-devops&tabs=java%2Ctfs-2018-2%2Cbrowser)