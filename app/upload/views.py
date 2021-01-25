from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from datetime import datetime
from math import ceil

import pydgraph

client_stub = pydgraph.DgraphClientStub \
    .from_slash_endpoint(
        "https://fablkt.us-west-2.aws.cloud.dgraph.io/graphql",
        "ecobQm0AP8y2hcB4zSd6zbcHhwjxXzsbfDFqXHiXDxk=")
client = pydgraph.DgraphClient(client_stub)


# Query for data.
def query_1(client):
    query = """
    {
     WorkProgress(func: type(WorkItem))
    @filter(eq(WorkItem.type, "project"))
    {
        WorkItem.id
         WorkItem.name
         WorkItem.type
         WorkItem.start_date
         WorkItem.end_date
         WorkItem.associated_objects{
             Object.obj_id
         }
         WorkItem.associated_work_items{
             WorkItem.id
             WorkItem.name
             WorkItem.type
             WorkItem.start_date
             WorkItem.end_date
             WorkItem.associated_objects{
                 Object.obj_id
             }
             WorkItem.associated_work_items{
             WorkItem.id
             WorkItem.name
             WorkItem.type
             WorkItem.start_date
             WorkItem.end_date
             WorkItem.associated_objects{
                 Object.obj_id
             }
         WorkItem.associated_work_items{
             WorkItem.id
             WorkItem.name
             WorkItem.type
             WorkItem.start_date
             WorkItem.end_date
             WorkItem.associated_objects{
                 Object.obj_id
             }
         }
         }
         }
     }
     JiraStory(func: type(JiraIssue)){
         JiraIssue.summary
         JiraIssue.status
         Object.obj_id
     }
     }
     """
    txn = client.txn()
    try:
        res = txn.query(query)
        ppl = json.loads(res.json)
    finally:
        txn.discard()
    return ppl


@api_view(['GET','POST'])
def Message(request):
    '''
    returns the message for demo
    '''
    data = request.data
    # d1 = {'message': message}
    return Response(data)


def work_items_objects(items):
    '''
    To return the WorkItem
    and Jira Id
    '''

    WorkProgres = items["WorkProgress"]
    JiraIssue = items["JiraStory"]
    return WorkProgres, JiraIssue


def get_jira_issue_status(JiraIssue):
    '''
    It stores the status of 
    jira issue whether done, Inprogres etc
    '''

    issue_status = {}
    for issue in JiraIssue:
        per_issue = issue
        issue_status[per_issue['Object.obj_id']] = per_issue['JiraIssue.status']
    return issue_status


def diff_date(start_date,end_date):
    '''
    It calculated the days
    between different start and end
    '''

    date_format = "%Y-%m-%d"
    a = datetime.strptime(start_date, date_format)
    b = datetime.strptime(end_date, date_format)
    delta = b - a 
    date_diff = (delta.days + 1)
    return date_diff


def jira_object_work(objects, JiraIssue):
  '''
  It calculates the percentage
  of sub work done by status of 
  Jira Issue
  '''

  total_count = 0
  done_count = 0
  issue_status = get_jira_issue_status(JiraIssue)
  for obj in objects:
    issue = issue_status[obj['Object.obj_id']]
    if(issue=='Done' or issue == 'done'):
      done_count += 1
    total_count += 1
  work_done = (done_count/total_count)*100
  return work_done


def check_ispartof(WorkProgress, work_id):
  '''
  Check whether the given workItem
  is present in project , task or subtask
  '''
  if(WorkProgress['WorkItem.id'] in work_id):
    return True
  else:
    for task in WorkProgress['WorkItem.associated_work_items']:
      if(task['WorkItem.id'] in work_id):
        return True
      else:
        for sub_task in task['WorkItem.associated_work_items']:
          if(sub_task['WorkItem.id'] in work_id):
            return True
    return False


def progress_report(WorkProgress, JiraIssue, work_ids):
  final_progress = {}
  current_length=0
  length=len(work_ids)
  for per_project in WorkProgress:
    if(check_ispartof(per_project, work_ids) == False):
      continue
    all_task = per_project['WorkItem.associated_work_items']
    for task in all_task:
      my_task = task
      sub_task = my_task['WorkItem.associated_work_items']
      overall_sub_task_work = 0
      for subt in sub_task:
        sub = subt
        objects = sub['WorkItem.associated_objects']
        work_done = jira_object_work(objects, JiraIssue)
        if(sub['WorkItem.id'] in work_ids):
          final_progress[sub['WorkItem.id']] = int(work_done)
          current_length += 1
        if(current_length == length):
          return final_progress
        start_date = sub['WorkItem.start_date'][0:10]
        end_date = sub['WorkItem.end_date'][0:10]
        date_diff = diff_date(start_date, end_date)
        overall_sub_task_work += (work_done*date_diff)
        total_work_done_task = overall_sub_task_work/100
      task_start_date = my_task['WorkItem.start_date'][0:10]
      task_end_date = my_task['WorkItem.end_date'][0:10]
      task_date_diff = diff_date(task_start_date, task_end_date)
      task_work_done=ceil(total_work_done_task/task_date_diff*100)
      if(my_task['WorkItem.id'] in work_ids):
        final_progress[my_task['WorkItem.id']] = int(task_work_done)
        current_length += 1
      if(current_length == length):
        return final_progress
    project_start_date = per_project['WorkItem.start_date'][0:10]
    project_end_date = per_project['WorkItem.end_date'][0:10]
    project_date_diff = diff_date(project_start_date,project_end_date)
    if(per_project['WorkItem.id'] in work_ids):
      final_progress[per_project['WorkItem.id']] = ceil(overall_sub_task_work/project_date_diff)
      current_length += 1
    if(current_length == length):
      return final_progress
    return final_progress


@api_view(['GET', 'POST'])
def progress(request):
    '''
    Show the percentage of work id
    with there complete percentage
    '''

    all_data = query_1(client)
    try:
        work_id = request.data['work_id']
    except KeyError:
        work_id = request.data

    WorkProgress, JiraIssue = work_items_objects(all_data)
    final_progres = progress_report(WorkProgress, JiraIssue, work_id)
    return Response(final_progres)