proxies ={
    "http": 'http://198.161.14.25:8080',
    "https": 'http://198.161.14.25:8080'
}

asanaHeaders = {
    'Authorization': "Bearer "
}

jiraHeaders = {
    'Authorization': "Basic "
}

#URLS
asanaTasksURL = 'https://app.asana.com/api/1.0/tasks/'
jiraSearchURL = 'https://jira.tsl.telus.com/rest/api/2/search?jql=component="ACXUX Google" and status!=Cancelled and status!=Archived and updated>="'
jiraIssueURL = 'https://jira.tsl.telus.com/rest/api/2/issue/'

sections = {
    'placeholder': '1204461209029133',
    'groomed': '1204461209029189',
    'to do': '1204461209029189',
    'in development': '1204461209029190',
    'blocked': '1204461209029190',
    'in testing': '1204461209029190',
    'test ready': '1204461209029190',
    'deployment ready': '1204461209029193',
    'deployment': '1204461209029193',
    'done': '1204461209029193'
}

jiraTaskBody = {
    'fields': {
        'project': {
            "id": "24348"
        },
        "issuetype": {
            "id": "3"
        },
        'priority': {
            'id': "3"
        },
        "components": [
            {'id': "28349"},
            {'id': "32374"}
        ],
        "labels": [
            "FBL",
            "Optimization"
        ]          
    }
}