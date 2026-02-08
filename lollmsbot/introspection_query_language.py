"""
Introspection Query Language (IQL) v2 - Structured Self-Examination for RCL-2

Provides a SQL-like query language for examining the agent's cognitive state.
This is a READ-ONLY introspection tool that doesn't modify any existing systems.

Example queries:
    INTROSPECT {
        SELECT uncertainty, attention_focus, epistemic_status
        FROM current_cognitive_state
        WHERE topic = "last_decision"
        DEPTH 3
        WITH transparency = "full"
        CONSTRAINT max_latency = 200ms
    }

Features:
- SQL-like syntax for cognitive queries
- Type-safe returns
- Constraint satisfaction
- Post-mortem analysis
- Root cause analysis for errors
- Reflexive debugging
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger("lollmsbot.iql")


class TokenType(Enum):
    """Token types for IQL lexer."""
    INTROSPECT = "INTROSPECT"
    SELECT = "SELECT"
    FROM = "FROM"
    WHERE = "WHERE"
    DEPTH = "DEPTH"
    WITH = "WITH"
    CONSTRAINT = "CONSTRAINT"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    EQUALS = "EQUALS"
    COMMA = "COMMA"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    EOF = "EOF"


@dataclass
class Token:
    """A lexical token."""
    type: TokenType
    value: Any
    position: int


class IQLLexer:
    """Tokenizer for IQL queries."""
    
    KEYWORDS = {
        "INTROSPECT", "SELECT", "FROM", "WHERE", 
        "DEPTH", "WITH", "CONSTRAINT"
    }
    
    def __init__(self, query: str):
        self.query = query
        self.position = 0
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """Tokenize the query string."""
        while self.position < len(self.query):
            char = self.query[self.position]
            
            # Skip whitespace
            if char.isspace():
                self.position += 1
                continue
            
            # Braces
            if char == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', self.position))
                self.position += 1
                continue
            
            if char == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', self.position))
                self.position += 1
                continue
            
            # Comma
            if char == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.position))
                self.position += 1
                continue
            
            # Equals
            if char == '=':
                self.tokens.append(Token(TokenType.EQUALS, '=', self.position))
                self.position += 1
                continue
            
            # String literals
            if char in ('"', "'"):
                self.tokens.append(self._read_string(char))
                continue
            
            # Numbers
            if char.isdigit():
                self.tokens.append(self._read_number())
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self.tokens.append(self._read_identifier())
                continue
            
            # Unknown character
            logger.warning(f"Unknown character '{char}' at position {self.position}")
            self.position += 1
        
        self.tokens.append(Token(TokenType.EOF, None, self.position))
        return self.tokens
    
    def _read_string(self, quote: str) -> Token:
        """Read a string literal."""
        start = self.position
        self.position += 1  # Skip opening quote
        
        value = ""
        while self.position < len(self.query):
            char = self.query[self.position]
            if char == quote:
                self.position += 1  # Skip closing quote
                break
            value += char
            self.position += 1
        
        return Token(TokenType.STRING, value, start)
    
    def _read_number(self) -> Token:
        """Read a number."""
        start = self.position
        value = ""
        
        while self.position < len(self.query):
            char = self.query[self.position]
            if char.isdigit() or char == '.':
                value += char
                self.position += 1
            else:
                break
        
        # Parse as float or int
        num_value = float(value) if '.' in value else int(value)
        return Token(TokenType.NUMBER, num_value, start)
    
    def _read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start = self.position
        value = ""
        
        while self.position < len(self.query):
            char = self.query[self.position]
            if char.isalnum() or char == '_':
                value += char
                self.position += 1
            else:
                break
        
        # Check if it's a keyword
        upper_value = value.upper()
        if upper_value in self.KEYWORDS:
            token_type = TokenType[upper_value]
        else:
            token_type = TokenType.IDENTIFIER
        
        return Token(token_type, value, start)


@dataclass
class IQLQuery:
    """Parsed IQL query structure."""
    select_fields: List[str]
    from_source: str
    where_conditions: Dict[str, Any] = field(default_factory=dict)
    depth: int = 1
    with_options: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)


class IQLParser:
    """Parser for IQL queries."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
    
    def parse(self) -> IQLQuery:
        """Parse tokens into query structure."""
        # Expect INTROSPECT
        self._expect(TokenType.INTROSPECT)
        
        # Expect {
        self._expect(TokenType.LBRACE)
        
        # Parse SELECT clause
        select_fields = self._parse_select()
        
        # Parse FROM clause
        from_source = self._parse_from()
        
        # Parse optional WHERE clause
        where_conditions = {}
        if self._current_token().type == TokenType.WHERE:
            where_conditions = self._parse_where()
        
        # Parse optional DEPTH
        depth = 1
        if self._current_token().type == TokenType.DEPTH:
            depth = self._parse_depth()
        
        # Parse optional WITH
        with_options = {}
        if self._current_token().type == TokenType.WITH:
            with_options = self._parse_with()
        
        # Parse optional CONSTRAINT
        constraints = {}
        if self._current_token().type == TokenType.CONSTRAINT:
            constraints = self._parse_constraint()
        
        # Expect }
        self._expect(TokenType.RBRACE)
        
        return IQLQuery(
            select_fields=select_fields,
            from_source=from_source,
            where_conditions=where_conditions,
            depth=depth,
            with_options=with_options,
            constraints=constraints,
        )
    
    def _current_token(self) -> Token:
        """Get current token."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return self.tokens[-1]  # EOF
    
    def _advance(self) -> Token:
        """Move to next token and return current."""
        token = self._current_token()
        if token.type != TokenType.EOF:
            self.position += 1
        return token
    
    def _expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type."""
        token = self._current_token()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type.value}, got {token.type.value} at position {token.position}"
            )
        return self._advance()
    
    def _parse_select(self) -> List[str]:
        """Parse SELECT clause."""
        self._expect(TokenType.SELECT)
        
        fields = []
        while True:
            token = self._expect(TokenType.IDENTIFIER)
            fields.append(token.value)
            
            if self._current_token().type != TokenType.COMMA:
                break
            self._advance()  # Skip comma
        
        return fields
    
    def _parse_from(self) -> str:
        """Parse FROM clause."""
        self._expect(TokenType.FROM)
        token = self._expect(TokenType.IDENTIFIER)
        return token.value
    
    def _parse_where(self) -> Dict[str, Any]:
        """Parse WHERE clause."""
        self._expect(TokenType.WHERE)
        
        conditions = {}
        while True:
            # Get field name
            field_token = self._expect(TokenType.IDENTIFIER)
            
            # Expect =
            self._expect(TokenType.EQUALS)
            
            # Get value
            value_token = self._current_token()
            if value_token.type in (TokenType.STRING, TokenType.NUMBER):
                self._advance()
                conditions[field_token.value] = value_token.value
            else:
                raise SyntaxError(f"Expected value at position {value_token.position}")
            
            # Check for more conditions (simplified - no AND/OR for now)
            if self._current_token().type not in (TokenType.IDENTIFIER,):
                break
        
        return conditions
    
    def _parse_depth(self) -> int:
        """Parse DEPTH clause."""
        self._expect(TokenType.DEPTH)
        token = self._expect(TokenType.NUMBER)
        return int(token.value)
    
    def _parse_with(self) -> Dict[str, Any]:
        """Parse WITH clause."""
        self._expect(TokenType.WITH)
        
        options = {}
        while True:
            # Get option name
            name_token = self._expect(TokenType.IDENTIFIER)
            
            # Expect =
            self._expect(TokenType.EQUALS)
            
            # Get value
            value_token = self._current_token()
            if value_token.type in (TokenType.STRING, TokenType.NUMBER):
                self._advance()
                options[name_token.value] = value_token.value
            else:
                raise SyntaxError(f"Expected value at position {value_token.position}")
            
            # Check for more options
            if self._current_token().type not in (TokenType.IDENTIFIER,):
                break
        
        return options
    
    def _parse_constraint(self) -> Dict[str, Any]:
        """Parse CONSTRAINT clause."""
        self._expect(TokenType.CONSTRAINT)
        
        constraints = {}
        while True:
            # Get constraint name
            name_token = self._expect(TokenType.IDENTIFIER)
            
            # Expect =
            self._expect(TokenType.EQUALS)
            
            # Get value
            value_token = self._current_token()
            if value_token.type in (TokenType.STRING, TokenType.NUMBER):
                self._advance()
                constraints[name_token.value] = value_token.value
            else:
                raise SyntaxError(f"Expected value at position {value_token.position}")
            
            # Check for more constraints
            if self._current_token().type not in (TokenType.IDENTIFIER,):
                break
        
        return constraints


@dataclass
class IntrospectionResult:
    """Result from an introspection query."""
    query: str
    fields: Dict[str, Any]
    source: str
    timestamp: datetime
    execution_time_ms: float
    constraints_satisfied: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "fields": self.fields,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "constraints_satisfied": self.constraints_satisfied,
            "metadata": self.metadata,
        }


class IQLExecutor:
    """
    Executor for IQL queries.
    
    This is READ-ONLY - it queries existing RCL-2 components without modifying them.
    """
    
    def __init__(self):
        """Initialize executor."""
        # Try to import RCL-2 components (optional - gracefully handle missing)
        self.has_cognitive_core = False
        self.has_restraints = False
        self.has_council = False
        self.has_twin = False
        self.has_narrative = False
        self.has_eigenmemory = False
        
        try:
            from lollmsbot.cognitive_core import get_cognitive_core
            self.get_cognitive_core = get_cognitive_core
            self.has_cognitive_core = True
        except ImportError:
            logger.debug("Cognitive core not available")
        
        try:
            from lollmsbot.constitutional_restraints import get_restraints
            self.get_restraints = get_restraints
            self.has_restraints = True
        except ImportError:
            logger.debug("Constitutional restraints not available")
        
        try:
            from lollmsbot.reflective_council import get_council
            self.get_council = get_council
            self.has_council = True
        except ImportError:
            logger.debug("Reflective council not available")
        
        try:
            from lollmsbot.cognitive_twin import get_cognitive_twin
            self.get_cognitive_twin = get_cognitive_twin
            self.has_twin = True
        except ImportError:
            logger.debug("Cognitive twin not available")
        
        try:
            from lollmsbot.narrative_identity import get_narrative_engine
            self.get_narrative_engine = get_narrative_engine
            self.has_narrative = True
        except ImportError:
            logger.debug("Narrative identity not available")
        
        try:
            from lollmsbot.eigenmemory import get_eigenmemory
            self.get_eigenmemory = get_eigenmemory
            self.has_eigenmemory = True
        except ImportError:
            logger.debug("Eigenmemory not available")
    
    def execute(self, query: IQLQuery, original_query: str) -> IntrospectionResult:
        """
        Execute an introspection query.
        
        Args:
            query: Parsed query structure
            original_query: Original query string
            
        Returns:
            IntrospectionResult with requested fields
        """
        start_time = time.time()
        
        # Route to appropriate source
        if query.from_source == "current_cognitive_state":
            fields = self._query_cognitive_state(query)
        elif query.from_source == "restraints":
            fields = self._query_restraints(query)
        elif query.from_source == "council":
            fields = self._query_council(query)
        elif query.from_source == "twin":
            fields = self._query_twin(query)
        elif query.from_source == "narrative":
            fields = self._query_narrative(query)
        elif query.from_source == "memory":
            fields = self._query_memory(query)
        else:
            raise ValueError(f"Unknown source: {query.from_source}")
        
        # Check constraints
        execution_time_ms = (time.time() - start_time) * 1000
        constraints_satisfied = self._check_constraints(
            query.constraints, 
            execution_time_ms
        )
        
        return IntrospectionResult(
            query=original_query,
            fields=fields,
            source=query.from_source,
            timestamp=datetime.now(),
            execution_time_ms=execution_time_ms,
            constraints_satisfied=constraints_satisfied,
            metadata={
                "depth": query.depth,
                "with_options": query.with_options,
            }
        )
    
    def _query_cognitive_state(self, query: IQLQuery) -> Dict[str, Any]:
        """Query current cognitive state."""
        if not self.has_cognitive_core:
            return {"error": "Cognitive core not available"}
        
        try:
            core = self.get_cognitive_core()
            state = core.get_current_state()
            
            # Extract requested fields
            result = {}
            for field in query.select_fields:
                if field == "uncertainty":
                    result["uncertainty"] = state.get("uncertainty", 0.0)
                elif field == "attention_focus":
                    result["attention_focus"] = state.get("attention_focus", [])
                elif field == "epistemic_status":
                    result["epistemic_status"] = state.get("epistemic_status", "unknown")
                elif field == "system_mode":
                    result["system_mode"] = state.get("current_system", "System1")
                elif field == "somatic_marker":
                    result["somatic_marker"] = state.get("somatic_marker", "NEUTRAL")
                else:
                    result[field] = state.get(field, None)
            
            return result
        except Exception as e:
            logger.error(f"Error querying cognitive state: {e}")
            return {"error": str(e)}
    
    def _query_restraints(self, query: IQLQuery) -> Dict[str, Any]:
        """Query constitutional restraints."""
        if not self.has_restraints:
            return {"error": "Constitutional restraints not available"}
        
        try:
            restraints = self.get_restraints()
            
            result = {}
            for field in query.select_fields:
                if field == "all":
                    result = restraints.get_all_restraints()
                elif field in restraints.get_all_restraints():
                    result[field] = restraints.get_restraint(field)
                else:
                    result[field] = None
            
            return result
        except Exception as e:
            logger.error(f"Error querying restraints: {e}")
            return {"error": str(e)}
    
    def _query_council(self, query: IQLQuery) -> Dict[str, Any]:
        """Query reflective council."""
        if not self.has_council:
            return {"error": "Reflective council not available"}
        
        try:
            council = self.get_council()
            
            result = {}
            for field in query.select_fields:
                if field == "status":
                    result["status"] = council.get_status()
                elif field == "last_deliberation":
                    result["last_deliberation"] = council.get_last_deliberation()
                elif field == "member_states":
                    result["member_states"] = council.get_member_states()
                else:
                    result[field] = None
            
            return result
        except Exception as e:
            logger.error(f"Error querying council: {e}")
            return {"error": str(e)}
    
    def _query_twin(self, query: IQLQuery) -> Dict[str, Any]:
        """Query cognitive twin."""
        if not self.has_twin:
            return {"error": "Cognitive twin not available"}
        
        try:
            twin = self.get_cognitive_twin()
            
            result = {}
            for field in query.select_fields:
                if field == "latency_prediction":
                    result["latency_prediction"] = twin.predict_latency()
                elif field == "memory_pressure":
                    result["memory_pressure"] = twin.predict_memory_pressure()
                elif field == "health":
                    result["health"] = twin.get_health()
                else:
                    result[field] = None
            
            return result
        except Exception as e:
            logger.error(f"Error querying twin: {e}")
            return {"error": str(e)}
    
    def _query_narrative(self, query: IQLQuery) -> Dict[str, Any]:
        """Query narrative identity."""
        if not self.has_narrative:
            return {"error": "Narrative identity not available"}
        
        try:
            narrative = self.get_narrative_engine()
            
            result = {}
            for field in query.select_fields:
                if field == "identity_summary":
                    result["identity_summary"] = narrative.get_identity_summary()
                elif field == "current_stage":
                    summary = narrative.get_identity_summary()
                    result["current_stage"] = summary.get("current_stage")
                elif field == "life_story":
                    result["life_story"] = [
                        e.to_dict() for e in narrative.get_life_story()[:10]
                    ]
                else:
                    result[field] = None
            
            return result
        except Exception as e:
            logger.error(f"Error querying narrative: {e}")
            return {"error": str(e)}
    
    def _query_memory(self, query: IQLQuery) -> Dict[str, Any]:
        """Query eigenmemory."""
        if not self.has_eigenmemory:
            return {"error": "Eigenmemory not available"}
        
        try:
            memory = self.get_eigenmemory()
            
            result = {}
            for field in query.select_fields:
                if field == "statistics":
                    result["statistics"] = memory.get_memory_statistics()
                elif field == "confabulations":
                    result["confabulations"] = memory.detect_confabulations()
                else:
                    result[field] = None
            
            return result
        except Exception as e:
            logger.error(f"Error querying memory: {e}")
            return {"error": str(e)}
    
    def _check_constraints(
        self, 
        constraints: Dict[str, Any], 
        execution_time_ms: float
    ) -> bool:
        """Check if constraints are satisfied."""
        if not constraints:
            return True
        
        # Check max_latency constraint
        if "max_latency" in constraints:
            max_latency_str = constraints["max_latency"]
            # Parse latency (e.g., "200ms")
            if isinstance(max_latency_str, str) and max_latency_str.endswith("ms"):
                max_latency_ms = float(max_latency_str[:-2])
                if execution_time_ms > max_latency_ms:
                    return False
        
        return True


def query_cognitive_state(query_string: str) -> IntrospectionResult:
    """
    Execute an IQL query against the cognitive state.
    
    This is the main entry point for introspection queries.
    
    Args:
        query_string: IQL query string
        
    Returns:
        IntrospectionResult with requested data
        
    Example:
        >>> result = query_cognitive_state('''
        ...     INTROSPECT {
        ...         SELECT uncertainty, system_mode
        ...         FROM current_cognitive_state
        ...     }
        ... ''')
        >>> print(result.fields['uncertainty'])
    """
    try:
        # Tokenize
        lexer = IQLLexer(query_string)
        tokens = lexer.tokenize()
        
        # Parse
        parser = IQLParser(tokens)
        query = parser.parse()
        
        # Execute
        executor = IQLExecutor()
        result = executor.execute(query, query_string)
        
        return result
    
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return IntrospectionResult(
            query=query_string,
            fields={"error": str(e)},
            source="error",
            timestamp=datetime.now(),
            execution_time_ms=0.0,
            constraints_satisfied=False,
        )


def post_mortem_analysis(error_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform post-mortem analysis on an error.
    
    Args:
        error_context: Context about the error (traceback, state, etc.)
        
    Returns:
        Analysis results with root cause and recommendations
    """
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "error_type": error_context.get("error_type", "unknown"),
        "root_cause": "unknown",
        "contributing_factors": [],
        "recommendations": [],
    }
    
    # Try to query cognitive state at time of error
    try:
        result = query_cognitive_state("""
            INTROSPECT {
                SELECT uncertainty, system_mode, somatic_marker
                FROM current_cognitive_state
            }
        """)
        
        if not result.fields.get("error"):
            analysis["cognitive_state_at_error"] = result.fields
            
            # Analyze for patterns
            uncertainty = result.fields.get("uncertainty", 0.0)
            if uncertainty > 0.7:
                analysis["contributing_factors"].append("High uncertainty")
                analysis["recommendations"].append("Request clarification or additional context")
    
    except Exception as e:
        logger.debug(f"Could not query cognitive state: {e}")
    
    return analysis


# Example queries for documentation
EXAMPLE_QUERIES = {
    "cognitive_state": """
        INTROSPECT {
            SELECT uncertainty, attention_focus, epistemic_status
            FROM current_cognitive_state
            DEPTH 3
            WITH transparency = "full"
        }
    """,
    
    "restraints": """
        INTROSPECT {
            SELECT hallucination_resistance, transparency_level
            FROM restraints
        }
    """,
    
    "council_status": """
        INTROSPECT {
            SELECT status, last_deliberation
            FROM council
        }
    """,
    
    "twin_predictions": """
        INTROSPECT {
            SELECT latency_prediction, memory_pressure
            FROM twin
            CONSTRAINT max_latency = 200ms
        }
    """,
    
    "narrative_summary": """
        INTROSPECT {
            SELECT identity_summary, current_stage
            FROM narrative
        }
    """,
    
    "memory_stats": """
        INTROSPECT {
            SELECT statistics, confabulations
            FROM memory
        }
    """,
}


if __name__ == "__main__":
    # Test the parser with example queries
    print("IQL v2 - Introspection Query Language")
    print("=" * 50)
    
    for name, query in EXAMPLE_QUERIES.items():
        print(f"\nTesting: {name}")
        print("-" * 50)
        try:
            result = query_cognitive_state(query)
            print(f"Success: {result.execution_time_ms:.2f}ms")
            print(f"Fields: {list(result.fields.keys())}")
            if result.fields.get("error"):
                print(f"Note: {result.fields['error']}")
        except Exception as e:
            print(f"Error: {e}")
