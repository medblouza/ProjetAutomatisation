import logging
import time
from app.llm.llm_tool import LLMTool
from app.mcp.agents.analyzer_agent  import AnalyzerAgent
from app.mcp.agents.brief_agent     import BriefAgent
from app.mcp.agents.strategy_agent  import StrategyAgent
from app.mcp.agents.structure_agent import StructureAgent
from app.mcp.agents.content_agent   import ContentAgent
from app.mcp.agents.qa_agent        import QAAgent


logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Pipeline : analyzer → brief → strategy → structure → content → qa
    """

    def __init__(self, llm: LLMTool):
        self.analyzer  = AnalyzerAgent(llm)
        self.brief     = BriefAgent(llm)
        self.strategy  = StrategyAgent(llm)
        self.structure = StructureAgent(llm)
        self.content   = ContentAgent(llm)
        self.qa        = QAAgent(llm)

    def run(self, raw_data: dict) -> dict:
        total_start = time.time()
        logger.info("=" * 60)
        logger.info("[Pipeline] 🚀 Démarrage génération CDC")
        logger.info(f"[Pipeline] Entreprise : {raw_data.get('company_name', 'Inconnue')}")
        logger.info("=" * 60)

        try:
            # Étape 1 : Analyse
            analyzed  = self._run_step("Analyzer",  self.analyzer.run,  raw_data)
            time.sleep(1)
            # Étape 2 : Brief créatif ← nouveau
            briefed   = self._run_step("Brief",     self.brief.run,     analyzed)
            time.sleep(1)
            # Étape 3 : Stratégie
            strategy  = self._run_step("Strategy",  self.strategy.run,  briefed)
            time.sleep(1)
            # Étape 4 : Structure
            structure = self._run_step("Structure", self.structure.run, strategy)
            time.sleep(1)
            # Étape 5 : Contenu
            content   = self._run_step("Content",   self.content.run,   structure)
            time.sleep(1)
            # Étape 6 : QA
            final     = self._run_step("QA",        self.qa.run,        content)

            total_time = time.time() - total_start
            logger.info(f"[Pipeline] 🎉 CDC généré en {total_time:.1f}s — Score : {final.get('score', 0)}/100")

            return final

        except Exception as e:
            logger.error(f"[Pipeline] ❌ Erreur critique : {e}", exc_info=True)
            return {
                "score":   0,
                "content": f"Erreur lors de la génération : {str(e)}",
                "issues":  [str(e)],
                "meta":    {"company": raw_data.get("company_name", "")},
            }

    def _run_step(self, name: str, func, data: dict) -> dict:
        try:
            start = time.time()
            logger.info(f"[Pipeline] ▶ Étape {name}...")
            result = func(data)
            logger.info(f"[Pipeline] ✅ {name} terminé en {time.time() - start:.1f}s")
            return result if isinstance(result, dict) else data
        except Exception as e:
            logger.error(f"[Pipeline] ❌ Erreur dans {name} : {e}", exc_info=True)
            return data