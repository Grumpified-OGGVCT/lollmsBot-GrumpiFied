"""
Awesome Claude Skills Manager
Handles cloning, updating, and maintaining the awesome-claude-skills repository.
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import shutil

logger = logging.getLogger(__name__)


@dataclass
class SkillInfo:
    """Information about a skill from awesome-claude-skills repository."""
    name: str
    path: Path
    category: str
    description: str
    tier: str  # tier-1, tier-2, or tier-3
    skill_md_path: Optional[Path] = None
    metadata: Optional[Dict[str, Any]] = None


class AwesomeSkillsManager:
    """
    Manages the awesome-claude-skills repository integration.
    
    Responsibilities:
    - Clone and update the awesome-claude-skills repository
    - Discover available skills
    - Load skill definitions
    - Convert skills to lollmsBot format
    """
    
    DEFAULT_REPO_URL = "https://github.com/Grumpified-OGGVCT/awesome-claude-skills.git"
    
    def __init__(
        self,
        skills_dir: Optional[Path] = None,
        repo_url: Optional[str] = None,
        auto_update: bool = True
    ):
        """
        Initialize the Awesome Skills Manager.
        
        Args:
            skills_dir: Directory to store the cloned repo (default: ~/.lollmsbot/awesome-skills)
            repo_url: URL of the awesome-claude-skills repository
            auto_update: Whether to automatically update the repository on init
        """
        self.repo_url = repo_url or self.DEFAULT_REPO_URL
        self.skills_dir = skills_dir or self._get_default_skills_dir()
        self.repo_path = self.skills_dir / "awesome-claude-skills"
        self.skills_index: Optional[Dict[str, SkillInfo]] = None
        
        # Ensure skills directory exists
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize repository
        if auto_update:
            self.ensure_repository()
    
    def _get_default_skills_dir(self) -> Path:
        """Get the default directory for storing awesome skills."""
        home = Path.home()
        return home / ".lollmsbot" / "awesome-skills"
    
    def ensure_repository(self) -> bool:
        """
        Ensure the awesome-claude-skills repository is cloned and up-to-date.
        
        Returns:
            True if repository is ready, False on error
        """
        try:
            if not self.is_cloned():
                logger.info(f"Cloning awesome-claude-skills from {self.repo_url}")
                return self.clone_repository()
            else:
                logger.info("Awesome-claude-skills repository already exists")
                return self.update_repository()
        except Exception as e:
            logger.error(f"Error ensuring repository: {e}")
            return False
    
    def is_cloned(self) -> bool:
        """Check if the repository is already cloned."""
        return (self.repo_path / ".git").exists()
    
    def clone_repository(self) -> bool:
        """
        Clone the awesome-claude-skills repository.
        
        Returns:
            True on success, False on error
        """
        try:
            # Remove existing directory if it's not a git repo
            if self.repo_path.exists() and not self.is_cloned():
                logger.warning(f"Removing invalid repository at {self.repo_path}")
                shutil.rmtree(self.repo_path)
            
            # Clone the repository
            result = subprocess.run(
                ["git", "clone", self.repo_url, str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully cloned repository to {self.repo_path}")
                return True
            else:
                logger.error(f"Failed to clone repository: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Repository clone timed out")
            return False
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return False
    
    def update_repository(self) -> bool:
        """
        Update the cloned repository with latest changes.
        
        Returns:
            True on success, False on error
        """
        if not self.is_cloned():
            logger.warning("Repository not cloned, cloning now")
            return self.clone_repository()
        
        try:
            # Fetch latest changes
            result = subprocess.run(
                ["git", "fetch", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to fetch updates: {result.stderr}")
                return False
            
            # Check if we're behind
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/master"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            commits_behind = int(result.stdout.strip() or "0")
            
            if commits_behind > 0:
                logger.info(f"Repository is {commits_behind} commits behind, pulling updates")
                
                # Pull latest changes
                result = subprocess.run(
                    ["git", "pull", "origin", "master"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    logger.info("Successfully updated repository")
                    return True
                else:
                    logger.error(f"Failed to pull updates: {result.stderr}")
                    return False
            else:
                logger.info("Repository is up-to-date")
                return True
                
        except subprocess.TimeoutExpired:
            logger.error("Repository update timed out")
            return False
        except Exception as e:
            logger.error(f"Error updating repository: {e}")
            return False
    
    def load_skills_index(self) -> Dict[str, SkillInfo]:
        """
        Load the skills index from the repository.
        
        Returns:
            Dictionary of skill name to SkillInfo
        """
        if self.skills_index is not None:
            return self.skills_index
        
        index_path = self.repo_path / "SKILL-INDEX.json"
        
        if not index_path.exists():
            logger.warning("SKILL-INDEX.json not found, scanning repository")
            return self._scan_repository()
        
        try:
            with open(index_path, 'r') as f:
                index_data = json.load(f)
            
            skills = {}
            skills_list = index_data.get("skills", [])
            
            # Handle both list and dict formats
            if isinstance(skills_list, list):
                for skill_data in skills_list:
                    skill_name = skill_data.get("name")
                    if not skill_name:
                        continue
                    
                    # Determine skill path
                    skill_path = self.repo_path / skill_data.get("path", skill_name)
                    
                    # Find SKILL.md file
                    skill_md = skill_path / "SKILL.md"
                    if not skill_md.exists():
                        # Try in universal format
                        for tier in ["tier-1-instruction-only", "tier-2-tool-enhanced", "tier-3-claude-only"]:
                            universal_path = self.repo_path / "universal" / tier / skill_name
                            if (universal_path / "system-prompt.md").exists():
                                skill_path = universal_path
                                skill_md = universal_path / "system-prompt.md"
                                break
                    
                    skills[skill_name] = SkillInfo(
                        name=skill_name,
                        path=skill_path,
                        category=skill_data.get("category", "Uncategorized"),
                        description=skill_data.get("description", ""),
                        tier=skill_data.get("tier", "tier-1"),
                        skill_md_path=skill_md if skill_md.exists() else None,
                        metadata=skill_data
                    )
            elif isinstance(skills_list, dict):
                # Old format: dict of skill_name -> skill_data
                for skill_name, skill_data in skills_list.items():
                    # Determine skill path
                    skill_path = self.repo_path / skill_data.get("path", skill_name)
                    
                    # Find SKILL.md file
                    skill_md = skill_path / "SKILL.md"
                    if not skill_md.exists():
                        # Try in universal format
                        for tier in ["tier-1-instruction-only", "tier-2-tool-enhanced", "tier-3-claude-only"]:
                            universal_path = self.repo_path / "universal" / tier / skill_name
                            if (universal_path / "system-prompt.md").exists():
                                skill_path = universal_path
                                skill_md = universal_path / "system-prompt.md"
                                break
                    
                    skills[skill_name] = SkillInfo(
                        name=skill_name,
                        path=skill_path,
                        category=skill_data.get("category", "Uncategorized"),
                        description=skill_data.get("description", ""),
                        tier=skill_data.get("tier", "tier-1"),
                        skill_md_path=skill_md if skill_md.exists() else None,
                        metadata=skill_data
                    )
            
            self.skills_index = skills
            logger.info(f"Loaded {len(skills)} skills from index")
            return skills
            
        except Exception as e:
            logger.error(f"Error loading skills index: {e}")
            return self._scan_repository()
    
    def _scan_repository(self) -> Dict[str, SkillInfo]:
        """
        Scan the repository for SKILL.md files and build index.
        
        Returns:
            Dictionary of skill name to SkillInfo
        """
        skills = {}
        
        try:
            # Find all SKILL.md files
            for skill_md in self.repo_path.rglob("SKILL.md"):
                if ".git" in str(skill_md):
                    continue
                
                skill_path = skill_md.parent
                skill_name = skill_path.name
                
                # Skip if in examples or templates
                if "example" in str(skill_path).lower() or "template" in str(skill_path).lower():
                    continue
                
                # Try to extract description from first line
                description = ""
                try:
                    with open(skill_md, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines[:10]:  # Check first 10 lines
                            if line.strip() and not line.startswith('#'):
                                description = line.strip()
                                break
                except Exception as e:
                    logger.debug(f"Could not read description from {skill_md}: {e}")
                
                skills[skill_name] = SkillInfo(
                    name=skill_name,
                    path=skill_path,
                    category="Uncategorized",
                    description=description,
                    tier="tier-1",
                    skill_md_path=skill_md
                )
            
            # Also scan universal format
            universal_dir = self.repo_path / "universal"
            if universal_dir.exists():
                for tier_dir in universal_dir.iterdir():
                    if not tier_dir.is_dir():
                        continue
                    
                    tier = tier_dir.name
                    for skill_dir in tier_dir.iterdir():
                        if not skill_dir.is_dir():
                            continue
                        
                        skill_name = skill_dir.name
                        system_prompt = skill_dir / "system-prompt.md"
                        
                        if system_prompt.exists():
                            # Only add if not already found
                            if skill_name not in skills:
                                description = ""
                                try:
                                    with open(system_prompt, 'r', encoding='utf-8') as f:
                                        lines = f.readlines()
                                        for line in lines[:10]:
                                            if line.strip() and not line.startswith('#'):
                                                description = line.strip()
                                                break
                                except Exception:
                                    pass
                                
                                skills[skill_name] = SkillInfo(
                                    name=skill_name,
                                    path=skill_dir,
                                    category="Uncategorized",
                                    description=description,
                                    tier=tier,
                                    skill_md_path=system_prompt
                                )
            
            self.skills_index = skills
            logger.info(f"Scanned repository and found {len(skills)} skills")
            return skills
            
        except Exception as e:
            logger.error(f"Error scanning repository: {e}")
            return {}
    
    def get_skill(self, skill_name: str) -> Optional[SkillInfo]:
        """
        Get information about a specific skill.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            SkillInfo object or None if not found
        """
        skills = self.load_skills_index()
        return skills.get(skill_name)
    
    def list_skills(self, category: Optional[str] = None) -> List[SkillInfo]:
        """
        List all available skills, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of SkillInfo objects
        """
        skills = self.load_skills_index()
        skill_list = list(skills.values())
        
        if category:
            skill_list = [s for s in skill_list if s.category == category]
        
        return sorted(skill_list, key=lambda s: s.name)
    
    def get_categories(self) -> List[str]:
        """
        Get all available skill categories.
        
        Returns:
            List of category names
        """
        skills = self.load_skills_index()
        categories = set(s.category for s in skills.values())
        return sorted(categories)
    
    def search_skills(self, query: str) -> List[SkillInfo]:
        """
        Search for skills matching a query.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching SkillInfo objects
        """
        skills = self.load_skills_index()
        query_lower = query.lower()
        
        results = []
        for skill in skills.values():
            # Search in name, description, and category
            if (query_lower in skill.name.lower() or
                query_lower in skill.description.lower() or
                query_lower in skill.category.lower()):
                results.append(skill)
        
        return sorted(results, key=lambda s: s.name)
    
    def load_skill_content(self, skill_name: str) -> Optional[str]:
        """
        Load the content of a skill's SKILL.md or system-prompt.md file.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Content of the skill file or None if not found
        """
        skill = self.get_skill(skill_name)
        if not skill or not skill.skill_md_path:
            logger.error(f"Skill not found or has no content file: {skill_name}")
            return None
        
        try:
            with open(skill.skill_md_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading skill content: {e}")
            return None
    
    def get_repository_info(self) -> Dict[str, Any]:
        """
        Get information about the repository state.
        
        Returns:
            Dictionary with repository information
        """
        info = {
            "cloned": self.is_cloned(),
            "path": str(self.repo_path),
            "url": self.repo_url,
            "skills_count": 0
        }
        
        if self.is_cloned():
            try:
                # Get current commit
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                info["commit"] = result.stdout.strip()
                
                # Get commit date
                result = subprocess.run(
                    ["git", "log", "-1", "--format=%cd"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                info["last_updated"] = result.stdout.strip()
                
                # Count skills
                skills = self.load_skills_index()
                info["skills_count"] = len(skills)
                
            except Exception as e:
                logger.error(f"Error getting repository info: {e}")
        
        return info
