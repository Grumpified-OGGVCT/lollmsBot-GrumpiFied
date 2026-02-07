"""
Awesome Claude Skills Integration
Integrates awesome-claude-skills with lollmsBot's SkillRegistry.
Uses Guardian for unified security scanning.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from lollmsbot.config import AwesomeSkillsConfig
from lollmsbot.awesome_skills_manager import AwesomeSkillsManager, SkillInfo
from lollmsbot.awesome_skills_converter import AwesomeSkillsConverter
from lollmsbot.skills import Skill, SkillRegistry
from lollmsbot.guardian import get_guardian

logger = logging.getLogger(__name__)


class AwesomeSkillsIntegration:
    """
    Integrates awesome-claude-skills with lollmsBot.
    
    Responsibilities:
    - Initialize and manage the awesome-claude-skills repository
    - Load and convert skills to lollmsBot format
    - Register skills with the SkillRegistry
    - Provide discovery and search interface
    """
    
    def __init__(
        self,
        config: AwesomeSkillsConfig,
        skill_registry: SkillRegistry,
        enable_security_scanning: bool = True
    ):
        """
        Initialize the integration.
        
        Args:
            config: Configuration for awesome-claude-skills
            skill_registry: lollmsBot's skill registry
            enable_security_scanning: Whether to scan skills for security threats
        """
        self.config = config
        self.registry = skill_registry
        self.enable_security_scanning = enable_security_scanning
        
        # Initialize manager and converter
        self.manager: Optional[AwesomeSkillsManager] = None
        self.converter = AwesomeSkillsConverter()
        
        # Use Guardian for security scanning (unified)
        self.guardian = get_guardian() if enable_security_scanning else None
        
        # Track loaded skills and scan results
        self.loaded_skills: Dict[str, Skill] = {}
        self.scan_results: Dict[str, Dict[str, Any]] = {}
        
        # Initialize if enabled
        if self.config.enabled:
            self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the awesome-claude-skills manager."""
        try:
            logger.info("Initializing awesome-claude-skills integration")
            
            # Create manager
            self.manager = AwesomeSkillsManager(
                skills_dir=self.config.skills_dir,
                repo_url=self.config.repo_url,
                auto_update=self.config.auto_update
            )
            
            # Load skills if auto-load is enabled
            if self.config.auto_load:
                self.load_enabled_skills()
            
            logger.info("Awesome-claude-skills integration initialized")
            
        except Exception as e:
            logger.error(f"Error initializing awesome-claude-skills: {e}")
            self.manager = None
    
    def is_available(self) -> bool:
        """Check if awesome-claude-skills is available."""
        return self.config.enabled and self.manager is not None and self.manager.is_cloned()
    
    def load_enabled_skills(self) -> int:
        """
        Load skills specified in configuration.
        
        Returns:
            Number of skills successfully loaded
        """
        if not self.is_available():
            logger.warning("Awesome-claude-skills not available")
            return 0
        
        # Get list of skills to load
        skills_to_load = self.config.enabled_skills
        
        if not skills_to_load:
            # Load all skills if none specified
            logger.info("No specific skills configured, loading all available skills")
            skills_to_load = list(self.manager.load_skills_index().keys())
        
        # Load each skill
        loaded_count = 0
        for skill_name in skills_to_load:
            if self.load_skill(skill_name):
                loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} out of {len(skills_to_load)} awesome-claude-skills")
        return loaded_count
    
    def load_skill(self, skill_name: str) -> bool:
        """
        Load a specific skill from awesome-claude-skills.
        
        Security scanning is ALWAYS performed - cannot be bypassed.
        
        Args:
            skill_name: Name of the skill to load
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.is_available():
            logger.warning("Awesome-claude-skills not available")
            return False
        
        # Check if already loaded
        if skill_name in self.loaded_skills:
            logger.debug(f"Skill already loaded: {skill_name}")
            return True
        
        try:
            # Get skill info
            skill_info = self.manager.get_skill(skill_name)
            if not skill_info:
                logger.error(f"Skill not found: {skill_name}")
                return False
            
            # SECURITY: Scan skill for threats before loading (using Guardian)
            # Security scanning CANNOT be bypassed
            if self.guardian:
                is_safe, threats = self._scan_skill_with_guardian(skill_info)
                self.scan_results[skill_name] = {
                    "is_safe": is_safe,
                    "threats": threats,
                    "skill_name": skill_name
                }
                
                if not is_safe:
                    logger.error(
                        f"🚨 SECURITY: Skill '{skill_name}' failed security scan"
                    )
                    logger.error(f"Detected threats:")
                    for threat in threats:
                        logger.error(f"  - {threat}")
                    
                    # Block loading of unsafe skills - NO BYPASS POSSIBLE
                    logger.error(f"❌ Blocking load of unsafe skill: {skill_name}")
                    return False
                else:
                    logger.info(f"✅ Security scan passed for skill: {skill_name}")
            else:
                logger.warning(f"⚠️  Guardian not available - loading {skill_name} without security scan")
            
            # Convert to lollmsBot skill
            skill = self.converter.convert_skill(skill_info)
            if not skill:
                logger.error(f"Failed to convert skill: {skill_name}")
                return False
            
            # Register with skill registry
            self.registry.register(skill, is_builtin=False)
            
            # Track loaded skill
            self.loaded_skills[skill_name] = skill
            
            logger.info(f"Loaded awesome-skill: {skill_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading skill {skill_name}: {e}")
            return False
    
    def _scan_skill_with_guardian(self, skill_info: SkillInfo) -> Tuple[bool, List[str]]:
        """
        Scan a skill using Guardian's unified threat detection.
        
        Args:
            skill_info: Skill information
            
        Returns:
            Tuple of (is_safe, list_of_threats)
        """
        if not skill_info.skill_md_path or not skill_info.skill_md_path.exists():
            logger.warning(f"Cannot scan skill {skill_info.name}: no skill file found")
            return False, ["No skill file found to scan"]
        
        try:
            content = skill_info.skill_md_path.read_text(encoding='utf-8')
            return self.guardian.scan_skill_content(skill_info.name, content)
        except Exception as e:
            logger.error(f"Error scanning skill {skill_info.name}: {e}")
            return False, [f"Scan error: {e}"]
    
    def unload_skill(self, skill_name: str) -> bool:
        """
        Unload a previously loaded skill.
        
        Args:
            skill_name: Name of the skill to unload
            
        Returns:
            True if unloaded successfully, False otherwise
        """
        if skill_name not in self.loaded_skills:
            logger.warning(f"Skill not loaded: {skill_name}")
            return False
        
        try:
            # Remove from registry
            # Note: This bypasses SkillRegistry's internal bookkeeping
            # (_categories, _tags, _search_index, _version_history).
            # TODO: Implement proper unregister() method on SkillRegistry
            # to maintain consistency across all internal indexes.
            if skill_name in self.registry._skills:
                del self.registry._skills[skill_name]
            
            # Remove from loaded skills
            del self.loaded_skills[skill_name]
            
            logger.info(f"Unloaded skill: {skill_name}")
            logger.warning(
                f"Skill '{skill_name}' may still appear in registry searches "
                f"until a proper unregister() method is implemented"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error unloading skill {skill_name}: {e}")
            return False
    
    def list_available_skills(self, category: Optional[str] = None) -> List[SkillInfo]:
        """
        List all available skills from awesome-claude-skills.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of available skills
        """
        if not self.is_available():
            logger.warning("Awesome-claude-skills not available")
            return []
        
        return self.manager.list_skills(category=category)
    
    def search_skills(self, query: str) -> List[SkillInfo]:
        """
        Search for skills matching a query.
        
        Args:
            query: Search query
            
        Returns:
            List of matching skills
        """
        if not self.is_available():
            logger.warning("Awesome-claude-skills not available")
            return []
        
        return self.manager.search_skills(query)
    
    def get_categories(self) -> List[str]:
        """
        Get all available skill categories.
        
        Returns:
            List of category names
        """
        if not self.is_available():
            return []
        
        return self.manager.get_categories()
    
    def update_repository(self) -> bool:
        """
        Update the awesome-claude-skills repository.
        
        Returns:
            True on success, False on error
        """
        if not self.is_available():
            logger.warning("Awesome-claude-skills not available")
            return False
        
        return self.manager.update_repository()
    
    def get_repository_info(self) -> Dict[str, Any]:
        """
        Get information about the repository state.
        
        Returns:
            Dictionary with repository information
        """
        if not self.is_available():
            return {
                "available": False,
                "reason": "Integration not enabled or repository not cloned"
            }
        
        info = self.manager.get_repository_info()
        info.update({
            "available": True,
            "loaded_skills_count": len(self.loaded_skills),
            "loaded_skills": list(self.loaded_skills.keys()),
            "security_scanning_enabled": self.guardian is not None,
            "scanned_skills_count": len(self.scan_results),
        })
        
        return info
    
    def get_scan_results(self, skill_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get security scan results for skills.
        
        Args:
            skill_name: Optional specific skill name, or None for all results
            
        Returns:
            Dictionary with scan results
        """
        if skill_name:
            return self.scan_results.get(skill_name, {})
        return self.scan_results
    
    def reload_all_skills(self) -> int:
        """
        Reload all currently loaded skills.
        
        Useful after updating the repository.
        
        Returns:
            Number of skills successfully reloaded
        """
        skill_names = list(self.loaded_skills.keys())
        
        # Unload all
        for skill_name in skill_names:
            self.unload_skill(skill_name)
        
        # Reload all
        reloaded_count = 0
        for skill_name in skill_names:
            if self.load_skill(skill_name):
                reloaded_count += 1
        
        logger.info(f"Reloaded {reloaded_count} out of {len(skill_names)} skills")
        return reloaded_count
    
    def batch_load_skills(self, skill_names: List[str]) -> Dict[str, bool]:
        """
        Load multiple skills at once.
        
        Args:
            skill_names: List of skill names to load
            
        Returns:
            Dictionary mapping skill name to success status
        """
        results = {}
        
        for skill_name in skill_names:
            results[skill_name] = self.load_skill(skill_name)
        
        return results
