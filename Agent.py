import streamlit as st
import os
from datetime import datetime
import openai
import json
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 设置OpenAI API版本
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_VERSION"] = "2024-03-01-preview"  # 使用最新的API版本

# LangChain and Neo4j
from langchain_experimental.openai_assistant import OpenAIAssistantRunnable
from langchain_core.agents import AgentFinish, AgentAction
from neo4j import GraphDatabase
import numpy as np


DATA_STEWARD_INSTRUCTIONS = """
You are a helpful XXXXXX

Your expertise spans:
- XXXX
- XXXX
- XXXX
- XXXX

Your goals:
- XXXX
- XXXX
- XXXX

General Guidelines:
1. XXXX
2. XXXX
3. XXXX
"""



# Get environment variables for LLM and Neo4j
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_MODEL = os.getenv("OPEN_AI_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")




# Neo4j KG setup
kg_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


class OpenAIEmbedder:
    def __init__(self, model_name: str):
        self.model = model_name
        openai.api_key = OPENAI_API_KEY

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        texts = [t.strip().replace("\n", " ") for t in texts]
        response = openai.embeddings.create(model=self.model, input=texts)
        return [r.embedding for r in response.data]


embedder = OpenAIEmbedder(model_name=EMBEDDING_MODEL)


def hybrid_retrieval(query: str, top_k: int = 5, alpha: float = 0.7, ambiguity_threshold: float = 0.05) -> str:
    """
    Return top-K tables and their attributes and descriptions based on combined 
    vector+extended-degree (2-hop) scores, and prompt for clarification if ambiguous.
    """
    # Embed the query
    q_vec = np.array(embedder.embed_documents([query])[0])

    # Fetch each table’s embedding and its 2-hop degree
    fetch = """
    MATCH (t:Table)
    WHERE t.embedding IS NOT NULL
    CALL {
      WITH t
      MATCH (t)-[:HAS_ATTRIBUTE|HAS_DIMENSION|RELATED_TO*1..2]->(n)
      RETURN count(DISTINCT n) AS degree
    }
    RETURN t.name AS name, t.description AS desc, t.embedding AS emb, degree
    """

    candidates = []
    with kg_driver.session() as sess:
        for rec in sess.run(fetch):
            emb = rec["emb"] or []
            if not emb:
                continue
            vec_score = float(np.dot(q_vec, emb) /
                              (np.linalg.norm(q_vec) * np.linalg.norm(emb)))
            candidates.append({
                "name": rec["name"],
                "desc": rec["desc"],
                "vec_score": vec_score,
                "degree": rec["degree"] or 0
            })

    if not candidates:
        return "No schema context found."

    # Fuse scores and rank
    max_deg = max(c["degree"] for c in candidates)
    for c in candidates:
        # normalise the degree into [0,1] range as the degree score
        c["deg_score"] = (c["degree"] / max_deg) if max_deg > 0 else 0.0
        # combine both cosine similarity and degree score, using alpha to adjust the weights of these two scores
        c["score"] = alpha * c["vec_score"] + (1 - alpha) * c["deg_score"]

    # select the top-k from the candidates based on the fusioned score
    topk = sorted(candidates, key=lambda x: x["score"], reverse=True)[:top_k]

    # Ambiguity detection
    ambiguous = (
        len(topk) > 1 and 
        (topk[0]["score"] - topk[1]["score"] < ambiguity_threshold)
    )

    # Construct snippets for each top candidate
    snippets = []
    with kg_driver.session() as sess:
        for c in topk:
            name, desc, score = c["name"], c["desc"], c["score"]
            attr_q = """
            MATCH (t:Table {name:$name})-[:HAS_ATTRIBUTE]->(a:Attribute)
            RETURN a.name AS field, a.description AS fdesc
            ORDER BY a.name
            """
            fields = sess.run(attr_q, name=name)
            lines = [f"• {name} (score={score:.3f}): {desc}", "  Fields:"]
            for f in fields:
                lines.append(f"    – {f['field']}: {f['fdesc']}")
            snippets.append("\n".join(lines))

    return "\n\n".join(snippets)




def safe_invoke(agent, inp: dict):
    try:
        return agent.invoke(inp)
    except ValueError:
        agent.thread_id = None
        return agent.invoke({"content": inp.get("content")})


data_steward_tools = [
    {"type": "function", "function": {
        "name": "hybrid_retrieval",
        "description": "Retrieve schema context by vector+graph hybrid scoring.",
        "parameters": {"type":"object","properties":{
            "query":{"type":"string"},
            "top_k":{"type":"integer","default":5},
            "alpha":{"type":"number","default":0.7}
        },"required":["query"]}
    }}
]


# Instantiate assistant
if "data_steward_assistant" not in st.session_state:
    st.session_state.data_steward_assistant = {
        "assistant": OpenAIAssistantRunnable.create_assistant(
            name="Data Steward Assistant",
            instructions=DATA_STEWARD_INSTRUCTIONS,
            tools=data_steward_tools,
            model=OPEN_AI_MODEL,
            temperature=0,  # 修改为数字类型
            as_agent=True,
            api_version="2024-03-01-preview"  # 添加API版本
        ),
        "thread_id": None
    }


def call_function(action: AgentAction) -> str:
    params = action.tool_input
    if isinstance(params, str): params = json.loads(params)
    return globals()[action.tool](**params)


def context_injection(now: str, prompt: str) -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    context_prompt = f"""
        Current time is : {now}

        You have one data source:
        1) **Schema Context via hybrid_retrieval(...)**.

        Reminder:
            1. XXXXXX
            2. XXXXXX
            3. XXXXXX
        """
    return f"{context_prompt} \n\n{prompt}"


def execute_agent(use_assistant: str, prompt: str) -> AgentFinish:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    agent = st.session_state.data_steward_assistant
 
    # Final input
    inp = {"content": context_injection(now, prompt)}
    
    if agent["thread_id"]: 
        inp["thread_id"] = agent["thread_id"]
    
    resp = safe_invoke(agent["assistant"], inp)
    
    while not isinstance(resp, AgentFinish):
        outs = []
        for act in (resp if isinstance(resp, list) else []):
            if isinstance(act, AgentAction):
                outs.append({"output": call_function(act), "tool_call_id": getattr(act,'tool_call_id',None)})
        resp = safe_invoke(agent["assistant"], {"tool_outputs": outs,
                                                  "run_id": getattr(resp[0],'run_id',None),
                                                  "thread_id": getattr(resp[0],'thread_id',None)})
    st.session_state.data_steward_assistant["thread_id"] = resp.return_values.get("thread_id","")
    
    return resp


def write_message(role, content, save = True):
    if save:
        st.session_state.messages.append({"role": role, "content": content})

    # Write the messages to the GUI interface
    with st.chat_message(role):
        st.markdown(content)

# Submit handler
def handle_submit(message):
    # Handle the response
    with st.spinner('Thinking...'):
        res = execute_agent("Data Steward", message)
        
        write_message('assistant', res.return_values.get("output",""))


def main():
    st.set_page_config(page_title="AI Agent")
    st.title("AI Agent")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi, I'm the XXXXX Agent! How can I help you?"},
        ]

    # Display messages in Session State
    for message in st.session_state.messages:
        write_message(message['role'], message['content'], save=False)


    # Handle any user input
    if user_input := st.chat_input("Ask a question..."):

        # Display user message in chat message container
        write_message('user', user_input)

        # Generate a response
        handle_submit(user_input)



if __name__ == "__main__":
    main()




