"""
Awesome Claude Skills Converter
Converts awesome-claude-skills format to lollmsBot's skill format.
"""

import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from lollmsbot.skills import Skill, SkillParameter, SkillComplexity
from lollmsbot.awesome_skills_manager import SkillInfo

logger = logging.getLogger(__name__)


class AwesomeSkillsConverter:
    """
    Converts awesome-claude-skills to lollmsBot Skill format.
    
    Awesome skills are typically instruction-only skills that provide
    guidance and workflows. We convert them to lollmsBot skills that
    can be executed by the agent system.
    """
    
    def __init__(self):
        """Initialize the converter."""
        self.complexity_mapping = {
            "tier-1-instruction-only": SkillComplexity.SIMPLE,
            "tier-2-tool-enhanced": SkillComplexity.MODERATE,
            "tier-3-claude-only": SkillComplexity.COMPLEX,
        }
    
    def convert_skill(self, skill_info: SkillInfo) -> Optional[Skill]:
        """
        Convert an AwesomeSkill to a lollmsBot Skill.
        
        Args:
            skill_info: Information about the awesome skill
            
        Returns:
            Converted Skill object or None on error
        """
        try:
            # Load skill content
            content = self._load_skill_content(skill_info)
            if not content:
                logger.error(f"Could not load content for skill: {skill_info.name}")
                return None
            
            # Parse skill content
            skill_data = self._parse_skill_content(content)
            
            # Determine complexity from tier
            complexity = self.complexity_mapping.get(
                skill_info.tier,
                SkillComplexity.SIMPLE
            )
            
            # Extract parameters if any
            parameters = self._extract_parameters(content)
            
            # Create the skill
            skill = Skill(
                name=skill_info.name,
                description=skill_data.get("description", skill_info.description),
                instructions=skill_data.get("instructions", content),
                complexity=complexity,
                parameters=parameters,
                tags=self._extract_tags(skill_info),
                examples=skill_data.get("examples", []),
                metadata={
                    "source": "awesome-claude-skills",
                    "category": skill_info.category,
                    "tier": skill_info.tier,
                    "original_path": str(skill_info.path),
                }
            )
            
            logger.info(f"Converted skill: {skill_info.name}")
            return skill
            
        except Exception as e:
            logger.error(f"Error converting skill {skill_info.name}: {e}")
            return None
    
    def _load_skill_content(self, skill_info: SkillInfo) -> Optional[str]:
        """Load the content of the skill file."""
        if not skill_info.skill_md_path or not skill_info.skill_md_path.exists():
            return None
        
        try:
            with open(skill_info.skill_md_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading skill file: {e}")
            return None
    
    def _parse_skill_content(self, content: str) -> Dict[str, Any]:
        """
        Parse skill content and extract structured information.
        
        Args:
            content: Raw skill content
            
        Returns:
            Dictionary with parsed data
        """
        data = {
            "description": "",
            "instructions": content,
            "examples": []
        }
        
        # Extract description (usually the first paragraph)
        lines = content.split('\n')
        description_lines = []
        in_description = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip title
            if stripped.startswith('#'):
                continue
            
            # Start collecting description
            if stripped and not in_description:
                in_description = True
                description_lines.append(stripped)
            elif in_description and stripped:
                description_lines.append(stripped)
            elif in_description and not stripped:
                # Empty line ends description
                break
        
        if description_lines:
            data["description"] = ' '.join(description_lines)
        
        # Extract examples
        example_pattern = re.compile(r'```(.*?)```', re.DOTALL)
        examples = example_pattern.findall(content)
        data["examples"] = [ex.strip() for ex in examples if ex.strip()]
        
        return data
    
    def _extract_parameters(self, content: str) -> List[SkillParameter]:
        """
        Extract parameters from skill content.
        
        Looks for patterns like:
        - Input: [parameter name]
        - Parameter: [parameter name]
        - Required: [parameter name]
        
        Args:
            content: Skill content
            
        Returns:
            List of SkillParameter objects
        """
        parameters = []
        
        # Common parameter patterns
        patterns = [
            r'(?:Input|Parameter|Required):\s*\*\*([^*]+)\*\*',  # **param**
            r'(?:Input|Parameter|Required):\s*`([^`]+)`',  # `param`
            r'(?:Input|Parameter|Required):\s*([A-Za-z_][A-Za-z0-9_]*)',  # plain text
        ]
        
        seen = set()
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                param_name = match.strip().lower().replace(' ', '_')
                if param_name and param_name not in seen:
                    parameters.append(
                        SkillParameter(
                            name=param_name,
                            description=f"Parameter extracted from skill: {match}",
                            required=True,
                            type="string"
                        )
                    )
                    seen.add(param_name)
        
        return parameters
    
    def _extract_tags(self, skill_info: SkillInfo) -> List[str]:
        """
        Extract tags from skill information.
        
        Args:
            skill_info: Skill information
            
        Returns:
            List of tags
        """
        tags = [
            "awesome-skills",
            skill_info.category.lower().replace(' ', '-'),
        ]
        
        # Add tier tag
        if skill_info.tier:
            tags.append(skill_info.tier)
        
        # Add tags from name (split on hyphen)
        name_parts = skill_info.name.split('-')
        tags.extend(name_parts)
        
        # Remove duplicates and return
        return list(set(tags))
    
    def batch_convert(self, skill_infos: List[SkillInfo]) -> List[Skill]:
        """
        Convert multiple skills at once.
        
        Args:
            skill_infos: List of skill information
            
        Returns:
            List of converted Skill objects
        """
        skills = []
        
        for skill_info in skill_infos:
            skill = self.convert_skill(skill_info)
            if skill:
                skills.append(skill)
        
        logger.info(f"Converted {len(skills)} out of {len(skill_infos)} skills")
        return skills
