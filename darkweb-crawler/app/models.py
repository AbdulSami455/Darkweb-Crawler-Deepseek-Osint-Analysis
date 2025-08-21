#!/usr/bin/env python3
"""
Pydantic models for structured data extraction from dark web content analysis.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CategoryType(str, Enum):
    """Enumeration of possible dark web site categories."""
    MARKETPLACE = "marketplace"
    VENDOR_SHOP = "vendor_shop"
    FORUM = "forum"
    LEAK_SITE = "leak_site"
    RANSOMWARE_BLOG = "ransomware_blog"
    CARDING = "carding"
    FRAUD_SERVICE = "fraud_service"
    MALWARE_SERVICE = "malware_service"
    HOSTING = "hosting"
    MIXING_LAUNDRY = "mixing_laundry"
    SEARCH_INDEX = "search_index"
    NEWS = "news"
    PHISHING = "phishing"
    SCAM = "scam"
    OTHER = "other"


class ContactMethod(BaseModel):
    """Model for contact method information."""
    type: str = Field(description="Type of contact method (e.g., Telegram, Email, Jabber, Tox)")
    value: str = Field(description="Contact identifier or address")
    description: Optional[str] = Field(default=None, description="Additional context about this contact method")


class CryptoWallet(BaseModel):
    """Model for cryptocurrency wallet information."""
    type: str = Field(description="Cryptocurrency type (e.g., BTC, ETH, XMR)")
    address: str = Field(description="Wallet address")
    network: Optional[str] = Field(default=None, description="Network or tag information")
    description: Optional[str] = Field(default=None, description="Additional context about this wallet")


class PGPKey(BaseModel):
    """Model for PGP key information."""
    fingerprint: str = Field(description="40-character hex fingerprint")
    key_block_present: bool = Field(description="Whether the full key block is present")
    description: Optional[str] = Field(default=None, description="Additional context about this PGP key")


class OnionLink(BaseModel):
    """Model for .onion link information."""
    url: str = Field(description="The .onion URL")
    is_v2: bool = Field(description="Whether this is a deprecated v2 onion address")
    description: Optional[str] = Field(default=None, description="Additional context about this link")


class ProductService(BaseModel):
    """Model for product or service information."""
    name: str = Field(description="Name of the product or service")
    price: Optional[str] = Field(default=None, description="Price information")
    currency: Optional[str] = Field(default=None, description="Currency used")
    description: Optional[str] = Field(default=None, description="Description of the product or service")


class KeyInformation(BaseModel):
    """Model for key information extracted from content."""
    names_aliases: List[str] = Field(default_factory=list, description="Names or aliases found")
    contact_methods: List[ContactMethod] = Field(default_factory=list, description="Contact methods found")
    crypto_wallets: List[CryptoWallet] = Field(default_factory=list, description="Cryptocurrency wallets found")
    pgp_keys: List[PGPKey] = Field(default_factory=list, description="PGP keys found")
    onion_links: List[OnionLink] = Field(default_factory=list, description="Onion links found")
    clearnet_urls: List[str] = Field(default_factory=list, description="Clearnet URLs found")
    products_services: List[ProductService] = Field(default_factory=list, description="Products or services listed")
    dates_timestamps: List[str] = Field(default_factory=list, description="Dates or timestamps found (ISO 8601)")
    target_industries: List[str] = Field(default_factory=list, description="Target industries mentioned")
    target_regions: List[str] = Field(default_factory=list, description="Target regions mentioned")
    affiliations: List[str] = Field(default_factory=list, description="Claims of affiliation or reputation")


class SecurityAssessment(BaseModel):
    """Model for security assessment information."""
    malware_indicators: List[str] = Field(default_factory=list, description="Indicators of malware")
    phishing_indicators: List[str] = Field(default_factory=list, description="Indicators of phishing")
    scam_indicators: List[str] = Field(default_factory=list, description="Indicators of scams")
    escrow_claims: List[str] = Field(default_factory=list, description="Escrow service claims")
    opsec_practices: List[str] = Field(default_factory=list, description="Operational security practices")
    external_links: List[str] = Field(default_factory=list, description="External links or downloads")
    le_impersonation_signs: List[str] = Field(default_factory=list, description="Signs of law enforcement impersonation")


class DarkWebAnalysis(BaseModel):
    """Main model for structured dark web content analysis."""
    content_summary: str = Field(description="What this page is about (plain, factual)")
    key_information: KeyInformation = Field(description="Extracted concrete details")
    security_assessment: SecurityAssessment = Field(description="Security assessment information")
    categories: List[CategoryType] = Field(description="Classification of page type")
    notable_elements: List[str] = Field(default_factory=list, description="Unusual or high-signal elements")
    recommendations: List[str] = Field(default_factory=list, description="Safety and handling guidance for analysts")
    source_reliability: int = Field(ge=1, le=5, description="Source reliability rating 1-5")
    source_reliability_explanation: str = Field(description="Brief explanation of reliability rating")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level 0-1")
    confidence_justification: str = Field(description="One-sentence justification for confidence level")
    limitations: List[str] = Field(default_factory=list, description="Limitations like truncation, language barriers, or low-quality OCR")
    detected_language: Optional[str] = Field(default=None, description="Detected language if non-English")
    english_summary: Optional[str] = Field(default=None, description="English summary if content is non-English")
