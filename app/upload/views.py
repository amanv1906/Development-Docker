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


@api_view(['GET'])
def Message(request):
    '''
    returns the message for demo
    '''
    message = request.query_params.get('message', 'creating_api in')
    d1 = {'message': message}
    return Response(d1)


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


def progress_report(WorkProgress, JiraIssue):
  '''
  Return the prohgress with
  there work id
  '''

  final_progress = {}
  for per_project in WorkProgress:
    all_task = per_project['WorkItem.associated_work_items']
    for task in all_task:
      my_task = task
      sub_task = my_task['WorkItem.associated_work_items']
      overall_sub_task_work = 0
      for subt in sub_task:
        sub = subt
        objects = sub['WorkItem.associated_objects']
        work_done = jira_object_work(objects, JiraIssue)
        final_progress[sub['WorkItem.id']] = int(work_done)
        start_date = sub['WorkItem.start_date'][0:10]
        end_date = sub['WorkItem.end_date'][0:10]
        date_format = "%Y-%m-%d"
        a = datetime.strptime(start_date, date_format)
        b = datetime.strptime(end_date, date_format)
        delta = b - a
        date_diff = diff_date(start_date, end_date)
        overall_sub_task_work += (work_done*date_diff)
        total_work_done_task = overall_sub_task_work/100
      task_start_date = my_task['WorkItem.start_date'][0:10]
      task_end_date = my_task['WorkItem.end_date'][0:10]
      task_date_diff = diff_date(task_start_date, task_end_date)
      task_work_done=ceil(total_work_done_task/task_date_diff*100)
      final_progress[my_task['WorkItem.id']] = int(task_work_done)
    project_start_date = per_project['WorkItem.start_date'][0:10]
    project_end_date = per_project['WorkItem.end_date'][0:10]
    project_date_diff = diff_date(project_start_date,project_end_date)
    final_progress[per_project['WorkItem.id']] = ceil(overall_sub_task_work/project_date_diff)
    return final_progress


@api_view(['GET'])
def progress(request):
    '''
    Show the percentage of work id
    with there complete percentage
    '''

    ppl = query_1(client)
    WorkProgress, JiraIssue = work_items_objects(ppl)
    final_progres = progress_report(WorkProgress, JiraIssue)
    return Response(final_progres)
