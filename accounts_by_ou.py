#  https://github.com/dannysteenman/aws-toolbox
#
#  License: MIT
#
# This script returns a list of acounts that are part of an Organizational Unit (OU)

import boto3
import sys
import pprint

pp = pprint.PrettyPrinter(indent=4)
client_ou=boto3.client('organizations')
client_ct=boto3.client('controltower')

root_org_id = 'r-****'

ou_tree = {}
ou_tree[root_org_id+'|'] = {}
ou_tree[root_org_id+'|']['accounts'] = []

account_numbers = []
all_controls = {}
controls_by_ou = {}
webservices = []


def get_accounts_in_ou(ou, accounts, next_token, root_org_id, top_child_id, second_child_id):

    if next_token != '' :
        response = client_ou.list_accounts_for_parent(ParentId=ou, NextToken=next_token)
    else:
        response = client_ou.list_accounts_for_parent(ParentId=ou)

    if len(response["Accounts"]) > 0:
        for account in response['Accounts']:
            account_numbers.append(account)

            if second_child_id != '':
                ou_tree[root_org_id+'|'][top_child_id+'|'][second_child_id+'|']['accounts'].append(account)
                #pull out a specific OUs account name:id
                if top_child_id == 'ou-***':
                    webservices.append(account['Name']+ ': '+ account['Id'])
            elif top_child_id != '':
                ou_tree[root_org_id+'|'][top_child_id+'|']['accounts'].append(account)
                if top_child_id == 'ou-***':
                    webservices.append(account['Name']+ ': '+ account['Id'])
            else:             
                ou_tree[root_org_id+'|']['accounts'].append(account)


        if 'NextToken' in response.keys():
            get_accounts_in_ou(ou, accounts, response['NextToken'], root_org_id=root_org_id, top_child_id=top_child_id, second_child_id=second_child_id)

    return

def describe_ou(ou):
    response = client_ou.describe_organizational_unit(OrganizationalUnitId=ou)
    return response["OrganizationalUnit"]

def get_ous_in_ou(ou):
    organization_children = client_ou.list_children(
        ParentId=ou,
        ChildType='ORGANIZATIONAL_UNIT',
        MaxResults=20
    )
    return organization_children

def list_enabled_controls(arn):
    controls = {}
    try:
        controls = client_ct.list_enabled_controls(
            targetIdentifier=arn
        )
    except:
        print("got exception with ou arn: "+arn )

    return controls

def list_enabled_controls(arn, next_token, root_org_id, top_child_id, second_child_id):
    controls = {}

    if next_token != '' :
        try:
            controls = client_ct.list_enabled_controls( targetIdentifier=arn,  NextToken=next_token )
        except:
            print("got exception with ou arn: "+arn )
            return
    else:
        try:
            controls = client_ct.list_enabled_controls( targetIdentifier=arn )
        except:
            print("got exception with ou arn: "+arn )
            return
        
    if len(controls) > 0:
        for control in controls['enabledControls']:
            all_controls[control['controlIdentifier']] = {}

            if second_child_id != '':
                top_ou_name = ou_tree[root_org_id+'|'][top_child_id+'|']['description']['Name']
                second_ou_name = ou_tree[root_org_id+'|'][top_child_id+'|'][second_child_id+'|']['description']['Name']
                controls_by_ou[root_org_id+'|'+top_ou_name+'|'+second_ou_name+'|'].append(control['controlIdentifier'])
                ou_tree[root_org_id+'|'][top_child_id+'|'][second_child_id+'|']['controls'].append(control['controlIdentifier'])
            elif top_child_id != '':
                top_ou_name = ou_tree[root_org_id+'|'][top_child_id+'|']['description']['Name']
                controls_by_ou[root_org_id+'|'+top_ou_name+'|'+''+'|'].append(control['controlIdentifier'])
                ou_tree[root_org_id+'|'][top_child_id+'|']['controls'].append(control['controlIdentifier'])
            else:             
                controls_by_ou[root_org_id+'|'+''+'|'+''+'|'+'root'+'|'].append(control['controlIdentifier'])
                ou_tree[root_org_id+'|']['controls'].append(control['controlIdentifier'])

    if 'NextToken' in controls.keys():
        list_enabled_controls(arn=arn, next_token=controls['NextToken'], root_org_id=root_org_id, top_child_id=top_child_id, second_child_id=second_child_id)

    return

get_accounts_in_ou(ou=root_org_id, accounts=[], next_token='', root_org_id=root_org_id, top_child_id='', second_child_id='')

ou_count = 0
top_level_ous = get_ous_in_ou(root_org_id)
#fields = 'root org id | top level org | secondary org | description | account arn | account email | account id | account name '
for top_child in top_level_ous['Children']:
    ou_count = ou_count+1
    ou_tree[root_org_id+'|'][top_child['Id']+'|'] = {}
    ou_tree[root_org_id+'|'][top_child['Id']+'|']['accounts'] = []
    ou_tree[root_org_id+'|'][top_child['Id']+'|']['controls'] = []

    ou_tree[root_org_id+'|'][top_child['Id']+'|']['description'] = describe_ou(top_child['Id'])
    top_ou_name = ou_tree[root_org_id+'|'][top_child['Id']+'|']['description']['Name']
    controls_by_ou[root_org_id+'|'+top_ou_name+'|'+''+'|'] = []

    arn=ou_tree[root_org_id+'|'][top_child['Id']+'|']['description']['Arn']
    list_enabled_controls(arn=arn, next_token='', root_org_id=root_org_id, top_child_id=top_child['Id'], second_child_id='')

    get_accounts_in_ou(ou=top_child['Id'], accounts=[], next_token='', root_org_id=root_org_id, top_child_id=top_child['Id'], second_child_id='')

    #ou_csv.append(root_org_id + '|' + top_child['Id']+ '|' + [second_child['Id']] + '|' + description_field + '|' + value )
    second_level_ous = get_ous_in_ou(top_child['Id'])
    for second_child in second_level_ous['Children']:
        ou_count = ou_count+1

        ou_tree[root_org_id+'|'][top_child['Id']+'|'][second_child['Id']+'|'] = {}
        ou_tree[root_org_id+'|'][top_child['Id']+'|'][second_child['Id']+'|']['accounts'] = []
        ou_tree[root_org_id+'|'][top_child['Id']+'|'][second_child['Id']+'|']['controls'] = []

        ou_tree[root_org_id+'|'][top_child['Id']+'|'][second_child['Id']+'|']['description'] = describe_ou(second_child['Id'])

        second_ou_name = ou_tree[root_org_id+'|'][top_child['Id']+'|'][second_child['Id']+'|']['description']['Name']
        controls_by_ou[root_org_id+'|'+top_ou_name+'|'+second_ou_name+'|'] = []

        arn=ou_tree[root_org_id+'|'][top_child['Id']+'|'][second_child['Id']+'|']['description']['Arn']
        list_enabled_controls(arn=arn, next_token='', root_org_id=root_org_id, top_child_id=top_child['Id'], second_child_id=second_child['Id'])

        get_accounts_in_ou(ou=second_child['Id'], accounts=[], next_token='', root_org_id=root_org_id, top_child_id=top_child['Id'], second_child_id=second_child['Id'] )


#pp.pprint(ou_tree)
#pp.pprint(ou_count)
#pp.pprint(all_controls)
#pp.pprint(account_numbers)
#pp.pprint(controls_by_ou)
#for service in sorted(webservices):
#    pp.pprint(service)

account_number_list = []
for account in account_numbers:
    account_number_list.append(account['Id'])

pp.pprint(len(account_number_list))
pp.pprint(sorted(account_number_list))
