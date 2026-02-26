import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class SkillAdapter:
    def __init__(self, system_skills_path: str, custom_skills_path: str):
        self.system_skills_path = Path(system_skills_path)
        self.custom_skills_path = Path(custom_skills_path)
        self.skills: Dict[str, Dict[str, Any]] = {}
        
    def load_skills(self):
        """加载所有技能（System 和 Custom）"""
        self.skills = {}
        
        # 加载 System Skills
        if self.system_skills_path.exists():
            self._load_from_dir(self.system_skills_path, is_builtin=True)
            
        # 加载 Custom Skills
        if self.custom_skills_path.exists():
            self._load_from_dir(self.custom_skills_path, is_builtin=False)
            
        logger.info(f"Loaded {len(self.skills)} skills in total.")
        
    def _load_from_dir(self, directory: Path, is_builtin: bool):
        """从指定目录加载技能"""
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    skill_file = item / "SKILL.md"
                    if skill_file.exists():
                        try:
                            skill_data = self._parse_skill_file(skill_file)
                            skill_id = item.name # 使用目录名作为 ID
                            
                            # 如果 frontmatter 里有 name，优先使用，但在 map 中还是以目录名为 key 避免冲突
                            # 或者统一使用目录名作为唯一标识
                            
                            skill_data.update({
                                "id": skill_id,
                                "is_builtin": is_builtin,
                                "tool_type": "system" if is_builtin else "custom",
                                "path": str(item.absolute())
                            })
                            
                            # 如果已存在（例如 Custom 覆盖 System），则覆盖
                            self.skills[skill_id] = skill_data
                        except Exception as e:
                            logger.error(f"Error loading skill from {item}: {e}")
        except Exception as e:
            logger.error(f"Error accessing directory {directory}: {e}")

    def _parse_skill_file(self, file_path: Path) -> Dict[str, Any]:
        """解析 SKILL.md 文件"""
        content = file_path.read_text(encoding='utf-8')
        
        # 简单的 Frontmatter 解析
        if content.startswith("---"):
            try:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_str = parts[1]
                    body = parts[2]
                    metadata = yaml.safe_load(frontmatter_str) or {}
                    metadata['description'] = metadata.get('description', '').strip()
                    metadata['content'] = body.strip()
                    return metadata
            except Exception as e:
                logger.warning(f"Failed to parse YAML frontmatter in {file_path}: {e}")
        
        # Fallback: 如果没有 Frontmatter，把整个内容当作描述
        return {
            "name": file_path.parent.name,
            "description": content[:200].strip(),
            "content": content
        }

    def list_skills(self) -> List[Dict[str, Any]]:
        """返回技能列表"""
        return list(self.skills.values())

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        return self.skills.get(skill_id)

    def delete_skill(self, skill_id: str) -> bool:
        """删除技能（仅 Custom）"""
        skill = self.skills.get(skill_id)
        if not skill:
            return False
            
        if skill['is_builtin']:
            raise ValueError("Cannot delete builtin skill")
            
        try:
            import shutil
            shutil.rmtree(skill['path'])
            del self.skills[skill_id]
            return True
        except Exception as e:
            logger.error(f"Failed to delete skill directory {skill['path']}: {e}")
            raise e
