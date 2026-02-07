"""
Phase 3C: Knowledge Graph Integration

This module builds and manages a knowledge graph from hobby insights,
enabling semantic connections and graph-based reasoning.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Knowledge graph node types"""
    CONCEPT = "concept"
    INSIGHT = "insight"
    PATTERN = "pattern"
    SKILL = "skill"
    TOOL = "tool"
    TECHNIQUE = "technique"


class RelationType(str, Enum):
    """Knowledge graph relationship types"""
    RELATES_TO = "relates_to"
    DERIVED_FROM = "derived_from"
    ENABLES = "enables"
    REQUIRES = "requires"
    SIMILAR_TO = "similar_to"
    PART_OF = "part_of"
    IMPROVES = "improves"


@dataclass
class KnowledgeNode:
    """Node in the knowledge graph"""
    node_id: str
    node_type: NodeType
    label: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class KnowledgeEdge:
    """Edge (relationship) in the knowledge graph"""
    edge_id: str
    relation_type: RelationType
    source_id: str
    target_id: str
    weight: float
    metadata: Dict[str, Any]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "relation_type": self.relation_type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "weight": self.weight,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


class KnowledgeGraph:
    """In-memory knowledge graph with persistence"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize knowledge graph
        
        Args:
            storage_path: Path for persistent storage
        """
        self.storage_path = storage_path or Path.home() / ".lollmsbot" / "knowledge"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        
        # Index for fast lookups
        self._node_by_label: Dict[str, Set[str]] = {}
        self._edges_from: Dict[str, Set[str]] = {}  # source -> edge_ids
        self._edges_to: Dict[str, Set[str]] = {}    # target -> edge_ids
        
        self._node_counter = 0
        self._edge_counter = 0
        self._lock = threading.Lock()
        
        self._load_state()
        
        logger.info(f"Knowledge Graph initialized with {len(self.nodes)} nodes, {len(self.edges)} edges")
    
    def add_node(
        self,
        label: str,
        content: str,
        node_type: NodeType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeNode:
        """
        Add a node to the graph
        
        Args:
            label: Node label/name
            content: Node content/description
            node_type: Type of node
            metadata: Additional metadata
            
        Returns:
            Created KnowledgeNode
        """
        with self._lock:
            self._node_counter += 1
            node_id = f"node_{self._node_counter}_{int(datetime.now().timestamp())}"
        
        now = datetime.now().isoformat()
        node = KnowledgeNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            content=content,
            metadata=metadata or {},
            created_at=now,
            updated_at=now
        )
        
        self.nodes[node_id] = node
        
        # Update index
        if label not in self._node_by_label:
            self._node_by_label[label] = set()
        self._node_by_label[label].add(node_id)
        
        self._save_state()
        
        logger.debug(f"Added node {node_id}: {label}")
        return node
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeEdge:
        """
        Add an edge to the graph
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relation_type: Type of relationship
            weight: Edge weight (0.0-1.0)
            metadata: Additional metadata
            
        Returns:
            Created KnowledgeEdge
        """
        if source_id not in self.nodes:
            raise ValueError(f"Source node {source_id} not found")
        if target_id not in self.nodes:
            raise ValueError(f"Target node {target_id} not found")
        
        with self._lock:
            self._edge_counter += 1
            edge_id = f"edge_{self._edge_counter}_{int(datetime.now().timestamp())}"
        
        edge = KnowledgeEdge(
            edge_id=edge_id,
            relation_type=relation_type,
            source_id=source_id,
            target_id=target_id,
            weight=weight,
            metadata=metadata or {},
            created_at=datetime.now().isoformat()
        )
        
        self.edges[edge_id] = edge
        
        # Update indexes
        if source_id not in self._edges_from:
            self._edges_from[source_id] = set()
        self._edges_from[source_id].add(edge_id)
        
        if target_id not in self._edges_to:
            self._edges_to[target_id] = set()
        self._edges_to[target_id].add(edge_id)
        
        self._save_state()
        
        logger.debug(f"Added edge {edge_id}: {source_id} -> {target_id} ({relation_type})")
        return edge
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)
    
    def find_nodes_by_label(self, label: str) -> List[KnowledgeNode]:
        """Find nodes by exact label match"""
        node_ids = self._node_by_label.get(label, set())
        return [self.nodes[nid] for nid in node_ids]
    
    def search_nodes(
        self,
        query: str,
        node_type: Optional[NodeType] = None,
        limit: int = 50
    ) -> List[KnowledgeNode]:
        """
        Search nodes by query string
        
        Args:
            query: Search query
            node_type: Filter by node type
            limit: Maximum results
            
        Returns:
            List of matching nodes
        """
        query_lower = query.lower()
        matches = []
        
        for node in self.nodes.values():
            if node_type and node.node_type != node_type:
                continue
            
            # Simple text matching
            if (query_lower in node.label.lower() or
                query_lower in node.content.lower()):
                matches.append(node)
            
            if len(matches) >= limit:
                break
        
        return matches
    
    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        relation_type: Optional[RelationType] = None
    ) -> List[Tuple[KnowledgeNode, KnowledgeEdge]]:
        """
        Get neighboring nodes
        
        Args:
            node_id: Node ID
            direction: "outgoing", "incoming", or "both"
            relation_type: Filter by relation type
            
        Returns:
            List of (neighbor_node, edge) tuples
        """
        neighbors = []
        
        # Outgoing edges
        if direction in ["outgoing", "both"]:
            edge_ids = self._edges_from.get(node_id, set())
            for edge_id in edge_ids:
                edge = self.edges[edge_id]
                if relation_type and edge.relation_type != relation_type:
                    continue
                target = self.nodes.get(edge.target_id)
                if target:
                    neighbors.append((target, edge))
        
        # Incoming edges
        if direction in ["incoming", "both"]:
            edge_ids = self._edges_to.get(node_id, set())
            for edge_id in edge_ids:
                edge = self.edges[edge_id]
                if relation_type and edge.relation_type != relation_type:
                    continue
                source = self.nodes.get(edge.source_id)
                if source:
                    neighbors.append((source, edge))
        
        return neighbors
    
    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """
        Find shortest path between two nodes (BFS)
        
        Args:
            start_id: Start node ID
            end_id: End node ID
            max_depth: Maximum path length
            
        Returns:
            List of node IDs forming the path, or None if no path found
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None
        
        if start_id == end_id:
            return [start_id]
        
        # BFS
        queue = [(start_id, [start_id])]
        visited = {start_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            # Get neighbors
            neighbors = self.get_neighbors(current_id, direction="outgoing")
            
            for neighbor, _ in neighbors:
                if neighbor.node_id in visited:
                    continue
                
                new_path = path + [neighbor.node_id]
                
                if neighbor.node_id == end_id:
                    return new_path
                
                visited.add(neighbor.node_id)
                queue.append((neighbor.node_id, new_path))
        
        return None
    
    def get_subgraph(
        self,
        node_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph centered on a node
        
        Args:
            node_id: Center node ID
            depth: Depth of subgraph
            
        Returns:
            Subgraph data with nodes and edges
        """
        if node_id not in self.nodes:
            return {"nodes": [], "edges": []}
        
        included_nodes = set()
        included_edges = set()
        
        # BFS to collect nodes
        queue = [(node_id, 0)]
        included_nodes.add(node_id)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            neighbors = self.get_neighbors(current_id)
            
            for neighbor, edge in neighbors:
                included_edges.add(edge.edge_id)
                
                if neighbor.node_id not in included_nodes:
                    included_nodes.add(neighbor.node_id)
                    queue.append((neighbor.node_id, current_depth + 1))
        
        return {
            "nodes": [self.nodes[nid].to_dict() for nid in included_nodes],
            "edges": [self.edges[eid].to_dict() for eid in included_edges]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        node_types = {}
        relation_types = {}
        
        for node in self.nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        
        for edge in self.edges.values():
            relation_types[edge.relation_type] = relation_types.get(edge.relation_type, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "relation_types": relation_types,
            "average_degree": (2 * len(self.edges)) / max(len(self.nodes), 1)
        }
    
    def _save_state(self) -> None:
        """Save graph to disk"""
        graph_file = self.storage_path / "knowledge_graph.json"
        
        state = {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": {k: v.to_dict() for k, v in self.edges.items()},
            "counters": {
                "node": self._node_counter,
                "edge": self._edge_counter
            }
        }
        
        try:
            with open(graph_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save knowledge graph: {e}")
    
    def _load_state(self) -> None:
        """Load graph from disk"""
        graph_file = self.storage_path / "knowledge_graph.json"
        
        if not graph_file.exists():
            return
        
        try:
            with open(graph_file, 'r') as f:
                state = json.load(f)
            
            # Load nodes
            for node_data in state.get("nodes", {}).values():
                node = KnowledgeNode(
                    node_id=node_data["node_id"],
                    node_type=NodeType(node_data["node_type"]),
                    label=node_data["label"],
                    content=node_data["content"],
                    metadata=node_data["metadata"],
                    created_at=node_data["created_at"],
                    updated_at=node_data["updated_at"]
                )
                self.nodes[node.node_id] = node
                
                # Update index
                if node.label not in self._node_by_label:
                    self._node_by_label[node.label] = set()
                self._node_by_label[node.label].add(node.node_id)
            
            # Load edges
            for edge_data in state.get("edges", {}).values():
                edge = KnowledgeEdge(
                    edge_id=edge_data["edge_id"],
                    relation_type=RelationType(edge_data["relation_type"]),
                    source_id=edge_data["source_id"],
                    target_id=edge_data["target_id"],
                    weight=edge_data["weight"],
                    metadata=edge_data["metadata"],
                    created_at=edge_data["created_at"]
                )
                self.edges[edge.edge_id] = edge
                
                # Update indexes
                if edge.source_id not in self._edges_from:
                    self._edges_from[edge.source_id] = set()
                self._edges_from[edge.source_id].add(edge.edge_id)
                
                if edge.target_id not in self._edges_to:
                    self._edges_to[edge.target_id] = set()
                self._edges_to[edge.target_id].add(edge.edge_id)
            
            # Load counters
            counters = state.get("counters", {})
            self._node_counter = counters.get("node", 0)
            self._edge_counter = counters.get("edge", 0)
            
            logger.info(f"Loaded knowledge graph: {len(self.nodes)} nodes, {len(self.edges)} edges")
            
        except Exception as e:
            logger.warning(f"Failed to load knowledge graph: {e}")


def build_graph_from_activities(
    graph: KnowledgeGraph,
    activities: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build knowledge graph from hobby activities
    
    Args:
        graph: KnowledgeGraph instance
        activities: List of hobby activity dictionaries
        
    Returns:
        Statistics about graph construction
    """
    nodes_added = 0
    edges_added = 0
    
    for activity in activities:
        hobby_type = activity.get("hobby_type", "UNKNOWN")
        insights = activity.get("insights_gained", [])
        patterns = activity.get("patterns_discovered", [])
        skills = activity.get("skills_improved", [])
        
        # Add nodes for insights
        for insight in insights:
            node = graph.add_node(
                label=f"Insight: {insight[:50]}...",
                content=insight,
                node_type=NodeType.INSIGHT,
                metadata={
                    "hobby_type": hobby_type,
                    "activity_id": activity.get("activity_id"),
                    "timestamp": activity.get("started_at")
                }
            )
            nodes_added += 1
        
        # Add nodes for patterns
        for pattern in patterns:
            node = graph.add_node(
                label=f"Pattern: {pattern[:50]}...",
                content=pattern,
                node_type=NodeType.PATTERN,
                metadata={
                    "hobby_type": hobby_type,
                    "activity_id": activity.get("activity_id"),
                    "timestamp": activity.get("started_at")
                }
            )
            nodes_added += 1
        
        # Add nodes for skills
        for skill in skills:
            # Check if skill node already exists
            existing = graph.find_nodes_by_label(skill)
            if not existing:
                node = graph.add_node(
                    label=skill,
                    content=f"Skill: {skill}",
                    node_type=NodeType.SKILL,
                    metadata={"hobby_type": hobby_type}
                )
                nodes_added += 1
    
    logger.info(f"Built graph from {len(activities)} activities: {nodes_added} nodes, {edges_added} edges")
    
    return {
        "nodes_added": nodes_added,
        "edges_added": edges_added,
        "activities_processed": len(activities)
    }


# Global instance
_knowledge_graph: Optional[KnowledgeGraph] = None
_graph_lock = threading.Lock()


def get_knowledge_graph(storage_path: Optional[Path] = None) -> KnowledgeGraph:
    """
    Get or create global knowledge graph
    
    Args:
        storage_path: Optional storage path
        
    Returns:
        KnowledgeGraph instance
    """
    global _knowledge_graph
    
    if _knowledge_graph is not None:
        return _knowledge_graph
    
    with _graph_lock:
        if _knowledge_graph is None:
            _knowledge_graph = KnowledgeGraph(storage_path)
        return _knowledge_graph
