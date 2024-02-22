from prefect import flow, task, get_run_logger, pause_flow_run
from prefect.artifacts import create_table_artifact
from prefect.input import RunInput
from enum import Enum
from typing import Optional
import requests

class Title(Enum):
    Mr = "Mr"
    Mrs = "Mrs"
    Ms = "Ms"
    Dr = "Dr"

class Approval(Enum):
    Approve = "Approve"
    Reject = "Reject"

class NameInput(RunInput):
    title: Optional[Title]
    first_name: Optional[str]  
    last_name: Optional[str]  
    description: Optional[str]
    approve: Approval = Approval.Reject  

@task(name="Fetching URL", retries = 1, retry_delay_seconds = 5, retry_jitter_factor = 0.1)
def fetch(url: str):
    logger = get_run_logger()
    response = requests.get(url)
    raw_data = response.json()
    logger.info(f"Raw response: {raw_data}")
    return raw_data

@task(name="Cleaning Data")
def clean(raw_data: dict):
    results = raw_data.get('results')[0]
    logger = get_run_logger()
    logger.info(f"Cleaned results: {results}")
    return results['name']

@flow(name="Create Names")
def create_names(num: int = 2):
    df = []
    url = "https://randomuser.me/api/"
    logger = get_run_logger()
    copy = num
    while num != 0:
        raw_data = fetch(url)
        df.append(clean(raw_data))
        num -= 1
    logger.info(f"create {copy} names: {df}")
    return df

@flow(name="Redeploy Flow")
def redeploy_flow():
    logger = get_run_logger()
    user_input = pause_flow_run(wait_for_input = NameInput)
    if user_input.first_name != None:
        logger.info(f"User input: {user_input.first_name} {user_input.last_name}!")
    # raw type of user_input
    input = {'title': user_input.title.value, 
             'first': user_input.first_name, 
             'last': user_input.last_name}
    list_of_names.append(input)
    if(user_input.approve.value == 'Approve'):
        logger.info(f"Report approved! Creating artifact...")
        create_table_artifact(
            key="name-table",
            table=list_of_names,
            description = user_input.description
        )
    else:
        raise Exception("User did not approve")

if __name__ == "__main__":
    list_of_names = create_names()
    redeploy_flow()  
