from typing import Literal
from pydantic import BaseModel, Field

Status = Literal["running", "success", "error"]

class RunCreate(BaseModel):
    agent_name: str = Field(min_length=1, max_length=120)
    user_input: str = Field(min_length=1, max_length=5000)
    prompt_version: str = Field(default="v1", max_length=80)
    status: Status = "running"
    duration_ms: int = Field(default=0, ge=0)
    response_summary: str = Field(default="", max_length=5000)
    error_message: str = Field(default="", max_length=5000)

class RunUpdate(BaseModel):
    status: Status
    duration_ms: int = Field(default=0, ge=0)
    response_summary: str = Field(default="", max_length=5000)
    error_message: str = Field(default="", max_length=5000)

class ToolCallCreate(BaseModel):
    tool_name: str = Field(min_length=1, max_length=120)
    input_summary: str = Field(default="", max_length=5000)
    output_summary: str = Field(default="", max_length=5000)
    status: Literal["success", "error"] = "success"
    duration_ms: int = Field(default=0, ge=0)
    error_message: str = Field(default="", max_length=5000)
