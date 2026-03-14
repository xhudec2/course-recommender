from ollama import chat
import json


def get_parser_prompt(user_question):
    return f"""You are an assistant.

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
    a reformulated question from the user, drop any information about study periods or owners.
    """


def parse_question(user_question):
    response = chat(
        model="qwen3:4b",
        messages=[{"role": "user", "content": get_parser_prompt(user_question)}],
        format="json",
        stream=False,
    )
    try:
        return json.loads(response.message.content)
    except Exception as e:
        print(f"Failed to parse question {e}")
