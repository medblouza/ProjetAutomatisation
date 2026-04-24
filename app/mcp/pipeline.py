''''
from app.llm.llm_tool import OllamaClient
from app.mcp.agents.analyzer_agent import AnalyzerAgent
from app.mcp.agents.strategy_agent import StrategyAgent
from app.mcp.agents.structure_agent import StructureAgent
from app.mcp.agents.content_agent import ContentAgent
from app.mcp.agents.qa_agent import QAAgent


class CDCPipeline:

    def __init__(self):
        llm = OllamaClient()

        self.analyzer = AnalyzerAgent(llm)
        self.strategy = StrategyAgent(llm)
        self.structure = StructureAgent(llm)
        self.content = ContentAgent(llm)
        self.qa = QAAgent(llm)

    def run(self, raw_data):

        print("Cleaning...")
        clean = clean_data(raw_data)

        print("Analysis...")
        analysis = self.analyzer.run(clean)

        print("Strategy...")
        strategy = self.strategy.run(analysis)

        print("Structure...")
        structure = self.structure.run(strategy)

        print("CDC...")
        cdc = self.content.run({
            "analysis": analysis,
            "strategy": strategy,
            "structure": structure
        })

        print("QA...")
        final = self.qa.run(cdc)

        return final
'''