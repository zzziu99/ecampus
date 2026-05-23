"""
火车谋杀案推理游戏
多个 agent 扮演乘客，其中一个藏着秘密，AI 探长出马破案
"""

from crewai import Agent, Task, Crew, Process
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

# 确保有可用的 API key
api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ 请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 环境变量")
    exit(1)

# 判断用的啥模型
if os.getenv("DEEPSEEK_API_KEY"):
    model = "deepseek-chat"
    provider = "deepseek"
else:
    model = "gpt-4o-mini"
    provider = "openai"

print(f"🕵️ 侦探使用模型: {provider}/{model}")
print("=" * 50)

# ==================== 案情设定 ====================
# 每个乘客的角色卡（只对他们自己可见）
PASSENGERS = {
    "王富贵": {
        "role": "50岁富商，坐在头等车厢",
        "secret": "你破产了，这趟车是去投靠远亲的。你认识死者李国华，他之前骗了你一大笔钱。",
        "personality": "暴躁、爱面子，说话冲"
    },
    "林梦瑶": {
        "role": "28岁旗袍女郎，带着一个手提箱",
        "secret": "你是死者的情妇，手提箱里装着死者的把柄证据，准备威胁他。",
        "personality": "妩媚、冷静，说话带刺"
    },
    "赵铁柱": {
        "role": "45岁退伍军人，硬座车厢",
        "secret": "你曾是死者的下属，被他陷害开除。你在车厢里偶遇他，非常震惊。",
        "personality": "沉默寡言，但情绪容易激动"
    },
    "苏小婉": {
        "role": "32岁女医生，软卧车厢",
        "secret": "死者是你前夫，长期家暴，你逃到外地重新开始。这趟车只是巧合。",
        "personality": "温和有礼，回避冲突"
    },
    "陈大华": {
        "role": "60岁老刑警，退休后旅游",
        "secret": "你以前办过死者的案子但没办下来，一直耿耿于怀。你认出他了。",
        "personality": "观察力强，老练沉稳"
    },
    "周明": {
        "role": "35岁列车员",
        "secret": "你听到了争吵声，但没敢多管。你隐约看到有人从死者车厢跑出来。",
        "personality": "胆小怕事，但很八卦"
    }
}

# ==================== 创建 Agent ====================

# 侦探
detective = Agent(
    role="侦探",
    goal="通过审问所有嫌疑人，还原案发经过，找出真凶",
    backstory="你是民国最著名的探长，思维缜密，洞察人心。"
             "火车上发生了一起谋杀案，你必须在到站前破案。"
             "死者是李国华，被发现死在头等车厢，胸口被刀刺中。死亡时间约一小时前。",
    allow_delegation=False,
    verbose=True,
    llm_config={"model": model, "provider": provider}
)

# 创建每个乘客 agent
suspects = {}
for name, info in PASSENGERS.items():
    suspects[name] = Agent(
        role=info["role"],
        goal=f"回答侦探的问题，但不要主动暴露自己的秘密",
        backstory=(
            f"你是{name}，{info['role']}。{info['personality']}。\n"
            f"你的秘密：{info['secret']}\n"
            f"你当然不是凶手（除非你真是），但你有需要隐瞒的事情。"
        ),
        allow_delegation=False,
        verbose=False,
        llm_config={"model": model, "provider": provider}
    )

# ==================== 任务规划 ====================

tasks = []

# 开场：探长了解案情
tasks.append(Task(
    description="""
    案情简报：K-1926次列车行驶途中，乘客李国华在头等车厢被刺身亡。
    刀是列车餐车的水果刀，没有指纹。死亡时间约在晚上9点到10点之间。

    现在你要列一份调查计划，包含：
    1. 确认所有嫌疑人名单
    2. 计划审问顺序和重点问题
    3. 要检查的关键证据位置

    先输出你的计划，然后开始调查。
    """,
    agent=detective,
    expected_output="包含嫌疑人名单和调查计划的推理笔记"
))

# 逐个审问
for name, info in PASSENGERS.items():
    tasks.append(Task(
        description=f"""
        审问嫌疑人 {name}（{info['role']}）。

        你需要问清楚：
        - 案发时他在哪里，有没有证人
        - 他和死者的关系
        - 有没有看到或听到什么异常
        - 他为什么坐这趟车

        记住：你要观察他的反应是否自然，有没有隐瞒什么。
        """,
        agent=detective,
        expected_output=f"审问{name}的记录和初步判断"
    ))

# 破案总结
tasks.append(Task(
    description="""
    你已经审问了所有嫌疑人。现在请综合分析：

    1. 每个人的证词有没有矛盾？
    2. 谁有杀人动机？
    3. 谁有机会作案？
    4. 证据指向谁？

    最后输出你的结论：谁是凶手？杀人动机是什么？还原案发经过。

    注意：凶手可能是任何一个乘客，也可能是列车员周明。
    根据审问得到的线索推理，不要预设答案。
    """,
    agent=detective,
    expected_output="包含凶手、动机和案发经过的完整破案报告"
))

# ==================== 启动 ====================

crew = Crew(
    agents=[detective] + list(suspects.values()),
    tasks=tasks,
    process=Process.sequential,
    verbose=True
)

print("🚂 列车开动了...")
print("💀 一声尖叫划破夜空——有人死了！")
print("=" * 50)

result = crew.kickoff()

print("\n" + "=" * 50)
print("📋 最终破案报告")
print("=" * 50)
print(result)
