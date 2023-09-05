import requests
import config
from datetime import datetime
from dateutil.relativedelta import relativedelta 
import re
import time
import functions_framework
start = time.time()
notesSeparator = '\n___________________________________\n'
now = datetime.now()
last_month_date = now + relativedelta(months=-1)


asanaTasks = []
asanaJiraMap = {}
newJiraTasks = []
processed = []
def deleteOldTasks():
    for key in asanaJiraMap:
        requests.post(config.asanaTasksURL + asanaJiraMap[key] + "/removeProject", json={'data':{'project':'1204461209029132'}},headers=config.asanaHeaders, proxies=config.proxies)

def queryAsanaBoard(r):   
    for task in r['data']:
        asanaTasks.append(task['gid'])
        for cf in task['custom_fields']:
            if cf['gid'] == '1204401545023806':
                asanaJiraMap[cf['display_value']] = task['gid']


# Add FBL MOB VOICE <> Tasks to Telus Jira Tracker board
def fblAsanaTasks(fbl):
    for task in fbl['data']:
        if 'FBL MOB Voice <>' in task['name'] and task['gid'] not in asanaTasks and not task['completed']:
            print('adding '+ task['gid'] +' to Telus Jira Tracker')
            requests.post(config.asanaTasksURL + task['gid'] + '/addProject', json={'data': {'project': '1204461209029132'}}, headers=config.asanaHeaders, proxies=config.proxies)
            asanaTasks.append(task['gid'])
            newJiraTasks.append(task['gid'])
            print('creating jira task...')
            body = config.jiraTaskBody
            body['fields']['customfield_10011'] = task['notes']
            body['fields']['summary'] = task['name']
            jiraNewTask = requests.post(config.jiraIssueURL, json=body, headers=config.jiraHeaders).json()
            asanaJiraMap[jiraNewTask['key']] = task['gid']
            print('created new task...', jiraNewTask['key'])

def preprocessing():
    r = requests.get(config.asanaTasksURL+'?project=1204461209029132&opt_fields=custom_fields.display_value', headers=config.asanaHeaders, proxies=config.proxies)
    if r.status_code != 200:
        raise Exception("Error while querying asana board ", r.status_code)
    queryAsanaBoard(r.json())
    fbl = requests.get(config.asanaTasksURL+'?project=1204725698301735&opt_fields=notes,name, completed', headers=config.asanaHeaders, proxies=config.proxies)
    if fbl.status_code != 200:
        raise Exception("Error while querying asana board")
    fblAsanaTasks(fbl.json()) 

def syncJiraToAsana(jiraTask):
    lastComment = jiraTask['fields']['customfield_10200'] if jiraTask['fields']['customfield_10200'] != None else ""
    description = jiraTask['fields']['customfield_10011'] if jiraTask['fields']['customfield_10011'] != None else jiraTask['fields']['description'] if jiraTask['fields']['description'] != None else ""
    notes = "Last Synced on " + str(now) + notesSeparator + re.sub("{([^\s]+)]|{([^\s]+)}|\\r|h[1-9]", "",description )
    notes += notesSeparator + re.sub("{([^\s]+)]|{([^\s]+)}|\\r|h[1-9]", "",lastComment)
    epicId = jiraTask['fields']['customfield_10001']
    epicName = "Empty Epic"
    if epicId != None:
        epicRes = requests.get(config.jiraIssueURL + epicId +"?fields=customfield_10004", headers=config.jiraHeaders).json()
        epicName = epicRes['fields'].get('customfield_10004', "")
    status = jiraTask['fields']['status']['name']
    sprint = jiraTask['fields']['customfield_10000'][-1].split("name=")[1].split(" ")[0] if jiraTask['fields']['customfield_10000'] != None else "No Sprint added"
    taskId = ""
    if jiraTask['key'] in asanaJiraMap:
        print('updating...', asanaJiraMap[jiraTask['key']])
        taskId = asanaJiraMap[jiraTask['key']]
        updateBody = {
            'data': {
                'notes': notes,
                'custom_fields': {
                    '1204401545023806': jiraTask['key'],
                    '1204461209029194': epicName,
                    '1204401548348079': status,
                    '1204473662622579': sprint,
                    '1204473653374534': '1204474208006017'
                }
            }
        }
        if status == 'Done':
            updateBody['data']['completed'] = True
        requests.put(config.asanaTasksURL + asanaJiraMap[jiraTask['key']], json=updateBody , headers=config.asanaHeaders, proxies=config.proxies)
        jiraComment = requests.get(config.jiraIssueURL+jiraTask['key']+'/comment', headers=config.jiraHeaders).json()
        jiraCommentCount = 0
        for c in jiraComment['comments']:
            if c['author']['key'] == 'x269332':
                jiraCommentCount += 1
        asanaComment = requests.get(config.asanaTasksURL + asanaJiraMap[jiraTask['key']] +'/stories', headers=config.asanaHeaders, proxies=config.proxies).json()

        for ac in asanaComment['data']:
            if ac['resource_subtype'] == 'comment_added':
                if jiraCommentCount == 0 and not updateBody['data'].get('completed', False):
                    asanaJiraComment = 'Comment from '+ac['created_by']['name']+ '  ' + ac['created_at'] + ':\n' + ac['text']
                    requests.post(config.jiraIssueURL+jiraTask['key']+'/comment', json={'body': asanaJiraComment} ,headers=config.jiraHeaders).json()
                else:
                    jiraCommentCount -= 1
        del asanaJiraMap[jiraTask['key']]
    else:
        print('creating...', jiraTask['fields']['summary'])
        createBody = {
            'data': {
                'name': jiraTask['fields']['summary'],
                'notes': notes,
                'custom_fields': {
                    '1204401545023806': jiraTask['key'],
                    '1204461209029194': epicName,
                    '1204401548348079': status,
                    '1204473662622579': sprint,
                    '1204473653374534': '1204474208006017'
                },
                'projects': [ '1204461209029132' ]
            }
        }
        if 'Google FBL' in jiraTask['fields']['summary'] or 'FBL Google' in jiraTask['fields']['summary']:
            createBody['data']['projects'].append('1204725698301735')
            createBody['data']['custom_fields']['1204882672226296'] = '1205076664988559'
        asanaCreate = requests.post(config.asanaTasksURL, json=createBody, headers=config.asanaHeaders, proxies=config.proxies).json()
        taskId = asanaCreate['data']['gid']
    sectionId = config.sections.get(status.lower(), '1204461209029133')
    requests.post('https://app.asana.com/api/1.0/sections/'+sectionId+'/addTask', json={'data': {'task': taskId}}, headers=config.asanaHeaders, proxies=config.proxies)
    return jiraTask['key']
    


@functions_framework.http
def syncAsanaJira(request):
    try:
        request_args = request.args
        if request_args and "asanaToken" in request_args and "jiraToken" in request_args:
            config.asanaHeaders['Authorization'] += request_args['asanaToken']
            config.jiraHeaders['Authorization'] += request_args['jiraToken']
            preprocessing()
            jiraTasks = requests.get(config.jiraSearchURL + last_month_date.strftime('%Y/%m/%d') +'" ORDER BY updated DESC', headers=config.jiraHeaders).json()
            for task in jiraTasks['issues']:
                syncJiraToAsana(task)
            deleteOldTasks()
            return ('Ok', 200)
        else:
            raise Exception("Asana token and/or Jira token is missing")
    except Exception as e:  
        return (str(e), 400)
