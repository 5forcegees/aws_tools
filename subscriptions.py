#  https://github.com/dannysteenman/aws-toolbox
#
#  License: MIT
#
# This script returns a list of log subscriptions 

import boto3

# Create CloudWatchLogs client
cloudwatch_logs = boto3.client('logs')

# List subscription filters through the pagination interface
paginator = cloudwatch_logs.get_paginator('describe_subscription_filters')
for response in paginator.paginate(logGroupName='GROUP_NAME'):
    print(response['subscriptionFilters'])