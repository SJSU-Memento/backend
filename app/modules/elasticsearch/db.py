import traceback
from elasticsearch import Elasticsearch
from typing import Dict, List, Literal, Optional, Any, Union
from datetime import datetime
import uuid
from sentence_transformers import SentenceTransformer

script_source = """double llm_score = cosineSimilarity(params.query_vector, 'llm_description_vector') + 1.0;
double ocr_score = !doc['ocr_text_vector'].isEmpty() ? cosineSimilarity(params.query_vector, 'ocr_text_vector') + 1.0 : 0;
return llm_score * 2 + ocr_score;
"""

class ImageSearchSystem:
    def __init__(
        self,
        elastic_host: str = "http://localhost:9200",
        index_name: str = "images",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.es = Elasticsearch(elastic_host)
        self.index_name = index_name
        # Initialize the embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        self._create_index_if_not_exists()

    def _create_index_if_not_exists(self):
        """Create the Elasticsearch index with appropriate mappings if it doesn't exist."""
        if not self.es.indices.exists(index=self.index_name):
            mappings = {
                "properties": {
                    "id": {"type": "keyword"},
                    "image_path": {"type": "keyword"},
                    "llm_description": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "llm_description_vector": {  # Dense vector field at top level
                        "type": "dense_vector",
                        "dims": 384,
                        "similarity": "cosine",
                        "index": True
                    },
                    "ocr_text": {
                        "type": "text",
                        "analyzer": "english"
                    },
                    "ocr_text_vector": {  # Another dense vector field at top level
                        "type": "dense_vector",
                        "dims": 384,
                        "similarity": "cosine",
                        "index": True
                    },
                    "location": {"type": "geo_point"},
                    "address": {"type": "text"},
                    "city": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "state": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "zip": {"type": "keyword"},
                    "country": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "metadata": {
                        "type": "object",
                        "dynamic": True
                    },
                    "tags": {"type": "keyword"},
                    "timestamp": {"type": "date"}
                }
            }

            
            self.es.indices.create(
                index=self.index_name,
                mappings=mappings,
                settings={
                    "index": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1
                    }
                }
            )

    def _generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for the given text."""
        return self.embedding_model.encode(text).tolist()

    def ingest_image_metadata(
        self,
        image_path: str,
        llm_description: str,
        timestamp: datetime = None,
        location_data: Optional[Dict[str, Any]] = None,
        ocr_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        custom_id: Optional[str] = None
    ) -> str:
        """Ingest image metadata into Elasticsearch with vector embeddings."""
        doc_id = custom_id or str(uuid.uuid4())
        
        # Generate embeddings for description and OCR text
        description_embedding = self._generate_embeddings(llm_description)
        
        document = {
            "id": doc_id,
            "image_path": image_path,
            "llm_description": llm_description,
            "llm_description_vector": description_embedding,
            "timestamp": timestamp,
            "tags": tags or []
        }

        if ocr_text:
            ocr_embedding = self._generate_embeddings(ocr_text)
            document["ocr_text"] = ocr_text
            document["ocr_text_vector"] = ocr_embedding

        if location_data:
            if 'latitude' in location_data and 'longitude' in location_data:
                document["location"] = {
                    "lat": location_data["latitude"],
                    "lon": location_data["longitude"]
                }
            
            for field in ['address', 'city', 'state', 'zip', 'country']:
                if field in location_data:
                    document[field] = location_data[field]

        if additional_metadata:
            document["metadata"] = additional_metadata

        try:
            self.es.index(index=self.index_name, id=doc_id, document=document)
            return doc_id
        except Exception as e:
            print(f"Error ingesting document: {e}")
            raise

    def search_images(
        self,
        query: Optional[str] = None,
        location_filters: Optional[Dict[str, Any]] = None,
        temporal_filters: Optional[Dict[str, Any]] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        search_type: Union[
            Literal['hybrid'],
            Literal['semantic'],
            Literal['keyword'],
            ] = "keyword",
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for images using semantic similarity and/or keyword matching.
        
        Args:
            query: Natural language query
            location_filters: Geographical and location-based filters
            metadata_filters: Additional filters for metadata fields
            search_type: Type of search to perform:
                - 'hybrid': Combine semantic and keyword search
                - 'semantic': Pure semantic similarity search
                - 'keyword': Traditional keyword-based search
            size: Number of results to return
        """
        must_conditions = []
        filter_conditions = []

        if query:
            if search_type in ['semantic', 'hybrid']:
                # Generate query embeddings
                query_embedding = self._generate_embeddings(query)
                
                semantic_query = {
                    "script_score": {
                        "min_score": 1.00001,
                        "query": {"match_all": {}},
                        "script": {
                            "source": script_source,
                            "params": {"query_vector": query_embedding}
                        }
                    }
                }
                
                if search_type == 'hybrid':
                    must_conditions.append({
                        "bool": {
                            "should": [
                                semantic_query,
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": [
                                            "llm_description^2",
                                            "ocr_text",
                                            "address",
                                            "city",
                                            "state",
                                            "country"
                                        ],
                                        "type": "best_fields",
                                        "fuzziness": "AUTO",
                                        "boost": 2,
                                    }
                                }
                            ]
                        }
                    })
                else:
                    must_conditions.append(semantic_query)
                    pass
            else:
                # Keyword-only search
                must_conditions.append({
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "llm_description^2",
                            "ocr_text",
                            "address",
                            "city",
                            "state",
                            "country"
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                })
        else:
            must_conditions.append({"match_all": {}})

        # Add location and metadata filters
        if location_filters:
            filter_conditions.append({
                "geo_distance": {
                    "distance": f"{location_filters['radius']}m",
                    "location": {
                        "lat": location_filters['lat'],
                        "lon": location_filters['long']
                    }
                }
            })

            for field in ['city', 'state', 'zip', 'country']:
                if field in location_filters:
                    filter_conditions.append({
                        "term": {f"{field}.keyword": location_filters[field]}
                    })

        if metadata_filters:
            for key, value in metadata_filters.items():
                if key == 'tags':
                    if isinstance(value, list):
                        filter_conditions.append({"terms": {"tags": value}})
                    else:
                        filter_conditions.append({"term": {"tags": value}})
                else:
                    filter_conditions.append({"term": {key: value}})

        if temporal_filters:
            filter_conditions.append({
                "range": {
                    "timestamp": {
                        "gte": temporal_filters['start'],
                        "lte": temporal_filters['end']
                    }
                }
            })
            print(filter_conditions)

        # Combine all query components
        search_body = {
             "_source": {
                "exclude": [ "*_vector" ]
            },
            "query": {
                "bool": {
                    "must": must_conditions,
                    "filter": filter_conditions
                }
            },
            "size": size
        }
        # print('search_body', json.dumps(search_body, indent=4))
        try:
            response = self.es.search(
                index=self.index_name,
                body=search_body,
            )

            response_hits = response.get("hits", {}).get("hits", [])
            
            return [{
                "score": hit["_score"],
                "timestamp": hit["_source"]["timestamp"],
                "id": hit["_source"]["id"],
                "image_path": f'/storage/{hit["_source"]["image_path"].split("/")[-1]}',
                "ocr_text": hit["_source"].get("ocr_text"),
                "description": hit["_source"]["llm_description"],
                "coords": hit["_source"].get("location"),
                "address": hit["_source"].get("address"),
                "city": hit["_source"].get("city"),
                "state": hit["_source"].get("state"),
                "zip": hit["_source"].get("zip"),
                "country": hit["_source"].get("country"),
                # "metadata": hit["_source"].get("metadata", {}),
                # "tags": hit["_source"].get("tags", []),
            } for hit in response_hits]
            
        except Exception as e:
            print(f"Error executing search: {e}")
            raise

    def get_image_sequence(self, timestamp: datetime, direction: Literal["before", "after"], limit: int = 10, inclusive: bool = False) -> List[Dict[str, Any]]:
        try:
            if direction == "before":
                sort_order = "desc"
                key = "lte" if inclusive else "lt"
                range_query = {
                    key: timestamp,
                    "format": "strict_date_optional_time"
                }
            else:
                sort_order = "asc"
                key = "gte" if inclusive else "gt"
                range_query = {
                    key: timestamp,
                    "format": "strict_date_optional_time"
                }


            search_body = {
                "query": {
                    "range": {
                        "timestamp": range_query
                    }
                },
                "sort": {
                    "timestamp": {
                        "order": sort_order
                    }
                },
                "size": limit
            }

            print(search_body)

            response = self.es.search(
                index=self.index_name,
                body=search_body
            )

            response_hits = response.get("hits", {}).get("hits", [])
            
            results = [{
                "id": hit["_source"]["id"],
                "timestamp": hit["_source"]["timestamp"],
                "image_path": f'/storage/{hit["_source"]["image_path"].split("/")[-1]}',
                "ocr_text": hit["_source"].get("ocr_text"),
                "description": hit["_source"]["llm_description"],
                "coords": hit["_source"].get("location"),
                "address": hit["_source"].get("address"),
                "city": hit["_source"].get("city"),
                "state": hit["_source"].get("state"),
                "zip": hit["_source"].get("zip"),
                "country": hit["_source"].get("country"),
                "timestamp": hit["_source"]["timestamp"]
            } for hit in response_hits]
            
            # ensure order is always oldest to newest
            if direction == "before":
                results.reverse()

            return results
        except Exception:
            traceback.print_exc("Error retrieving image sequence")
            return []
        
    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by its ID."""
        try:
            result = self.es.get(index=self.index_name, id=doc_id)
            return result["_source"]
        except Exception as e:
            print(f"Error retrieving document: {e}")
            return None



if __name__ == "__main__":    
    # Example hybrid search with location filter
    elastic = ImageSearchSystem()

    hybrid_results = elastic.search_images(
        query="shoes",
        search_type="hybrid"
    )

    print(hybrid_results)