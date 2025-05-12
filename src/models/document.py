"""
Document models for representing Confluence document data.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Any, Optional


class DocumentType(str, Enum):
    """Types of business requirement documents."""
    ABRD = "ABRD"
    FBRD = "FBRD"
    UNKNOWN = "UNKNOWN"


@dataclass
class DocumentMetadata:
    """Metadata for a document."""
    document_id: str = ""
    document_type: DocumentType = DocumentType.UNKNOWN
    project_code: str = ""
    document_version: str = ""
    status: str = ""
    created_date: str = ""
    last_updated_date: str = ""
    document_owner: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert enum to string
        data["document_type"] = self.document_type.value
        return data


@dataclass
class DocumentSection:
    """Section of a document."""
    section_id: str
    title: str
    level: int
    content: str
    section_number: str = ""
    requirement_ids: List[str] = field(default_factory=list)


@dataclass
class SearchableDocument:
    """Document ready for indexing in Azure Search."""
    id: str
    content: str
    source_page_id: str
    source_page_title: str
    source_url: str
    is_section: bool
    section_id: str
    section_title: str
    section_level: int
    section_number: str
    document_type: DocumentType
    project_code: str
    document_id: str
    document_version: str
    document_status: str
    created_date: str
    last_updated_date: str
    document_owner: str
    summary: str = ""
    requirement_ids: List[str] = field(default_factory=list)
    vectorized: bool = False
    vector: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Azure Search indexing."""
        data = asdict(self)
        
        # Convert enum to string
        data["document_type"] = self.document_type.value
        
        # Handle vector field
        if self.vectorized and self.vector:
            # Convert vector to space-separated string of values
            data["vector"] = " ".join(str(x) for x in self.vector)
        else:
            # Remove vector-related fields if not vectorized
            if "vector" in data:
                del data["vector"]
        
        # The 'vectorized' field is internal and not part of the Azure Search schema
        if "vectorized" in data:
            del data["vectorized"]
            
        return data 