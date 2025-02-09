from typing import Dict, Any, List, Optional
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
import yaml
from pathlib import Path
from app.core.logging import logger

class APIDocumentationManager:
    def __init__(self, app: FastAPI, docs_dir: Path):
        self.app = app
        self.docs_dir = docs_dir
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def generate_openapi_spec(self) -> Dict[str, Any]:
        try:
            return get_openapi(
                title=self.app.title,
                version=self.app.version,
                openapi_version="3.0.2",
                description=self.app.description,
                routes=self.app.routes
            )
        except Exception as e:
            logger.error(f"Failed to generate OpenAPI spec: {str(e)}")
            raise

    def save_openapi_spec(self, format: str = "yaml") -> None:
        try:
            spec = self.generate_openapi_spec()
            file_path = self.docs_dir / f"openapi.{format}"
            
            with open(file_path, 'w') as f:
                if format == "yaml":
                    yaml.dump(spec, f, sort_keys=False)
                else:
                    import json
                    json.dump(spec, f, indent=2)
                    
            logger.info(f"Saved OpenAPI spec to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save OpenAPI spec: {str(e)}")
            raise

    def generate_markdown_docs(self) -> None:
        try:
            spec = self.generate_openapi_spec()
            md_content = self._convert_spec_to_markdown(spec)
            
            with open(self.docs_dir / "api.md", 'w') as f:
                f.write(md_content)
                
            logger.info("Generated Markdown API documentation")
        except Exception as e:
            logger.error(f"Failed to generate Markdown docs: {str(e)}")
            raise

    def _convert_spec_to_markdown(self, spec: Dict[str, Any]) -> str:
        md = [f"# {spec['info']['title']}\n"]
        md.append(f"Version: {spec['info']['version']}\n")
        
        if 'description' in spec['info']:
            md.append(f"{spec['info']['description']}\n")

        md.append("## Endpoints\n")
        
        for path, path_item in spec['paths'].items():
            for method, operation in path_item.items():
                md.append(f"### {method.upper()} {path}\n")
                
                if 'summary' in operation:
                    md.append(f"{operation['summary']}\n")
                    
                if 'description' in operation:
                    md.append(f"{operation['description']}\n")
                    
                if 'parameters' in operation:
                    md.append("#### Parameters\n")
                    for param in operation['parameters']:
                        md.append(f"- `{param['name']}` ({param['in']}): {param.get('description', '')}\n")
                
                if 'requestBody' in operation:
                    md.append("#### Request Body\n")
                    md.append("```json\n")
                    md.append(yaml.dump(operation['requestBody']['content']['application/json']['schema']))
                    md.append("```\n")
                
                if 'responses' in operation:
                    md.append("#### Responses\n")
                    for status, response in operation['responses'].items():
                        md.append(f"**{status}**: {response.get('description', '')}\n")
                
                md.append("\n---\n")

        return "\n".join(md) 