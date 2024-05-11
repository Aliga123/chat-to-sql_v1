#####################################
#1. 使用GPT作为LLM，实现与SQL数据库的交互。
#####################################
# 设置openai的key
import os
os.environ["OPENAI_API_KEY"] = "your_key"

from langchain import OpenAI, SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.chat_models import ChatOpenAI

# 设置OpenAI模型
#llm = OpenAI(temperature=0)
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)  # 注意模型名称可能需要根据实际可用模型调整

from langchain.prompts.prompt import PromptTemplate
# 自定义prompt
_DEFAULT_TEMPLATE = """Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Use the following format:

Question: "Question here"
SQLQuery: "SQL Query to run"
SQLResult: "Result of the SQLQuery"
Answer: "Final answer here"

Only use the following tables:

{table_info}


Question: {input}"""
PROMPT = PromptTemplate(
    input_variables=["input", "table_info", "dialect"], template=_DEFAULT_TEMPLATE
)

# 连接到MySQL数据库
db_user = "your_user"
db_password = "your_password"
db_host = "your_ip"
db_name = "your_database"
db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

# 创建chain
#db_chain = SQLDatabaseChain(llm=llm, database=db, verbose=True)
db_chain = SQLDatabaseChain(llm=llm, database=db, prompt=PROMPT, verbose=True)

############################################
#2. 使用ChatGlm-6b作为LLM，实现与SQL数据库的交互。
# 注意：在 CPU 上运行时，会根据硬件自动编译 CPU Kernel ，请确保已安装 GCC 和 OpenMP （Linux一般已安装，对于Windows则需手动安装）。需要大概 32GB 内存。
###########################################
from transformers import AutoTokenizer, AutoModel
from transformers import pipeline
from langchain import HuggingFacePipeline
import torch, logging

def loding_local_chain():
    # 加载本地ChatGlm-6b模型
    tokenizer = AutoTokenizer.from_pretrained("model/ChatGlm-6b", trust_remote_code=True)
    model = AutoModel.from_pretrained("model/ChatGlm-6b", trust_remote_code=True).half().cuda()

    # 默认为无 GPU，但如果可用，请使用 GPU 和半精度模式
    device_id = -1  # default to no-GPU, but use GPU and half precision mode if available
    if torch.cuda.is_available():
        device_id = 0
        try:
            model = model.half()
        except RuntimeError as exc:
            logging.warn(f"Could not run model in half precision mode: {str(exc)}")

    pipe = pipeline(task="text2text-generation", model=model, tokenizer=tokenizer, max_length=1024, device=device_id)
    local_llm = HuggingFacePipeline(pipeline=pipe)

    # 创建本地模型的chain
    local_chain = SQLDatabaseChain.from_llm(local_llm, db, verbose=True, return_intermediate_steps=True, use_query_checker=True)
    return local_chain

# 使用自然语言进行SQL查询
def text2SQL(question, model):
    # 使用API
    if model == 'GPT3.5':
        db_chain.run(question)
    # 使用本地模型, 注意在无GPU情况下，请确保已安装 GCC 和 OpenMP （Linux一般已安装，对于Windows则需手动安装），且需要大概 32GB 内存。
    if model == 'ChatGlm-6b':
        local_chain = loding_local_chain()
        local_chain(question)


# 运行时，会有很多库版本落后警告，不用管
text2SQL("有哪些产品？", 'GPT3.5')
text2SQL("哪个产品卖的最多？", 'GPT3.5')
text2SQL("请问5月15日的销售额是多少？", 'GPT3.5')

