import sys
sys.path.append('./')
import requests
import json
import os
from DecisionRules.alias import alias_lst

# Establish environment variables and api call headers
api_key = os.environ['MANAGEMENT_API_KEY']
get_header = {'Authorization': 'Bearer ' + api_key}
post_header = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+ api_key}

# Loop through each individual rule file in the rule directory
rule_directory = './DecisionRules/rule'
for rule_file in [filename for filename in os.listdir(rule_directory) if filename.endswith('.json')]:
    with open(os.path.join(rule_directory, rule_file)) as rule:
        rule = json.loads(rule.read())
    rule_alias = rule['ruleAlias']

    # Execute a GET request to chheck if the rule exists in the integration, stage or production space (dynamic action)
    check = requests.get('https://us.api.decisionrules.io/api/rule/'+rule_alias, headers = get_header)
    # If the rule exists, execute a custom POST request to overwrite the existing with the updated version
    if check.status_code == 200: 
        print('The Rule ('+rule_alias+') exists in the targeted space, executing a version update.')
        rule['ruleId'] = (json.loads(check.text))['ruleId']
        rule['version'] = (json.loads(check.text))['version']
        rule = json.dumps(rule)
        rule_post = requests.post('https://us.api.decisionrules.io/api/rule/', headers = post_header, data = rule)  
        print('The Rule ('+rule_alias+') has been successfully updated.') if rule_post.status_code == 200 else print('The Rule ('+rule_alias+') update was not successful. Error: ', rule_post.text)
    
    # Otherwise, if the rule does not exist, or was not found, execute a POST request with the base url to initialize the first version
    else:
        print('The Rule ('+rule_alias+') does not exist in the targeted space, executing an upload.')
        del rule['ruleId']
        del rule['version']
        rule = json.dumps(rule)
        rule_post = requests.post('https://us.api.decisionrules.io/api/rule/', headers = post_header, data = rule)
        print('The Rule ('+rule_alias+') has been successfully uploaded.') if rule_post.status_code == 200 else print('The Rule ('+rule_alias+') upload was not successful. Error: ', rule_post.text)

# Loop through each individual flow file in the flow directory
flow_directory = './DecisionRules/flow'
for flow_file in [filename for filename in os.listdir(flow_directory) if filename.endswith('.json')]:
    with open(os.path.join(flow_directory, flow_file)) as flow:
        flow = json.loads(flow.read())
    flow_alias = flow[0]['ruleAlias']  
    flow = json.dumps(flow)
    check = requests.get('https://us.api.decisionrules.io/api/rule-flow/'+flow_alias, headers = get_header)

    # If the rule flow exists, execute a custom POST request to introduce a new version
    if check.status_code == 200:   
        print('The Rule Flow ('+flow_alias+') exists in the targeted space, executing a version update.')
        rule_flow_post = requests.post('https://us.api.decisionrules.io/api/rule-flow/import?new-version='+flow_alias, headers = post_header, data = flow)
        print('The Rule Flow ('+flow_alias+') has been successfully updated.') if rule_flow_post.status_code == 200 else print('The Rule Flow ('+flow_alias+') update was not successful. Error: ', rule_flow_post.text)

    # Otherwise, if the rule flow does not exist, or was not found, execute a POST request with the base url to initialize the first version
    else:   
        print('The Rule Flow ('+flow_alias+') does not exist in the targeted space, executing an upload.')
        rule_flow_post = requests.post('https://us.api.decisionrules.io/api/rule-flow/import', headers = post_header, data = flow)
        print('The Rule Flow ('+flow_alias+') has been successfully uploaded.') if rule_flow_post.status_code == 200 else print('The Rule Flow ('+flow_alias+') upload was not successful. Error: ', rule_flow_post.text)
