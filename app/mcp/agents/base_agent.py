from app.mcp.agents.analyzer_agent import AnalyzerAgent
from app.mcp.agents.content_agent import ContentAgent
from app.mcp.agents.qa_agent import QAAgent
from app.mcp.agents.strategy_agent import StrategyAgent
from app.mcp.agents.structure_agent import StructureAgent


class BaseAgent:
    def __init__(self, llm):
        self.analyzer = AnalyzerAgent(llm)
        self.strategy = StrategyAgent(llm)
        self.structure = StructureAgent(llm)
        self.content = ContentAgent(llm)
        self.qa = QAAgent(llm)

    def run(self, raw):

        data = self.analyzer.run(raw)
        strategy = self.strategy.run(data)
        structure = self.structure.run(strategy)
        content = self.content.run(structure)
        final = self.qa.run(content)

        return final