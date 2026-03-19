from ollama import chat
import json


def get_parser_prompt(user_question):
    return f"""
    You are a part of a system that uses ChromaDB and similarity search on course descriptions (that have up to 500 words)
    to find what a user is looking for. Your task is to parse the user prompt and then reformulate the user's question
    to make it sound like a course description.

    This is a prompt from a user:
    {user_question}

    Your task is to parse it and output 3 things as a json:
    periods: 
    as a list of study periods, allowed values for study periods are: sp1, sp2, sp3, sp4, no period, summer
    it can also be empty if the user does not mention it.

    owners:
    as a list of owner study programmes, allowed study programmes:
    ['MPMAR', 'MPWPS', 'MPMOB', 'MPPEN', 'TRACKS', 'MPMCN', 'MPISC', 'MPPDE', 'MPIDE', 'MPDSC', 'MPALG', 'MPMEI', 'MPCAS', 'MPPHS', 'MPBIO', 'MPEPO', 'MPICT', 'MPSOF', 'MPMED', 'MPEES', 'MPIEE', 'MPDES', 'MPAME', 'MPENM', 'MPTSE', 'MPARC', 'MPCSC', 'MPDSD', 'MPSEB', 'MPAEM', 'MPQOM', 'MPHPC', 'MPSYS', 'MPDCM', 'MPSCM', 'MPSES', 'MPSOV', 'MPBDP', 'MPLOL', 'MPNAT']
    it can also be empty if the user does not mention it.
    
    question:
    Make a course description based on the information given by the user, drop any information about study periods or owners.
    Reformulate it in such a way that it sounds like a course description and include any information that should be in the
    course based on your knowledge. Do not make up too much information.
    """


def parse_question(user_question):
    response = chat(
        model="gpt-oss:20b-cloud",
        messages=[{"role": "user", "content": get_parser_prompt(user_question)}],
        format="json",
        stream=False,
    )
    jsons = response.message.content[8:-4]
    try:
        return json.loads(jsons)
    except Exception as e:
        print(f"Failed to parse question {e}")
