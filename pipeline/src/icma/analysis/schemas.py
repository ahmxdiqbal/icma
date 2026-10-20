"""Structured outputs requested from the model at each analysis stage.

These are also the training targets for specialised models, so field names and enums should change
only with a prompt version bump.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- stage A0: per-chain matn


class ChainMatn(Strict):
    chain_id: int
    relation: Literal["full_text", "partial_text", "reference_only", "not_found"] = Field(
        description="full_text: this route's own complete matn is quoted. partial_text: only some "
        "words are quoted (e.g. 'bi-ma'nahu, qala: ...'). reference_only: the collector only says "
        "the text is the same or similar, with no wording. not_found: no text for this route."
    )
    matn_ar: str = Field(
        description="Verbatim Arabic quoted for this route. Must be non-empty for full_text and "
        "partial_text, and empty for reference_only and not_found."
    )
    same_as_chain_id: int | None = Field(
        description="Chain whose wording this route is said to share, when the text says so."
    )
    reference_formula_ar: str = Field(
        description="The collector's formula, e.g. 'بمثله', 'نحوه', 'بإسناد يحيى ومعناه', or ''."
    )
    note_en: str


class ChainMatnSet(Strict):
    chains: list[ChainMatn]


# ---------------------------------------------------------------- stage A: matn inventory


class MatnElement(Strict):
    id: str = Field(description="Short stable id, E1, E2, ...")
    label_en: str
    description_en: str
    exemplar_ar: str


class ElementReading(Strict):
    element_id: str
    wording_ar: str = Field(description="The words this variant uses for the element.")
    wording_class: str = Field(
        description="Short code for the wording family, shared across variants that use the same "
        "wording (e.g. 'nafy_sana' vs 'taghrib_am'), so wording differences can be counted."
    )


class VariantReading(Strict):
    variant_id: str
    elements: list[ElementReading] = Field(description="Elements present, in textual order.")
    translation_en: str
    notes_en: str


class MatnInventory(Strict):
    elements: list[MatnElement]
    variants: list[VariantReading]


# ---------------------------------------------------------------- stage C: ICMA synthesis

Verdict = Literal["supported", "doubtful", "rejected", "undecidable"]


class NodeJudgement(Strict):
    node_key: str
    verdict: Verdict
    reasoning: str


class DiveJudgement(Strict):
    chain_id: int
    interpretation: Literal[
        "later_borrowing", "independent_transmission", "transmission_error", "undecidable"
    ]
    reasoning: str


class MatnCluster(Strict):
    label: str
    defining_features: str
    variant_ids: list[str]
    branch_node_keys: list[str] = Field(
        description="Transmitters whose branches carry this cluster (empty if none)."
    )


class CommonLink(Strict):
    node_key: str
    verdict: Verdict
    cluster_labels: list[str] = Field(description="Matn clusters this transmitter circulated.")
    reasoning: str


class Correlation(Strict):
    finding: Literal["strong", "partial", "none", "insufficient_data"]
    reasoning: str


class Reconstruction(Strict):
    node_key: str = Field(description="Transmitter whose wording is reconstructed.")
    text_ar: str
    translation_en: str
    uncertain_elements: list[str]


class Dating(Strict):
    earliest_reliable_node_key: str
    date_range_ah: str = Field(description="e.g. '90-110'")
    date_range_ce: str
    reasoning: str


class IcmaAnalysis(Strict):
    convergence_point: NodeJudgement = Field(
        description="Is the node where most chains converge a genuine common link?"
    )
    common_links: list[CommonLink] = Field(
        description="Every transmitter shown to have circulated a matn cluster; may be several."
    )
    partial_common_links: list[NodeJudgement]
    upper_isnad: str = Field(description="Assessment of the chains above the common link(s).")
    dives: list[DiveJudgement]
    matn_clusters: list[MatnCluster]
    correlation: Correlation
    reconstructions: list[Reconstruction]
    dating: Dating
    alternative_readings: list[str] = Field(
        description="How a Juynboll-style or a more sceptical reading would differ, and why."
    )
    open_questions: list[str]
    confidence: Literal["high", "medium", "low"]
