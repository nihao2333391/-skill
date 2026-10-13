"""Deterministic parser, DOCX builder, and verifier for NEU proposals."""

from .parser import Block, InputContractError, ProposalDocument, Signature, parse_file, parse_text

__all__ = [
    "Block",
    "InputContractError",
    "ProposalDocument",
    "Signature",
    "parse_file",
    "parse_text",
]
