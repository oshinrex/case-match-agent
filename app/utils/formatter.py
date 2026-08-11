def format_engagement_for_embedding(engagement) -> str:
    """
    Convert an Engagement into structured text for semantic embedding.
    """

    sections = [
        ("Industry", engagement.industry),
        ("Service Line", engagement.service_line),
        ("Engagement Type", engagement.engagement_type),
        ("Client Relationship", engagement.client_relationship),
        ("Relationship Context", engagement.relationship_context),
        ("Relationship Duration", engagement.relationship_duration),

        ("Business Problem", engagement.business_problem),
        ("Business Capabilities", engagement.business_capabilities),

        ("Solution", engagement.solution),
        ("Technology Stack", engagement.technology_stack),
        ("Architecture Patterns", engagement.architecture_patterns),

        ("Outcome", engagement.outcome),
        ("Financial Impact", engagement.financial_impact),

        ("Company Size", engagement.company_size),
        ("Project Scale", engagement.project_scale),
        ("Investment", engagement.investment),

        ("Case Narrative", engagement.case_narrative),
    ]

    return "\n".join(
        f"{label}: {value}"
        for label, value in sections
        if value is not None and value != ""
    )