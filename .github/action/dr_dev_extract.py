import sys
sys.path.append('./')
import requests
import json
import os
from DecisionRules.alias import alias_lst

# Establish environment variables and api call headers (stored as repository secrets)
api_key = os.environ['MANAGEMENT_API_KEY']
header = {'Authorization': 'Bearer '+ api_key}

# Remove JSON files from repository that should no longer be included in the release
current_json = (os.listdir('DecisionRules/rule')) + (os.listdir('DecisionRules/flow'))
alias_json = ['{}.json'.format(alias) for alias in alias_lst]
alias_json.append('placeholder.txt')
to_be_removed_lst = list(set(current_json ) - set(alias_json))

for file in to_be_removed_lst:
    try:
      os.remove('./DecisionRules/rule/'+file)
    except:
        pass
    try:
      os.remove('./DecisionRules/flow/'+file)
    except:
       pass

# Execute a GET request extract all existing rules and rule flows from the development space. 
space_request = requests.get('https://us.api.decisionrules.io/api/space/items', headers = header)
if space_request.status_code == 200:
    print('All rule and rule flow data has been extracted from the development space successfully.')
    
    # Simplify space contents to only include rules and rule flows referenced in the alias list, defined in the alias.py file.
    space_contents = json.loads(space_request.text)
    rules = [rule for rule in space_contents if rule['ruleAlias'] in alias_lst and rule['type'] in ['decision-table', 'decision-tree']]
    flows = [rule for rule in space_contents if rule['ruleAlias'] in alias_lst and rule['type'] == 'composition']

    # Loop through each individual rule aliases
    for rule in rules: 
      rule_alias = rule['ruleAlias']
      # Execute a GET request to check if the rule exists in the development space
      check = requests.get('https://us.api.decisionrules.io/api/rule/'+rule_alias, headers = header)

      # If the rule exists in the development space, convert the check response to json, define the custom file name, and add it to the repo
      if check.status_code == 200:
        print('The Rule ('+rule_alias+') exists in the development space, executing an extraction.')
        rule_json = json.loads(check.text)
        filepath = './DecisionRules/rule/'+rule_alias+'.json'
        with open(filepath, 'w') as file:
          json.dump(rule_json, file)
        print('The Rule ('+rule_alias+') has been esuccessfully added to the GitHub repository here: '+filepath+'.')

      # Otherwise, if the rule does not exist, or was not found in the development space, raise an error.
      else:
        raise Exception('The Rule ('+rule_alias+') does not exist in the development space. Error:', check.text)
    
    # Loop through each individual rule flow alias
    for flow in flows: 
      flow_alias = flow['ruleAlias']

      # Execute a GET request to check if the rule flow exists in the development space
      check = requests.get('https://us.api.decisionrules.io/api/rule-flow/export/'+flow_alias, headers = header)

      # If the rule flow exists in the development space, convert the check response to json, define the custom file name, and add it to the repo
      if check.status_code == 200:
        print('The Rule Flow ('+flow_alias+') exists in the development space, executing an extraction.')
        flow_json = json.loads(check.text)
        filepath = './DecisionRules/flow/'+flow_alias+'.json'
        with open(filepath, 'w') as file:
          json.dump(flow_json, file)
        print('The Rule Flow ('+flow_alias+') has been successfully added to the GitHub repository here: '+filepath+'.')

      # Otherwise, if the rule flow does not exist, or was not found in the development space, raise an error.
      else:
        raise Exception('The Rule Flow ('+flow_alias+') does not exist in the development space. Error: ', check.text)

else: 
   raise Exception('All rule and rule flow data were not extracted from the development space successfully. Error: ', space_request.text)
