"""
Knowledge Graph

This module implements a knowledge graph connecting concepts across repositories,
enabling multi-repository knowledge transfer and pattern discovery.
"""
import os
import json
import logging
import time
import uuid
import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from enum import Enum

class NodeType(Enum):
    """Types of nodes in the knowledge graph."""
    CONCEPT = "concept"
    CODE_ENTITY = "code_entity"
    PATTERN = "pattern"
    REPOSITORY = "repository"
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    AUTHOR = "author"
    COMMIT = "commit"
    ISSUE = "issue"
    DEPENDENCY = "dependency"


class EdgeType(Enum):
    """Types of edges in the knowledge graph."""
    IS_A = "is_a"
    PART_OF = "part_of"
    IMPLEMENTS = "implements"
    DEPENDS_ON = "depends_on"
    CALLS = "calls"
    EXTENDS = "extends"
    AUTHORED_BY = "authored_by"
    CONTAINS = "contains"
    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    EVOLVED_FROM = "evolved_from"
    DOCUMENTED_BY = "documented_by"


class KnowledgeGraph:
    """
    Knowledge Graph connecting concepts across repositories.
    
    This graph enables:
    - Cross-repository concept mapping
    - Pattern discovery
    - Knowledge transfer
    - Semantic search
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the knowledge graph.
        
        Args:
            storage_dir: Optional directory for persistent storage
        """
        # Set up storage directory
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), 'knowledge_graph_storage')
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize graph
        self.graph = nx.MultiDiGraph()
        
        # Initialize node and edge metadata
        self.node_metadata = {}  # node_id -> metadata
        self.edge_metadata = {}  # (source_id, target_id, edge_key) -> metadata
        
        # Initialize embeddings
        self.node_embeddings = {}  # node_id -> embedding vector
        
        # Initialize logger
        self.logger = logging.getLogger('knowledge_graph')
        
        # Load existing data
        self._load_graph()
    
    def _load_graph(self) -> None:
        """Load the graph from storage."""
        graph_path = os.path.join(self.storage_dir, 'graph.json')
        metadata_path = os.path.join(self.storage_dir, 'metadata.json')
        embeddings_path = os.path.join(self.storage_dir, 'embeddings.npz')
        
        # Load graph
        if os.path.exists(graph_path):
            try:
                with open(graph_path, 'r') as f:
                    graph_data = json.load(f)
                
                # Create nodes
                for node_id, node_attrs in graph_data['nodes'].items():
                    self.graph.add_node(node_id, **node_attrs)
                
                # Create edges
                for edge in graph_data['edges']:
                    source, target, key = edge['source'], edge['target'], edge.get('key', 0)
                    self.graph.add_edge(source, target, key=key, **edge['attrs'])
                
                self.logger.info(f"Loaded graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
            except Exception as e:
                self.logger.error(f"Error loading graph: {str(e)}")
                # Initialize new graph
                self.graph = nx.MultiDiGraph()
        
        # Load metadata
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                self.node_metadata = metadata['nodes']
                self.edge_metadata = metadata['edges']
                
                self.logger.info(f"Loaded metadata for {len(self.node_metadata)} nodes and {len(self.edge_metadata)} edges")
            except Exception as e:
                self.logger.error(f"Error loading metadata: {str(e)}")
                # Initialize new metadata
                self.node_metadata = {}
                self.edge_metadata = {}
        
        # Load embeddings
        if os.path.exists(embeddings_path):
            try:
                embeddings = np.load(embeddings_path, allow_pickle=True)
                self.node_embeddings = embeddings['embeddings'].item()
                
                self.logger.info(f"Loaded embeddings for {len(self.node_embeddings)} nodes")
            except Exception as e:
                self.logger.error(f"Error loading embeddings: {str(e)}")
                # Initialize new embeddings
                self.node_embeddings = {}
    
    def save(self) -> None:
        """Save the graph to storage."""
        graph_path = os.path.join(self.storage_dir, 'graph.json')
        metadata_path = os.path.join(self.storage_dir, 'metadata.json')
        embeddings_path = os.path.join(self.storage_dir, 'embeddings.npz')
        
        # Save graph
        try:
            # Convert graph to serializable format
            nodes_data = {n: dict(self.graph.nodes[n]) for n in self.graph.nodes}
            edges_data = []
            
            for u, v, k in self.graph.edges(keys=True):
                edges_data.append({
                    'source': u,
                    'target': v,
                    'key': k,
                    'attrs': dict(self.graph.edges[u, v, k])
                })
            
            graph_data = {
                'nodes': nodes_data,
                'edges': edges_data
            }
            
            with open(graph_path, 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            self.logger.info(f"Saved graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        except Exception as e:
            self.logger.error(f"Error saving graph: {str(e)}")
        
        # Save metadata
        try:
            # Convert edge keys to strings for JSON serialization
            edge_metadata = {}
            for (u, v, k), metadata in self.edge_metadata.items():
                edge_metadata[f"{u}|{v}|{k}"] = metadata
            
            metadata = {
                'nodes': self.node_metadata,
                'edges': edge_metadata
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Saved metadata for {len(self.node_metadata)} nodes and {len(self.edge_metadata)} edges")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {str(e)}")
        
        # Save embeddings
        try:
            np.savez_compressed(embeddings_path, embeddings=self.node_embeddings)
            
            self.logger.info(f"Saved embeddings for {len(self.node_embeddings)} nodes")
        except Exception as e:
            self.logger.error(f"Error saving embeddings: {str(e)}")
    
    def add_node(self, node_type: Union[str, NodeType], name: str, 
                properties: Optional[Dict[str, Any]] = None,
                metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a node to the graph.
        
        Args:
            node_type: Type of node
            name: Name of the node
            properties: Optional node properties
            metadata: Optional node metadata
            
        Returns:
            Node ID
        """
        # Generate node ID
        node_id = str(uuid.uuid4())
        
        # Convert node_type to string if enum
        if isinstance(node_type, NodeType):
            node_type = node_type.value
        
        # Create node attributes
        node_attrs = {
            'type': node_type,
            'name': name,
            'properties': properties or {}
        }
        
        # Add node to graph
        self.graph.add_node(node_id, **node_attrs)
        
        # Store metadata
        if metadata:
            self.node_metadata[node_id] = metadata
        
        self.logger.info(f"Added node: {name} (ID: {node_id}, Type: {node_type})")
        return node_id
    
    def add_edge(self, source_id: str, target_id: str, edge_type: Union[str, EdgeType],
               properties: Optional[Dict[str, Any]] = None,
               metadata: Optional[Dict[str, Any]] = None,
               weight: float = 1.0) -> Tuple[str, str, int]:
        """
        Add an edge to the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_type: Type of edge
            properties: Optional edge properties
            metadata: Optional edge metadata
            weight: Edge weight
            
        Returns:
            Tuple of (source_id, target_id, edge_key)
        """
        # Verify nodes exist
        if source_id not in self.graph:
            raise ValueError(f"Source node {source_id} not found")
        
        if target_id not in self.graph:
            raise ValueError(f"Target node {target_id} not found")
        
        # Convert edge_type to string if enum
        if isinstance(edge_type, EdgeType):
            edge_type = edge_type.value
        
        # Create edge attributes
        edge_attrs = {
            'type': edge_type,
            'weight': weight,
            'properties': properties or {}
        }
        
        # Add edge to graph
        edge_key = self.graph.add_edge(source_id, target_id, **edge_attrs)
        
        # Store metadata
        if metadata:
            self.edge_metadata[(source_id, target_id, edge_key)] = metadata
        
        self.logger.info(f"Added edge: {edge_type} from {source_id} to {target_id} (Key: {edge_key})")
        return (source_id, target_id, edge_key)
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Node data or None if not found
        """
        if node_id not in self.graph:
            return None
        
        # Get node attributes
        node_attrs = dict(self.graph.nodes[node_id])
        
        # Add metadata if exists
        if node_id in self.node_metadata:
            node_attrs['metadata'] = self.node_metadata[node_id]
        
        # Add ID
        node_attrs['id'] = node_id
        
        return node_attrs
    
    def get_edge(self, source_id: str, target_id: str, 
               edge_key: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get an edge by source, target, and key.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_key: Optional edge key
            
        Returns:
            Edge data or None if not found
        """
        if not self.graph.has_edge(source_id, target_id):
            return None
        
        if edge_key is None:
            # Get the first edge
            edge_key = 0
        
        if not self.graph.has_edge(source_id, target_id, edge_key):
            return None
        
        # Get edge attributes
        edge_attrs = dict(self.graph.edges[source_id, target_id, edge_key])
        
        # Add metadata if exists
        if (source_id, target_id, edge_key) in self.edge_metadata:
            edge_attrs['metadata'] = self.edge_metadata[(source_id, target_id, edge_key)]
        
        # Add IDs and key
        edge_attrs['source'] = source_id
        edge_attrs['target'] = target_id
        edge_attrs['key'] = edge_key
        
        return edge_attrs
    
    def update_node(self, node_id: str, 
                  properties: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a node's properties and metadata.
        
        Args:
            node_id: ID of the node to update
            properties: Optional node properties to update
            metadata: Optional node metadata to update
            
        Returns:
            Update success
        """
        if node_id not in self.graph:
            return False
        
        # Update properties
        if properties:
            curr_props = self.graph.nodes[node_id].get('properties', {})
            curr_props.update(properties)
            self.graph.nodes[node_id]['properties'] = curr_props
        
        # Update metadata
        if metadata:
            if node_id not in self.node_metadata:
                self.node_metadata[node_id] = {}
            
            self.node_metadata[node_id].update(metadata)
        
        self.logger.info(f"Updated node: {node_id}")
        return True
    
    def update_edge(self, source_id: str, target_id: str, edge_key: int,
                  properties: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  weight: Optional[float] = None) -> bool:
        """
        Update an edge's properties, metadata, and weight.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_key: Edge key
            properties: Optional edge properties to update
            metadata: Optional edge metadata to update
            weight: Optional edge weight to update
            
        Returns:
            Update success
        """
        if not self.graph.has_edge(source_id, target_id, edge_key):
            return False
        
        # Update properties
        if properties:
            curr_props = self.graph.edges[source_id, target_id, edge_key].get('properties', {})
            curr_props.update(properties)
            self.graph.edges[source_id, target_id, edge_key]['properties'] = curr_props
        
        # Update weight
        if weight is not None:
            self.graph.edges[source_id, target_id, edge_key]['weight'] = weight
        
        # Update metadata
        if metadata:
            edge_meta_key = (source_id, target_id, edge_key)
            if edge_meta_key not in self.edge_metadata:
                self.edge_metadata[edge_meta_key] = {}
            
            self.edge_metadata[edge_meta_key].update(metadata)
        
        self.logger.info(f"Updated edge: {source_id} to {target_id} (Key: {edge_key})")
        return True
    
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node from the graph.
        
        Args:
            node_id: ID of the node to delete
            
        Returns:
            Deletion success
        """
        if node_id not in self.graph:
            return False
        
        # Remove from graph
        self.graph.remove_node(node_id)
        
        # Remove metadata
        if node_id in self.node_metadata:
            del self.node_metadata[node_id]
        
        # Remove embedding
        if node_id in self.node_embeddings:
            del self.node_embeddings[node_id]
        
        # Remove edge metadata for edges connected to this node
        for key in list(self.edge_metadata.keys()):
            source, target, edge_key = key
            if source == node_id or target == node_id:
                del self.edge_metadata[key]
        
        self.logger.info(f"Deleted node: {node_id}")
        return True
    
    def delete_edge(self, source_id: str, target_id: str, 
                  edge_key: Optional[int] = None) -> bool:
        """
        Delete an edge from the graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_key: Optional edge key
            
        Returns:
            Deletion success
        """
        if not self.graph.has_edge(source_id, target_id):
            return False
        
        if edge_key is None:
            # Delete all edges between source and target
            self.graph.remove_edges_from([(source_id, target_id, k) for k in self.graph[source_id][target_id]])
            
            # Remove metadata
            for key in list(self.edge_metadata.keys()):
                s, t, ek = key
                if s == source_id and t == target_id:
                    del self.edge_metadata[key]
        else:
            # Delete specific edge
            if not self.graph.has_edge(source_id, target_id, edge_key):
                return False
            
            self.graph.remove_edge(source_id, target_id, edge_key)
            
            # Remove metadata
            edge_meta_key = (source_id, target_id, edge_key)
            if edge_meta_key in self.edge_metadata:
                del self.edge_metadata[edge_meta_key]
        
        self.logger.info(f"Deleted edge: {source_id} to {target_id}" + (f" (Key: {edge_key})" if edge_key is not None else ""))
        return True
    
    def find_nodes(self, node_type: Optional[Union[str, NodeType]] = None,
                 name_pattern: Optional[str] = None,
                 properties: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find nodes matching criteria.
        
        Args:
            node_type: Optional node type to filter by
            name_pattern: Optional regex pattern to match node names
            properties: Optional properties to filter by
            
        Returns:
            List of matching nodes
        """
        import re
        
        # Convert node_type to string if enum
        if isinstance(node_type, NodeType):
            node_type = node_type.value
        
        # Compile regex if provided
        name_regex = None
        if name_pattern:
            try:
                name_regex = re.compile(name_pattern)
            except Exception as e:
                self.logger.error(f"Invalid regex pattern: {name_pattern}")
                name_regex = None
        
        # Find matching nodes
        results = []
        
        for node_id in self.graph.nodes:
            node_data = self.get_node(node_id)
            
            # Apply node type filter
            if node_type and node_data['type'] != node_type:
                continue
            
            # Apply name pattern filter
            if name_regex and not name_regex.search(node_data['name']):
                continue
            
            # Apply properties filter
            if properties:
                match = True
                node_props = node_data.get('properties', {})
                
                for key, value in properties.items():
                    if key not in node_props or node_props[key] != value:
                        match = False
                        break
                
                if not match:
                    continue
            
            results.append(node_data)
        
        return results
    
    def find_edges(self, edge_type: Optional[Union[str, EdgeType]] = None,
                 source_id: Optional[str] = None,
                 target_id: Optional[str] = None,
                 min_weight: Optional[float] = None,
                 max_weight: Optional[float] = None,
                 properties: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find edges matching criteria.
        
        Args:
            edge_type: Optional edge type to filter by
            source_id: Optional source node ID
            target_id: Optional target node ID
            min_weight: Optional minimum weight
            max_weight: Optional maximum weight
            properties: Optional properties to filter by
            
        Returns:
            List of matching edges
        """
        # Convert edge_type to string if enum
        if isinstance(edge_type, EdgeType):
            edge_type = edge_type.value
        
        # Find matching edges
        results = []
        
        for u, v, k in self.graph.edges(keys=True):
            # Apply source filter
            if source_id and u != source_id:
                continue
            
            # Apply target filter
            if target_id and v != target_id:
                continue
            
            edge_data = self.get_edge(u, v, k)
            
            # Apply edge type filter
            if edge_type and edge_data['type'] != edge_type:
                continue
            
            # Apply weight filters
            if min_weight is not None and edge_data.get('weight', 1.0) < min_weight:
                continue
            
            if max_weight is not None and edge_data.get('weight', 1.0) > max_weight:
                continue
            
            # Apply properties filter
            if properties:
                match = True
                edge_props = edge_data.get('properties', {})
                
                for key, value in properties.items():
                    if key not in edge_props or edge_props[key] != value:
                        match = False
                        break
                
                if not match:
                    continue
            
            results.append(edge_data)
        
        return results
    
    def get_neighbors(self, node_id: str, 
                    direction: str = 'both',
                    edge_type: Optional[Union[str, EdgeType]] = None,
                    neighbor_type: Optional[Union[str, NodeType]] = None) -> List[Dict[str, Any]]:
        """
        Get neighbors of a node.
        
        Args:
            node_id: ID of the node
            direction: Direction ('in', 'out', or 'both')
            edge_type: Optional filter by edge type
            neighbor_type: Optional filter by neighbor node type
            
        Returns:
            List of neighbor nodes
        """
        if node_id not in self.graph:
            return []
        
        # Convert types to strings if enums
        if isinstance(edge_type, EdgeType):
            edge_type = edge_type.value
        
        if isinstance(neighbor_type, NodeType):
            neighbor_type = neighbor_type.value
        
        neighbors = []
        
        # Get outgoing neighbors
        if direction in ['out', 'both']:
            for target in self.graph.successors(node_id):
                for k in self.graph[node_id][target]:
                    edge_data = self.get_edge(node_id, target, k)
                    
                    # Apply edge type filter
                    if edge_type and edge_data['type'] != edge_type:
                        continue
                    
                    neighbor_data = self.get_node(target)
                    
                    # Apply neighbor type filter
                    if neighbor_type and neighbor_data['type'] != neighbor_type:
                        continue
                    
                    # Add edge data to neighbor data
                    neighbor_with_edge = neighbor_data.copy()
                    neighbor_with_edge['edge'] = edge_data
                    neighbor_with_edge['direction'] = 'out'
                    
                    neighbors.append(neighbor_with_edge)
        
        # Get incoming neighbors
        if direction in ['in', 'both']:
            for source in self.graph.predecessors(node_id):
                for k in self.graph[source][node_id]:
                    edge_data = self.get_edge(source, node_id, k)
                    
                    # Apply edge type filter
                    if edge_type and edge_data['type'] != edge_type:
                        continue
                    
                    neighbor_data = self.get_node(source)
                    
                    # Apply neighbor type filter
                    if neighbor_type and neighbor_data['type'] != neighbor_type:
                        continue
                    
                    # Add edge data to neighbor data
                    neighbor_with_edge = neighbor_data.copy()
                    neighbor_with_edge['edge'] = edge_data
                    neighbor_with_edge['direction'] = 'in'
                    
                    neighbors.append(neighbor_with_edge)
        
        return neighbors
    
    def set_node_embedding(self, node_id: str, embedding: np.ndarray) -> bool:
        """
        Set the embedding vector for a node.
        
        Args:
            node_id: ID of the node
            embedding: Embedding vector
            
        Returns:
            Success flag
        """
        if node_id not in self.graph:
            return False
        
        self.node_embeddings[node_id] = embedding
        return True
    
    def get_node_embedding(self, node_id: str) -> Optional[np.ndarray]:
        """
        Get the embedding vector for a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Embedding vector or None if not found
        """
        return self.node_embeddings.get(node_id)
    
    def find_similar_nodes(self, query_embedding: np.ndarray,
                         node_type: Optional[Union[str, NodeType]] = None,
                         top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find nodes with similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            node_type: Optional filter by node type
            top_k: Maximum number of results
            
        Returns:
            List of (node_id, similarity) tuples
        """
        if not self.node_embeddings:
            return []
        
        # Convert node_type to string if enum
        if isinstance(node_type, NodeType):
            node_type = node_type.value
        
        # Compute similarities
        similarities = []
        
        for node_id, embedding in self.node_embeddings.items():
            # Apply node type filter
            if node_type:
                node_data = self.get_node(node_id)
                if node_data['type'] != node_type:
                    continue
            
            # Compute cosine similarity
            similarity = self._cosine_similarity(query_embedding, embedding)
            similarities.append((node_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        return similarities[:top_k]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Cosine similarity
        """
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def find_path(self, source_id: str, target_id: str, 
                max_length: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Find a path between two nodes.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            max_length: Maximum path length
            
        Returns:
            List of alternating nodes and edges, or None if no path
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None
        
        try:
            # Find shortest path
            path = nx.shortest_path(self.graph, source_id, target_id, weight='weight', method='dijkstra')
            
            if len(path) > max_length + 1:
                return None
            
            # Convert to alternating nodes and edges
            result = []
            
            for i in range(len(path)):
                # Add node
                node_id = path[i]
                result.append(self.get_node(node_id))
                
                # Add edge if not the last node
                if i < len(path) - 1:
                    next_node_id = path[i + 1]
                    # Get first edge
                    edge_key = min(self.graph[node_id][next_node_id].keys())
                    result.append(self.get_edge(node_id, next_node_id, edge_key))
            
            return result
        
        except nx.NetworkXNoPath:
            return None
    
    def compute_centrality(self, node_type: Optional[Union[str, NodeType]] = None,
                         weight: str = 'weight') -> Dict[str, float]:
        """
        Compute node centrality.
        
        Args:
            node_type: Optional filter by node type
            weight: Edge attribute to use as weight
            
        Returns:
            Dictionary mapping node IDs to centrality values
        """
        # Convert node_type to string if enum
        if isinstance(node_type, NodeType):
            node_type = node_type.value
        
        # Create a subgraph if node type is specified
        if node_type:
            node_ids = [n for n in self.graph.nodes if self.graph.nodes[n]['type'] == node_type]
            subgraph = self.graph.subgraph(node_ids)
        else:
            subgraph = self.graph
        
        # Compute betweenness centrality
        try:
            centrality = nx.betweenness_centrality(subgraph, weight=weight)
            return centrality
        except Exception as e:
            self.logger.error(f"Error computing centrality: {str(e)}")
            return {}
    
    def find_communities(self, node_type: Optional[Union[str, NodeType]] = None,
                       min_community_size: int = 3) -> List[List[str]]:
        """
        Find communities in the graph.
        
        Args:
            node_type: Optional filter by node type
            min_community_size: Minimum community size
            
        Returns:
            List of communities (each a list of node IDs)
        """
        # Convert node_type to string if enum
        if isinstance(node_type, NodeType):
            node_type = node_type.value
        
        # Create a subgraph if node type is specified
        if node_type:
            node_ids = [n for n in self.graph.nodes if self.graph.nodes[n]['type'] == node_type]
            subgraph = self.graph.subgraph(node_ids)
        else:
            subgraph = self.graph
        
        # Convert to undirected graph for community detection
        undirected = subgraph.to_undirected()
        
        # Find communities
        try:
            import community as community_louvain
            
            # Compute communities using Louvain method
            partition = community_louvain.best_partition(undirected)
            
            # Group nodes by community
            communities = {}
            for node_id, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = []
                
                communities[community_id].append(node_id)
            
            # Filter by minimum size
            result = [nodes for nodes in communities.values() if len(nodes) >= min_community_size]
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error finding communities: {str(e)}")
            return []
    
    def extract_subgraph(self, node_ids: List[str], include_neighbors: bool = False,
                       neighbor_types: Optional[List[Union[str, NodeType]]] = None) -> 'KnowledgeGraph':
        """
        Extract a subgraph containing specified nodes.
        
        Args:
            node_ids: List of node IDs to include
            include_neighbors: Whether to include neighbors
            neighbor_types: Optional filter for neighbor types
            
        Returns:
            Extracted subgraph as a new KnowledgeGraph
        """
        # Convert neighbor types to strings if enums
        if neighbor_types:
            neighbor_types = [t.value if isinstance(t, NodeType) else t for t in neighbor_types]
        
        # Find all nodes to include
        all_nodes = set(node_ids)
        
        if include_neighbors:
            for node_id in node_ids:
                neighbors = self.get_neighbors(node_id)
                
                for neighbor in neighbors:
                    # Apply neighbor type filter
                    if neighbor_types and neighbor['type'] not in neighbor_types:
                        continue
                    
                    all_nodes.add(neighbor['id'])
        
        # Create a new knowledge graph
        subgraph = KnowledgeGraph()
        
        # Copy nodes and edges
        for node_id in all_nodes:
            node_data = self.get_node(node_id)
            
            # Create node in subgraph
            subgraph.graph.add_node(node_id, **{k: v for k, v in node_data.items() if k != 'id' and k != 'metadata'})
            
            # Copy metadata
            if 'metadata' in node_data:
                subgraph.node_metadata[node_id] = node_data['metadata']
            
            # Copy embedding
            if node_id in self.node_embeddings:
                subgraph.node_embeddings[node_id] = self.node_embeddings[node_id]
        
        # Copy edges between included nodes
        for node_id in all_nodes:
            for neighbor_id in all_nodes:
                if self.graph.has_edge(node_id, neighbor_id):
                    for k in self.graph[node_id][neighbor_id]:
                        edge_data = self.get_edge(node_id, neighbor_id, k)
                        
                        # Create edge in subgraph
                        edge_attrs = {key: value for key, value in edge_data.items() 
                                   if key not in ['source', 'target', 'key', 'metadata']}
                        
                        subgraph.graph.add_edge(node_id, neighbor_id, key=k, **edge_attrs)
                        
                        # Copy metadata
                        if 'metadata' in edge_data:
                            subgraph.edge_metadata[(node_id, neighbor_id, k)] = edge_data['metadata']
        
        return subgraph
    
    def merge(self, other: 'KnowledgeGraph', node_map: Optional[Dict[str, str]] = None) -> None:
        """
        Merge another knowledge graph into this one.
        
        Args:
            other: Knowledge graph to merge
            node_map: Optional mapping from other's node IDs to this graph's node IDs
        """
        # Use identity mapping if not provided
        if node_map is None:
            node_map = {node_id: node_id for node_id in other.graph.nodes}
        
        # Copy nodes
        for node_id in other.graph.nodes:
            if node_id in node_map:
                mapped_id = node_map[node_id]
                
                # Skip if node already exists
                if mapped_id in self.graph:
                    # Merge properties
                    node_data = other.get_node(node_id)
                    self.update_node(mapped_id, properties=node_data.get('properties'))
                    
                    # Merge metadata
                    if 'metadata' in node_data:
                        self.update_node(mapped_id, metadata=node_data['metadata'])
                else:
                    # Copy node
                    node_data = other.get_node(node_id)
                    
                    # Create node in this graph
                    self.graph.add_node(mapped_id, **{k: v for k, v in node_data.items() 
                                                   if k != 'id' and k != 'metadata'})
                    
                    # Copy metadata
                    if 'metadata' in node_data:
                        self.node_metadata[mapped_id] = node_data['metadata']
                    
                    # Copy embedding
                    if node_id in other.node_embeddings:
                        self.node_embeddings[mapped_id] = other.node_embeddings[node_id]
        
        # Copy edges
        for source_id, target_id, k in other.graph.edges(keys=True):
            if source_id in node_map and target_id in node_map:
                mapped_source = node_map[source_id]
                mapped_target = node_map[target_id]
                
                # Skip if edge already exists
                if self.graph.has_edge(mapped_source, mapped_target, k):
                    # Merge properties
                    edge_data = other.get_edge(source_id, target_id, k)
                    self.update_edge(mapped_source, mapped_target, k, 
                                  properties=edge_data.get('properties'),
                                  weight=edge_data.get('weight'))
                    
                    # Merge metadata
                    if 'metadata' in edge_data:
                        self.update_edge(mapped_source, mapped_target, k, 
                                      metadata=edge_data['metadata'])
                else:
                    # Copy edge
                    edge_data = other.get_edge(source_id, target_id, k)
                    
                    # Create edge in this graph
                    edge_attrs = {key: value for key, value in edge_data.items() 
                               if key not in ['source', 'target', 'key', 'metadata']}
                    
                    self.graph.add_edge(mapped_source, mapped_target, key=k, **edge_attrs)
                    
                    # Copy metadata
                    if 'metadata' in edge_data:
                        self.edge_metadata[(mapped_source, mapped_target, k)] = edge_data['metadata']
        
        self.logger.info(f"Merged knowledge graph with {other.graph.number_of_nodes()} nodes and {other.graph.number_of_edges()} edges")
    
    def visualize(self, node_ids: Optional[List[str]] = None, 
                max_nodes: int = 100, 
                output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a visualization of the graph.
        
        Args:
            node_ids: Optional list of node IDs to include
            max_nodes: Maximum number of nodes to include
            output_file: Optional file to save the visualization to
            
        Returns:
            Visualization data
        """
        try:
            import matplotlib.pyplot as plt
            
            # Create a subgraph if node IDs are specified
            if node_ids:
                subgraph = self.extract_subgraph(node_ids)
                graph = subgraph.graph
            else:
                graph = self.graph
            
            # Limit to max_nodes
            if graph.number_of_nodes() > max_nodes:
                # Take most central nodes
                centrality = nx.betweenness_centrality(graph)
                top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
                top_node_ids = [node_id for node_id, _ in top_nodes]
                
                graph = graph.subgraph(top_node_ids)
            
            # Set up colors and sizes based on node types
            colors = []
            sizes = []
            labels = {}
            
            for node_id in graph.nodes:
                node_type = graph.nodes[node_id]['type']
                node_name = graph.nodes[node_id]['name']
                
                # Assign color based on node type
                type_colors = {
                    'concept': 'blue',
                    'code_entity': 'green',
                    'pattern': 'purple',
                    'repository': 'red',
                    'file': 'orange',
                    'function': 'cyan',
                    'class': 'magenta',
                    'module': 'yellow',
                    'author': 'brown',
                    'commit': 'gray',
                    'issue': 'pink',
                    'dependency': 'olive'
                }
                
                colors.append(type_colors.get(node_type, 'black'))
                
                # Set size based on connections
                size = 100 + 10 * (graph.in_degree(node_id) + graph.out_degree(node_id))
                sizes.append(min(size, 500))  # Cap size
                
                # Set label
                labels[node_id] = node_name
            
            # Set up edge colors based on edge types
            edge_colors = []
            
            for source, target, key in graph.edges(keys=True):
                edge_type = graph.edges[source, target, key]['type']
                
                # Assign color based on edge type
                type_colors = {
                    'is_a': 'blue',
                    'part_of': 'green',
                    'implements': 'purple',
                    'depends_on': 'red',
                    'calls': 'orange',
                    'extends': 'cyan',
                    'authored_by': 'magenta',
                    'contains': 'yellow',
                    'related_to': 'gray',
                    'similar_to': 'pink',
                    'evolved_from': 'brown',
                    'documented_by': 'olive'
                }
                
                edge_colors.append(type_colors.get(edge_type, 'black'))
            
            # Create the plot
            plt.figure(figsize=(12, 12))
            
            # Use spring layout for positioning
            pos = nx.spring_layout(graph)
            
            # Draw nodes
            nx.draw_networkx_nodes(graph, pos, node_color=colors, node_size=sizes, alpha=0.8)
            
            # Draw edges
            nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, width=1, alpha=0.5, arrows=True)
            
            # Draw labels
            nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8)
            
            # Configure plot
            plt.axis('off')
            plt.title(f"Knowledge Graph Visualization ({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)")
            
            # Save to file if specified
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()
            
            # Return visualization data
            return {
                'node_count': graph.number_of_nodes(),
                'edge_count': graph.number_of_edges(),
                'node_types': {node_id: graph.nodes[node_id]['type'] for node_id in graph.nodes},
                'edge_types': {(s, t, k): graph.edges[s, t, k]['type'] for s, t, k in graph.edges(keys=True)},
                'output_file': output_file
            }
        
        except Exception as e:
            self.logger.error(f"Error generating visualization: {str(e)}")
            return {'error': str(e)}


class MultiRepositoryKnowledgeGraph:
    """
    Knowledge graph for connecting concepts across multiple repositories.
    
    This class provides:
    - Building knowledge graphs from repositories
    - Finding patterns across repositories
    - Knowledge transfer between repositories
    """
    
    def __init__(self, knowledge_graph: Optional[KnowledgeGraph] = None,
               storage_dir: Optional[str] = None):
        """
        Initialize the multi-repository knowledge graph.
        
        Args:
            knowledge_graph: Optional existing knowledge graph
            storage_dir: Optional directory for persistent storage
        """
        # Initialize knowledge graph
        self.kg = knowledge_graph or KnowledgeGraph(storage_dir)
        
        # Initialize logger
        self.logger = logging.getLogger('multi_repo_kg')
        
        # Map of repository IDs to node IDs
        self.repo_nodes = {}  # repo_id -> node_id
    
    def add_repository(self, repo_id: str, name: str, 
                     url: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a repository to the knowledge graph.
        
        Args:
            repo_id: Repository ID
            name: Repository name
            url: Repository URL
            metadata: Optional repository metadata
            
        Returns:
            Node ID
        """
        # Create a node for the repository
        node_id = self.kg.add_node(
            node_type=NodeType.REPOSITORY,
            name=name,
            properties={
                'url': url,
                'repo_id': repo_id
            },
            metadata=metadata
        )
        
        # Store the mapping
        self.repo_nodes[repo_id] = node_id
        
        self.logger.info(f"Added repository {name} (ID: {repo_id}) to knowledge graph")
        return node_id
    
    def import_code_files(self, repo_id: str, files: List[Dict[str, Any]]) -> List[str]:
        """
        Import code files from a repository into the knowledge graph.
        
        Args:
            repo_id: Repository ID
            files: List of code files
            
        Returns:
            List of file node IDs
        """
        if repo_id not in self.repo_nodes:
            raise ValueError(f"Repository {repo_id} not found in knowledge graph")
        
        repo_node_id = self.repo_nodes[repo_id]
        file_node_ids = []
        
        for file in files:
            # Create a node for the file
            file_node_id = self.kg.add_node(
                node_type=NodeType.FILE,
                name=file['path'],
                properties={
                    'path': file['path'],
                    'language': file['language'],
                    'size': file.get('size', 0),
                    'last_modified': file.get('last_modified', time.time()),
                    'file_id': file.get('id')
                },
                metadata=file.get('metadata')
            )
            
            # Create an edge from the repository to the file
            self.kg.add_edge(
                source_id=repo_node_id,
                target_id=file_node_id,
                edge_type=EdgeType.CONTAINS,
                properties={
                    'relationship': 'repository_contains_file'
                }
            )
            
            file_node_ids.append(file_node_id)
        
        self.logger.info(f"Imported {len(files)} files from repository {repo_id} into knowledge graph")
        return file_node_ids
    
    def import_code_entities(self, repo_id: str, file_node_id: str, 
                           entities: List[Dict[str, Any]]) -> List[str]:
        """
        Import code entities from a file into the knowledge graph.
        
        Args:
            repo_id: Repository ID
            file_node_id: File node ID
            entities: List of code entities
            
        Returns:
            List of entity node IDs
        """
        if repo_id not in self.repo_nodes:
            raise ValueError(f"Repository {repo_id} not found in knowledge graph")
        
        entity_node_ids = []
        
        for entity in entities:
            entity_type = entity['type']
            
            # Map entity type to node type
            if entity_type == 'function':
                node_type = NodeType.FUNCTION
            elif entity_type == 'class':
                node_type = NodeType.CLASS
            elif entity_type == 'module':
                node_type = NodeType.MODULE
            else:
                node_type = NodeType.CODE_ENTITY
            
            # Create a node for the entity
            entity_node_id = self.kg.add_node(
                node_type=node_type,
                name=entity['name'],
                properties={
                    'name': entity['name'],
                    'type': entity_type,
                    'start_line': entity.get('start_line'),
                    'end_line': entity.get('end_line'),
                    'entity_id': entity.get('id')
                },
                metadata=entity.get('metadata')
            )
            
            # Create an edge from the file to the entity
            self.kg.add_edge(
                source_id=file_node_id,
                target_id=entity_node_id,
                edge_type=EdgeType.CONTAINS,
                properties={
                    'relationship': 'file_contains_entity'
                }
            )
            
            entity_node_ids.append(entity_node_id)
        
        self.logger.info(f"Imported {len(entities)} code entities into knowledge graph")
        return entity_node_ids
    
    def import_dependencies(self, source_entity_id: str, 
                          target_entities: List[Dict[str, Any]]) -> List[str]:
        """
        Import dependencies between code entities into the knowledge graph.
        
        Args:
            source_entity_id: Source entity node ID
            target_entities: List of target entities with dependency type
            
        Returns:
            List of edge keys
        """
        edge_keys = []
        
        for target in target_entities:
            target_id = target['entity_id']
            dependency_type = target['dependency_type']
            
            # Map dependency type to edge type
            if dependency_type == 'calls':
                edge_type = EdgeType.CALLS
            elif dependency_type == 'extends':
                edge_type = EdgeType.EXTENDS
            elif dependency_type == 'implements':
                edge_type = EdgeType.IMPLEMENTS
            else:
                edge_type = EdgeType.DEPENDS_ON
            
            # Create an edge for the dependency
            source_id, target_id, edge_key = self.kg.add_edge(
                source_id=source_entity_id,
                target_id=target_id,
                edge_type=edge_type,
                properties={
                    'dependency_type': dependency_type,
                    'weight': target.get('weight', 1.0)
                },
                weight=target.get('weight', 1.0)
            )
            
            edge_keys.append(edge_key)
        
        self.logger.info(f"Imported {len(target_entities)} dependencies into knowledge graph")
        return edge_keys
    
    def import_patterns(self, repo_id: str, patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Import design patterns into the knowledge graph.
        
        Args:
            repo_id: Repository ID
            patterns: List of design patterns
            
        Returns:
            List of pattern node IDs
        """
        if repo_id not in self.repo_nodes:
            raise ValueError(f"Repository {repo_id} not found in knowledge graph")
        
        repo_node_id = self.repo_nodes[repo_id]
        pattern_node_ids = []
        
        for pattern in patterns:
            # Create a node for the pattern
            pattern_node_id = self.kg.add_node(
                node_type=NodeType.PATTERN,
                name=pattern['name'],
                properties={
                    'name': pattern['name'],
                    'type': pattern['type'],
                    'confidence': pattern.get('confidence', 1.0),
                    'pattern_id': pattern.get('id')
                },
                metadata=pattern.get('metadata')
            )
            
            # Create an edge from the repository to the pattern
            self.kg.add_edge(
                source_id=repo_node_id,
                target_id=pattern_node_id,
                edge_type=EdgeType.CONTAINS,
                properties={
                    'relationship': 'repository_contains_pattern'
                }
            )
            
            # Connect pattern to involved entities
            for entity_id in pattern.get('entities', []):
                self.kg.add_edge(
                    source_id=pattern_node_id,
                    target_id=entity_id,
                    edge_type=EdgeType.CONTAINS,
                    properties={
                        'relationship': 'pattern_contains_entity'
                    }
                )
            
            pattern_node_ids.append(pattern_node_id)
        
        self.logger.info(f"Imported {len(patterns)} patterns from repository {repo_id} into knowledge graph")
        return pattern_node_ids
    
    def import_concepts(self, concepts: List[Dict[str, Any]]) -> List[str]:
        """
        Import concepts into the knowledge graph.
        
        Args:
            concepts: List of concepts
            
        Returns:
            List of concept node IDs
        """
        concept_node_ids = []
        
        for concept in concepts:
            # Create a node for the concept
            concept_node_id = self.kg.add_node(
                node_type=NodeType.CONCEPT,
                name=concept['name'],
                properties={
                    'name': concept['name'],
                    'description': concept.get('description', ''),
                    'domain': concept.get('domain', ''),
                    'concept_id': concept.get('id')
                },
                metadata=concept.get('metadata')
            )
            
            # Set embedding if provided
            if 'embedding' in concept:
                embedding = np.array(concept['embedding'])
                self.kg.set_node_embedding(concept_node_id, embedding)
            
            # Connect concept to related entities
            for entity in concept.get('related_entities', []):
                entity_id = entity['entity_id']
                relationship = entity.get('relationship', 'related_to')
                
                # Map relationship to edge type
                if relationship == 'is_a':
                    edge_type = EdgeType.IS_A
                elif relationship == 'part_of':
                    edge_type = EdgeType.PART_OF
                elif relationship == 'implements':
                    edge_type = EdgeType.IMPLEMENTS
                else:
                    edge_type = EdgeType.RELATED_TO
                
                self.kg.add_edge(
                    source_id=entity_id,
                    target_id=concept_node_id,
                    edge_type=edge_type,
                    properties={
                        'relationship': relationship,
                        'weight': entity.get('weight', 1.0)
                    },
                    weight=entity.get('weight', 1.0)
                )
            
            concept_node_ids.append(concept_node_id)
        
        self.logger.info(f"Imported {len(concepts)} concepts into knowledge graph")
        return concept_node_ids
    
    def find_similar_patterns(self, pattern_id: str, 
                            min_similarity: float = 0.7,
                            across_repos: bool = True) -> List[Dict[str, Any]]:
        """
        Find patterns similar to a given pattern.
        
        Args:
            pattern_id: ID of the pattern node
            min_similarity: Minimum similarity threshold
            across_repos: Whether to look across all repositories
            
        Returns:
            List of similar patterns with similarity scores
        """
        pattern_node = self.kg.get_node(pattern_id)
        if not pattern_node or pattern_node['type'] != NodeType.PATTERN.value:
            raise ValueError(f"Node {pattern_id} is not a pattern")
        
        # Get the pattern's repository
        pattern_repo = None
        for neighbor in self.kg.get_neighbors(pattern_id, direction='in', edge_type=EdgeType.CONTAINS):
            if neighbor['type'] == NodeType.REPOSITORY.value:
                pattern_repo = neighbor['id']
                break
        
        # Get all pattern nodes
        patterns = self.kg.find_nodes(node_type=NodeType.PATTERN)
        
        # Compute similarities
        similar_patterns = []
        
        for other_pattern in patterns:
            other_id = other_pattern['id']
            
            # Skip self
            if other_id == pattern_id:
                continue
            
            # Check if from different repositories if required
            if not across_repos and pattern_repo:
                other_repo = None
                for neighbor in self.kg.get_neighbors(other_id, direction='in', edge_type=EdgeType.CONTAINS):
                    if neighbor['type'] == NodeType.REPOSITORY.value:
                        other_repo = neighbor['id']
                        break
                
                if other_repo == pattern_repo:
                    continue
            
            # Compute similarity based on shared entities
            pattern_entities = set()
            for neighbor in self.kg.get_neighbors(pattern_id, direction='out', edge_type=EdgeType.CONTAINS):
                if neighbor['type'] in [NodeType.FUNCTION.value, NodeType.CLASS.value, NodeType.MODULE.value]:
                    pattern_entities.add(neighbor['id'])
            
            other_entities = set()
            for neighbor in self.kg.get_neighbors(other_id, direction='out', edge_type=EdgeType.CONTAINS):
                if neighbor['type'] in [NodeType.FUNCTION.value, NodeType.CLASS.value, NodeType.MODULE.value]:
                    other_entities.add(neighbor['id'])
            
            # Jaccard similarity
            if not pattern_entities or not other_entities:
                similarity = 0.0
            else:
                intersection = len(pattern_entities.intersection(other_entities))
                union = len(pattern_entities.union(other_entities))
                similarity = intersection / union
            
            if similarity >= min_similarity:
                result = {
                    'pattern': other_pattern,
                    'similarity': similarity
                }
                
                # Add repository information
                for neighbor in self.kg.get_neighbors(other_id, direction='in', edge_type=EdgeType.CONTAINS):
                    if neighbor['type'] == NodeType.REPOSITORY.value:
                        result['repository'] = neighbor
                        break
                
                similar_patterns.append(result)
        
        # Sort by similarity (descending)
        similar_patterns.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similar_patterns
    
    def find_knowledge_transfer_opportunities(self, source_repo_id: str, 
                                           target_repo_id: str,
                                           min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find opportunities for knowledge transfer between repositories.
        
        Args:
            source_repo_id: Source repository ID
            target_repo_id: Target repository ID
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of knowledge transfer opportunities
        """
        if source_repo_id not in self.repo_nodes:
            raise ValueError(f"Source repository {source_repo_id} not found in knowledge graph")
        
        if target_repo_id not in self.repo_nodes:
            raise ValueError(f"Target repository {target_repo_id} not found in knowledge graph")
        
        source_node_id = self.repo_nodes[source_repo_id]
        target_node_id = self.repo_nodes[target_repo_id]
        
        # Get patterns in source repository
        source_patterns = []
        for neighbor in self.kg.get_neighbors(source_node_id, direction='out', edge_type=EdgeType.CONTAINS):
            if neighbor['type'] == NodeType.PATTERN.value:
                source_patterns.append(neighbor)
        
        # Get entities in target repository
        target_entities = {}  # entity_id -> entity
        target_files = []
        
        for neighbor in self.kg.get_neighbors(target_node_id, direction='out', edge_type=EdgeType.CONTAINS):
            if neighbor['type'] == NodeType.FILE.value:
                target_files.append(neighbor)
                
                # Get entities in the file
                for entity_neighbor in self.kg.get_neighbors(neighbor['id'], direction='out', edge_type=EdgeType.CONTAINS):
                    if entity_neighbor['type'] in [NodeType.FUNCTION.value, NodeType.CLASS.value, NodeType.MODULE.value]:
                        target_entities[entity_neighbor['id']] = entity_neighbor
        
        # Find opportunities
        opportunities = []
        
        for pattern in source_patterns:
            # Get entities in the pattern
            pattern_entities = []
            for neighbor in self.kg.get_neighbors(pattern['id'], direction='out', edge_type=EdgeType.CONTAINS):
                if neighbor['type'] in [NodeType.FUNCTION.value, NodeType.CLASS.value, NodeType.MODULE.value]:
                    pattern_entities.append(neighbor)
            
            # Check if pattern could be applied to target
            # This is a simplified approach - in a real system, this would use
            # more sophisticated matching algorithms
            
            # For each target entity, compute similarity to pattern entities
            entity_similarities = {}
            
            for target_id, target_entity in target_entities.items():
                best_similarity = 0.0
                best_match = None
                
                for pattern_entity in pattern_entities:
                    # Compute similarity based on name and function signatures
                    name_similarity = self._name_similarity(
                        pattern_entity['properties'].get('name', ''),
                        target_entity['properties'].get('name', '')
                    )
                    
                    if name_similarity > best_similarity:
                        best_similarity = name_similarity
                        best_match = pattern_entity
                
                if best_similarity >= min_similarity:
                    entity_similarities[target_id] = {
                        'target_entity': target_entity,
                        'pattern_entity': best_match,
                        'similarity': best_similarity
                    }
            
            # Check if enough entities match
            if len(entity_similarities) >= 2:  # Require at least 2 matching entities
                opportunities.append({
                    'pattern': pattern,
                    'matching_entities': entity_similarities,
                    'overall_similarity': sum(m['similarity'] for m in entity_similarities.values()) / len(entity_similarities)
                })
        
        # Sort by overall similarity (descending)
        opportunities.sort(key=lambda x: x['overall_similarity'], reverse=True)
        
        return opportunities
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """
        Compute similarity between two names.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score
        """
        # Convert to lowercase
        name1 = name1.lower()
        name2 = name2.lower()
        
        # Exact match
        if name1 == name2:
            return 1.0
        
        # Split into parts (camelCase, snake_case, etc.)
        import re
        
        def split_name(name):
            # Split by camelCase
            parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', name)
            if len(parts) <= 1:
                # Split by snake_case or kebab-case
                parts = re.split(r'[_\-]', name)
            return [p.lower() for p in parts if p]
        
        parts1 = split_name(name1)
        parts2 = split_name(name2)
        
        if not parts1 or not parts2:
            return 0.0
        
        # Compute Jaccard similarity of parts
        intersection = len(set(parts1).intersection(set(parts2)))
        union = len(set(parts1).union(set(parts2)))
        
        return intersection / union
    
    def compute_repository_similarity(self, repo_id1: str, repo_id2: str) -> Dict[str, Any]:
        """
        Compute similarity between two repositories.
        
        Args:
            repo_id1: First repository ID
            repo_id2: Second repository ID
            
        Returns:
            Similarity metrics
        """
        if repo_id1 not in self.repo_nodes:
            raise ValueError(f"Repository {repo_id1} not found in knowledge graph")
        
        if repo_id2 not in self.repo_nodes:
            raise ValueError(f"Repository {repo_id2} not found in knowledge graph")
        
        node_id1 = self.repo_nodes[repo_id1]
        node_id2 = self.repo_nodes[repo_id2]
        
        # Get files in each repository
        files1 = {}  # file_id -> file
        files2 = {}  # file_id -> file
        
        for neighbor in self.kg.get_neighbors(node_id1, direction='out', edge_type=EdgeType.CONTAINS):
            if neighbor['type'] == NodeType.FILE.value:
                files1[neighbor['id']] = neighbor
        
        for neighbor in self.kg.get_neighbors(node_id2, direction='out', edge_type=EdgeType.CONTAINS):
            if neighbor['type'] == NodeType.FILE.value:
                files2[neighbor['id']] = neighbor
        
        # Compute language distribution similarity
        languages1 = {}
        languages2 = {}
        
        for file in files1.values():
            lang = file['properties'].get('language', 'unknown')
            languages1[lang] = languages1.get(lang, 0) + 1
        
        for file in files2.values():
            lang = file['properties'].get('language', 'unknown')
            languages2[lang] = languages2.get(lang, 0) + 1
        
        # Convert to distributions
        sum1 = sum(languages1.values())
        sum2 = sum(languages2.values())
        
        lang_dist1 = {lang: count / sum1 for lang, count in languages1.items()}
        lang_dist2 = {lang: count / sum2 for lang, count in languages2.items()}
        
        # Compute Jensen-Shannon divergence
        all_langs = set(lang_dist1.keys()).union(set(lang_dist2.keys()))
        
        kl_div1 = 0.0
        kl_div2 = 0.0
        
        m_dist = {}
        for lang in all_langs:
            p = lang_dist1.get(lang, 0.0)
            q = lang_dist2.get(lang, 0.0)
            m = (p + q) / 2
            m_dist[lang] = m
            
            if p > 0:
                kl_div1 += p * np.log2(p / m) if m > 0 else 0.0
            
            if q > 0:
                kl_div2 += q * np.log2(q / m) if m > 0 else 0.0
        
        js_div = (kl_div1 + kl_div2) / 2
        lang_similarity = 1.0 - min(js_div, 1.0)  # Convert to similarity
        
        # Get patterns in each repository
        patterns1 = []
        patterns2 = []
        
        for neighbor in self.kg.get_neighbors(node_id1, direction='out', edge_type=EdgeType.CONTAINS):
            if neighbor['type'] == NodeType.PATTERN.value:
                patterns1.append(neighbor)
        
        for neighbor in self.kg.get_neighbors(node_id2, direction='out', edge_type=EdgeType.CONTAINS):
            if neighbor['type'] == NodeType.PATTERN.value:
                patterns2.append(neighbor)
        
        # Compare patterns
        pattern_names1 = set(p['name'] for p in patterns1)
        pattern_names2 = set(p['name'] for p in patterns2)
        
        common_patterns = pattern_names1.intersection(pattern_names2)
        all_patterns = pattern_names1.union(pattern_names2)
        
        pattern_similarity = len(common_patterns) / len(all_patterns) if all_patterns else 0.0
        
        # Combine similarities
        overall_similarity = (lang_similarity + pattern_similarity) / 2
        
        return {
            'repositories': [repo_id1, repo_id2],
            'language_similarity': lang_similarity,
            'pattern_similarity': pattern_similarity,
            'overall_similarity': overall_similarity,
            'language_distributions': {
                repo_id1: lang_dist1,
                repo_id2: lang_dist2
            },
            'common_patterns': list(common_patterns)
        }
    
    def save(self) -> None:
        """Save the knowledge graph."""
        self.kg.save()
        
        # Save repository node mapping
        mapping_path = os.path.join(self.kg.storage_dir, 'repo_mapping.json')
        
        try:
            with open(mapping_path, 'w') as f:
                json.dump(self.repo_nodes, f, indent=2)
            
            self.logger.info(f"Saved repository node mapping for {len(self.repo_nodes)} repositories")
        except Exception as e:
            self.logger.error(f"Error saving repository node mapping: {str(e)}")
    
    def visualize_repository_similarity_network(self, min_similarity: float = 0.6,
                                             output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Visualize the similarity network between repositories.
        
        Args:
            min_similarity: Minimum similarity threshold
            output_file: Optional file to save the visualization to
            
        Returns:
            Visualization data
        """
        try:
            import matplotlib.pyplot as plt
            import networkx as nx
            
            # Create a graph of repositories
            G = nx.Graph()
            
            # Add nodes for each repository
            for repo_id, node_id in self.repo_nodes.items():
                repo_node = self.kg.get_node(node_id)
                G.add_node(repo_id, name=repo_node['name'])
            
            # Compute similarities between repositories
            for repo_id1 in self.repo_nodes:
                for repo_id2 in self.repo_nodes:
                    if repo_id1 >= repo_id2:  # Avoid duplicate comparisons
                        continue
                    
                    try:
                        similarity = self.compute_repository_similarity(repo_id1, repo_id2)
                        if similarity['overall_similarity'] >= min_similarity:
                            G.add_edge(
                                repo_id1, 
                                repo_id2, 
                                weight=similarity['overall_similarity'],
                                similarity=similarity
                            )
                    except Exception as e:
                        self.logger.error(f"Error computing similarity between {repo_id1} and {repo_id2}: {str(e)}")
            
            # Create the plot
            plt.figure(figsize=(12, 12))
            
            # Calculate node sizes based on number of files
            sizes = {}
            for repo_id, node_id in self.repo_nodes.items():
                file_count = 0
                for neighbor in self.kg.get_neighbors(node_id, direction='out', edge_type=EdgeType.CONTAINS):
                    if neighbor['type'] == NodeType.FILE.value:
                        file_count += 1
                
                sizes[repo_id] = 100 + 10 * file_count
            
            # Use spring layout for positioning
            pos = nx.spring_layout(G, weight='weight')
            
            # Draw nodes
            nx.draw_networkx_nodes(
                G, 
                pos, 
                node_size=[sizes.get(n, 100) for n in G.nodes()],
                alpha=0.8
            )
            
            # Draw edges with width proportional to similarity
            edge_widths = [G[u][v]['weight'] * 5 for u, v in G.edges()]
            nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.5)
            
            # Draw labels
            labels = {n: G.nodes[n]['name'] for n in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels=labels, font_size=10)
            
            # Configure plot
            plt.axis('off')
            plt.title(f"Repository Similarity Network ({G.number_of_nodes()} repositories, {G.number_of_edges()} connections)")
            
            # Save to file if specified
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()
            
            # Return visualization data
            return {
                'repository_count': G.number_of_nodes(),
                'connection_count': G.number_of_edges(),
                'average_similarity': np.mean([G[u][v]['weight'] for u, v in G.edges()]) if G.number_of_edges() > 0 else 0.0,
                'output_file': output_file
            }
        
        except Exception as e:
            self.logger.error(f"Error generating visualization: {str(e)}")
            return {'error': str(e)}