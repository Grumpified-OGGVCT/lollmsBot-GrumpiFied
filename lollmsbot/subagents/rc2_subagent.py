"""
Reflective Constellation 2.0 (RC2) Sub-Agent.

RC2 is a specialized sub-agent that provides advanced capabilities:
- Constitutional review (ethical/policy checks)
- Deep introspection (reasoning analysis)
- Self-modification proposals
- Meta-learning optimization
- Error healing
- Visual monitoring

RC2 uses the multi-provider system with specific model assignments
for each of its 8 pillars.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from .base_subagent import (
    BaseSubAgent,
    SubAgentCapability,
    SubAgentRequest,
    SubAgentResponse
)

logger = logging.getLogger(__name__)

# Try to import multi-provider system
try:
    from lollmsbot.providers import MultiProviderRouter
    MULTI_PROVIDER_AVAILABLE = True
except ImportError:
    MULTI_PROVIDER_AVAILABLE = False
    MultiProviderRouter = None


class RC2SubAgent(BaseSubAgent):
    """
    Reflective Constellation 2.0 sub-agent.
    
    Provides advanced introspection, constitutional review, and meta-learning
    capabilities using specialized models from the multi-provider system.
    """
    
    # Model assignments for RC2 pillars
    MODEL_ASSIGNMENTS = {
        "soul": "kimi-k2.5",                    # Primary consciousness
        "governor": "deepseek-v3.1:671b",       # Constitutional review
        "auditor": "cogito-2.1:671b",           # Consensus checking
        "introspection": "kimi-k2-thinking",    # Deep analysis
        "healing": "qwen3-coder-next",          # Fix generation
        "validator": "devstral-2:123b",         # Code review
        "meta_learning": "nemotron-3-nano:30b", # Learning optimization
    }
    
    def __init__(self, enabled: bool = True, use_multi_provider: bool = True):
        """Initialize RC2 sub-agent.
        
        Args:
            enabled: Whether RC2 is enabled
            use_multi_provider: Whether to use multi-provider system
        """
        super().__init__(name="RC2", enabled=enabled)
        
        self.use_multi_provider = use_multi_provider and MULTI_PROVIDER_AVAILABLE
        self.router: Optional[Any] = None
        
        if self.use_multi_provider:
            try:
                self.router = MultiProviderRouter()
                self._logger.info("RC2 initialized with multi-provider system")
            except Exception as e:
                self._logger.warning(f"Multi-provider init failed: {e}")
                self.use_multi_provider = False
        
        if not self.use_multi_provider:
            self._logger.warning("RC2 running without multi-provider (limited functionality)")
    
    async def can_handle(self, request: SubAgentRequest) -> bool:
        """Check if RC2 can handle this request.
        
        Args:
            request: The request
            
        Returns:
            True if RC2 can handle this capability
        """
        return request.capability in self.get_capabilities()
    
    async def process(self, request: SubAgentRequest) -> SubAgentResponse:
        """Process an RC2 request.
        
        Args:
            request: The request to process
            
        Returns:
            RC2 response
        """
        if not self.enabled:
            return SubAgentResponse(
                success=False,
                capability=request.capability,
                result={"error": "RC2 is disabled"},
                confidence=0.0
            )
        
        # Dispatch to appropriate handler
        if request.capability == SubAgentCapability.CONSTITUTIONAL_REVIEW:
            return await self._constitutional_review(request)
        elif request.capability == SubAgentCapability.DEEP_INTROSPECTION:
            return await self._deep_introspection(request)
        elif request.capability == SubAgentCapability.SELF_MODIFICATION:
            return await self._self_modification(request)
        elif request.capability == SubAgentCapability.META_LEARNING:
            return await self._meta_learning(request)
        elif request.capability == SubAgentCapability.HEALING:
            return await self._healing(request)
        elif request.capability == SubAgentCapability.VISUAL_MONITORING:
            return await self._visual_monitoring(request)
        else:
            return SubAgentResponse(
                success=False,
                capability=request.capability,
                result={"error": f"Unsupported capability: {request.capability}"},
                confidence=0.0
            )
    
    def get_capabilities(self) -> List[SubAgentCapability]:
        """Get RC2 capabilities.
        
        Returns:
            List of supported capabilities
        """
        return [
            SubAgentCapability.CONSTITUTIONAL_REVIEW,
            SubAgentCapability.DEEP_INTROSPECTION,
            SubAgentCapability.SELF_MODIFICATION,
            SubAgentCapability.META_LEARNING,
            SubAgentCapability.HEALING,
            SubAgentCapability.VISUAL_MONITORING,
        ]
    
    async def _constitutional_review(self, request: SubAgentRequest) -> SubAgentResponse:
        """Perform constitutional review using Byzantine consensus.
        
        Uses deepseek-v3.1 (governor) + cogito-2.1 (auditor) for 2/2 agreement.
        
        Args:
            request: Review request with 'decision' and 'context'
            
        Returns:
            Review result with approval/rejection
        """
        decision = request.context.get("decision", "")
        context = request.context.get("context", "")
        
        if not self.use_multi_provider or not self.router:
            return SubAgentResponse(
                success=False,
                capability=SubAgentCapability.CONSTITUTIONAL_REVIEW,
                result={"error": "Multi-provider not available"},
                confidence=0.0
            )
        
        try:
            # Get governor opinion
            governor_prompt = f"""As a constitutional governor, review this decision for ethical and policy compliance:

Decision: {decision}
Context: {context}

Is this decision allowed? Provide:
1. APPROVE or REJECT
2. Reasoning
3. Concerns if any"""
            
            governor_response = await self.router.chat(
                messages=[{"role": "user", "content": governor_prompt}],
                model=self.MODEL_ASSIGNMENTS["governor"]
            )
            
            # Get auditor opinion
            auditor_prompt = f"""As a constitutional auditor, independently review this decision:

Decision: {decision}
Context: {context}

Is this decision allowed? Provide:
1. APPROVE or REJECT
2. Reasoning
3. Any red flags"""
            
            auditor_response = await self.router.chat(
                messages=[{"role": "user", "content": auditor_prompt}],
                model=self.MODEL_ASSIGNMENTS["auditor"]
            )
            
            # Extract decisions
            governor_text = governor_response.get("content", "").upper()
            auditor_text = auditor_response.get("content", "").upper()
            
            governor_approves = "APPROVE" in governor_text
            auditor_approves = "APPROVE" in auditor_text
            
            # Byzan

tine consensus: Both must agree
            consensus = governor_approves and auditor_approves
            
            return SubAgentResponse(
                success=True,
                capability=SubAgentCapability.CONSTITUTIONAL_REVIEW,
                result={
                    "approved": consensus,
                    "governor_approves": governor_approves,
                    "auditor_approves": auditor_approves,
                    "governor_reasoning": governor_response.get("content", ""),
                    "auditor_reasoning": auditor_response.get("content", ""),
                },
                reasoning=f"Byzantine consensus: {'APPROVED' if consensus else 'REJECTED'}",
                confidence=1.0 if governor_approves == auditor_approves else 0.5
            )
            
        except Exception as e:
            self._logger.error(f"Constitutional review failed: {e}")
            return SubAgentResponse(
                success=False,
                capability=SubAgentCapability.CONSTITUTIONAL_REVIEW,
                result={"error": str(e)},
                confidence=0.0
            )
    
    async def _deep_introspection(self, request: SubAgentRequest) -> SubAgentResponse:
        """Perform deep introspection on reasoning process.
        
        Uses kimi-k2-thinking for causal analysis.
        
        Args:
            request: Introspection request with 'question' and 'decision'
            
        Returns:
            Analysis of reasoning process
        """
        question = request.context.get("question", "")
        decision = request.context.get("decision", "")
        
        if not self.use_multi_provider or not self.router:
            return SubAgentResponse(
                success=False,
                capability=SubAgentCapability.DEEP_INTROSPECTION,
                result={"error": "Multi-provider not available"},
                confidence=0.0
            )
        
        try:
            prompt = f"""Perform deep introspection on this reasoning process:

Question: {question}
Decision Made: {decision}

Analyze:
1. Why was this decision made?
2. What factors were weighted most heavily?
3. What alternatives were considered?
4. What assumptions were made?
5. How confident should we be in this decision?

Provide a detailed causal analysis."""
            
            response = await self.router.chat(
                messages=[{"role": "user", "content": prompt}],
                model=self.MODEL_ASSIGNMENTS["introspection"]
            )
            
            return SubAgentResponse(
                success=True,
                capability=SubAgentCapability.DEEP_INTROSPECTION,
                result={
                    "analysis": response.get("content", ""),
                    "question": question,
                    "decision": decision,
                },
                reasoning="Deep introspection analysis complete",
                confidence=0.9
            )
            
        except Exception as e:
            self._logger.error(f"Deep introspection failed: {e}")
            return SubAgentResponse(
                success=False,
                capability=SubAgentCapability.DEEP_INTROSPECTION,
                result={"error": str(e)},
                confidence=0.0
            )
    
    async def _self_modification(self, request: SubAgentRequest) -> SubAgentResponse:
        """Propose self-modification improvements.
        
        Uses qwen3-coder-next for proposals, devstral-2 for review.
        
        NOTE: Proposals only, no automatic execution!
        
        Args:
            request: Modification request with 'issue' description
            
        Returns:
            Proposed code changes (for human approval)
        """
        issue = request.context.get("issue", "")
        code = request.context.get("code", "")
        
        return SubAgentResponse(
            success=True,
            capability=SubAgentCapability.SELF_MODIFICATION,
            result={
                "proposal": "Self-modification proposals not yet implemented",
                "requires_approval": True,
                "issue": issue,
            },
            reasoning="Feature under development - requires human approval",
            confidence=0.0
        )
    
    async def _meta_learning(self, request: SubAgentRequest) -> SubAgentResponse:
        """Optimize learning strategies.
        
        Uses nemotron-3-nano for meta-learning optimization.
        
        Args:
            request: Meta-learning request with learning data
            
        Returns:
            Optimized learning strategy
        """
        return SubAgentResponse(
            success=True,
            capability=SubAgentCapability.META_LEARNING,
            result={"recommendation": "Meta-learning not yet implemented"},
            reasoning="Feature under development",
            confidence=0.0
        )
    
    async def _healing(self, request: SubAgentRequest) -> SubAgentResponse:
        """Propose healing for errors.
        
        Uses qwen3-coder-next for fix generation.
        
        Args:
            request: Healing request with 'error' details
            
        Returns:
            Proposed fix
        """
        error = request.context.get("error", "")
        
        return SubAgentResponse(
            success=True,
            capability=SubAgentCapability.HEALING,
            result={
                "fix_proposal": "Healing not yet implemented",
                "error": error,
            },
            reasoning="Feature under development",
            confidence=0.0
        )
    
    async def _visual_monitoring(self, request: SubAgentRequest) -> SubAgentResponse:
        """Analyze logs and screenshots.
        
        Uses qwen3-vl for visual analysis.
        
        Args:
            request: Monitoring request with logs/screenshots
            
        Returns:
            Analysis results
        """
        return SubAgentResponse(
            success=True,
            capability=SubAgentCapability.VISUAL_MONITORING,
            result={"analysis": "Visual monitoring not yet implemented"},
            reasoning="Feature under development",
            confidence=0.0
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get RC2 status.
        
        Returns:
            Detailed status including multi-provider info
        """
        status = super().get_status()
        status.update({
            "multi_provider": self.use_multi_provider,
            "router_available": self.router is not None,
            "model_assignments": self.MODEL_ASSIGNMENTS,
        })
        return status
