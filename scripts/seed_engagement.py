from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.engagements import Engagement


engagements = [

    Engagement(
        client_name="Example Manufacturing Co.",
        industry="Manufacturing",

        service_line="Data & AI",
        engagement_type="Digital Transformation",
        client_relationship="Strategic Client",
        relationship_context=(
            "The consulting team supported the organization "
            "as a strategic technology partner during a broader "
            "digital transformation initiative."
        ),
        relationship_duration="5 years",

        business_problem=(
            "The organization lacked real-time visibility into "
            "factory operations and supply-chain events, making "
            "it difficult for decision makers to identify "
            "disruptions and respond quickly."
        ),
        business_capabilities=(
            "Real-time analytics, supply-chain visibility, "
            "operational intelligence"
        ),

        solution=(
            "Implemented an event-driven streaming analytics "
            "platform that ingested operational events and "
            "provided low-latency dashboards for decision makers."
        ),
        technology_stack=(
            "AWS, Kafka, Python, real-time analytics"
        ),
        architecture_patterns=(
            "Event-driven architecture, streaming analytics, "
            "cloud-native architecture"
        ),

        outcome=(
            "Improved operational visibility and enabled faster "
            "responses to supply-chain disruptions."
        ),
        financial_impact="Reduced operational inefficiencies.",

        company_size="Large enterprise",
        project_scale=(
            "Enterprise-wide deployment across multiple "
            "manufacturing facilities"
        ),
        investment=None,

        case_narrative=(
            "A large manufacturing organization needed real-time "
            "visibility into factory and supply-chain activity. "
            "The consulting team implemented an event-driven "
            "streaming analytics architecture using AWS and Kafka. "
            "The platform processed operational events and provided "
            "low-latency dashboards for decision makers, improving "
            "operational visibility and enabling faster responses "
            "to supply-chain disruptions."
        ),

        source_url=None,
    ),


    # --------------------------------------------------
    # SPORTS
    # --------------------------------------------------

    Engagement(
        client_name="Example Sports Organization",
        industry="Sports",

        service_line="Data & AI",
        engagement_type="Customer Experience Transformation",
        client_relationship="Strategic Client",
        relationship_context=(
            "The consulting team partnered with the organization "
            "to modernize its digital fan experience."
        ),
        relationship_duration="3 years",

        business_problem=(
            "The organization lacked real-time insight into fan "
            "behavior across stadium, mobile, and digital channels."
        ),
        business_capabilities=(
            "Real-time fan analytics, personalization, "
            "customer engagement"
        ),

        solution=(
            "Built a real-time event processing platform that "
            "combined digital interactions, stadium events, and "
            "customer activity to provide live analytics and "
            "personalized fan experiences."
        ),
        technology_stack=(
            "AWS, Kafka, Python, streaming analytics, APIs"
        ),
        architecture_patterns=(
            "Event-driven architecture, real-time processing, "
            "cloud-native architecture"
        ),

        outcome=(
            "Enabled the organization to understand fan behavior "
            "in real time and deliver more personalized experiences."
        ),
        financial_impact=(
            "Increased digital engagement and opportunities "
            "for targeted revenue generation."
        ),

        company_size="Large enterprise",
        project_scale=(
            "Multi-channel platform supporting stadium and "
            "digital fan interactions"
        ),
        investment=None,

        case_narrative=(
            "A large sports organization wanted to understand "
            "fan behavior in real time across stadium, mobile, "
            "and digital channels. The consulting team built an "
            "event-driven streaming platform using AWS and Kafka "
            "to process fan interactions and provide real-time "
            "analytics. The architecture enabled personalized "
            "fan experiences and increased digital engagement."
        ),

        source_url=None,
    ),


    # --------------------------------------------------
    # RETAIL
    # --------------------------------------------------

    Engagement(
        client_name="Example Retail Corporation",
        industry="Retail",

        service_line="Customer Transformation",
        engagement_type="Digital Commerce",
        client_relationship="Technology Partner",
        relationship_context=(
            "The consulting team helped modernize the company's "
            "digital customer experience."
        ),
        relationship_duration="4 years",

        business_problem=(
            "The retailer had difficulty understanding customer "
            "behavior across online and physical channels."
        ),
        business_capabilities=(
            "Customer analytics, personalization, "
            "real-time recommendations"
        ),

        solution=(
            "Developed a unified customer analytics platform "
            "that processed behavioral events in real time "
            "and powered personalized recommendations."
        ),
        technology_stack=(
            "AWS, Python, APIs, machine learning"
        ),
        architecture_patterns=(
            "Event-driven architecture, cloud-native "
            "microservices, real-time analytics"
        ),

        outcome=(
            "Improved customer personalization and enabled "
            "faster responses to customer behavior."
        ),
        financial_impact=(
            "Improved conversion opportunities through "
            "personalized recommendations."
        ),

        company_size="Large enterprise",
        project_scale="Enterprise digital commerce platform",
        investment=None,

        case_narrative=(
            "A large retailer wanted to understand customer "
            "behavior across online and physical channels. "
            "The consulting team developed a real-time customer "
            "analytics platform using AWS and machine learning. "
            "Behavioral events were processed continuously to "
            "power personalized recommendations and improve "
            "digital customer experiences."
        ),

        source_url=None,
    ),


    # --------------------------------------------------
    # BANKING
    # --------------------------------------------------

    Engagement(
        client_name="Example Financial Institution",
        industry="Financial Services",

        service_line="Data & AI",
        engagement_type="Risk Transformation",
        client_relationship="Strategic Technology Partner",
        relationship_context=(
            "The consulting team supported the institution's "
            "modernization of its data and risk infrastructure."
        ),
        relationship_duration="6 years",

        business_problem=(
            "The organization relied on batch-based systems "
            "that delayed detection of suspicious transactions."
        ),
        business_capabilities=(
            "Real-time transaction monitoring, anomaly detection, "
            "risk analytics"
        ),

        solution=(
            "Implemented a real-time transaction monitoring "
            "platform capable of processing high-volume event "
            "streams and identifying anomalous behavior."
        ),
        technology_stack=(
            "AWS, Kafka, Python, machine learning"
        ),
        architecture_patterns=(
            "Event-driven architecture, streaming analytics, "
            "real-time anomaly detection"
        ),

        outcome=(
            "Reduced the time required to identify potentially "
            "suspicious transactions."
        ),
        financial_impact=(
            "Reduced operational risk and improved monitoring "
            "efficiency."
        ),

        company_size="Large financial institution",
        project_scale="High-volume enterprise transaction platform",
        investment=None,

        case_narrative=(
            "A large financial institution needed to replace "
            "batch-based transaction monitoring with a real-time "
            "architecture. The consulting team implemented an "
            "event-driven streaming platform using AWS and Kafka "
            "to process high-volume transaction events and detect "
            "anomalous behavior. The solution reduced detection "
            "latency and improved risk monitoring."
        ),

        source_url=None,
    ),


    # --------------------------------------------------
    # LOGISTICS
    # --------------------------------------------------

    Engagement(
        client_name="Example Logistics Company",
        industry="Transportation",

        service_line="Supply Chain",
        engagement_type="Operations Transformation",
        client_relationship="Technology Partner",
        relationship_context=(
            "The consulting team worked with the organization "
            "to improve supply-chain visibility."
        ),
        relationship_duration="4 years",

        business_problem=(
            "The organization lacked real-time visibility into "
            "shipments and transportation operations."
        ),
        business_capabilities=(
            "Supply-chain visibility, shipment tracking, "
            "operational analytics"
        ),

        solution=(
            "Built a real-time shipment tracking and analytics "
            "platform that processed events from vehicles, "
            "warehouses, and logistics systems."
        ),
        technology_stack=(
            "AWS, Kafka, Python, IoT"
        ),
        architecture_patterns=(
            "Event-driven architecture, streaming analytics, "
            "IoT architecture"
        ),

        outcome=(
            "Improved shipment visibility and enabled operations "
            "teams to identify disruptions earlier."
        ),
        financial_impact=(
            "Reduced operational delays and improved resource utilization."
        ),

        company_size="Large transportation company",
        project_scale="Multi-region logistics network",
        investment=None,

        case_narrative=(
            "A large logistics organization needed real-time "
            "visibility into shipments and transportation operations. "
            "The consulting team built an event-driven streaming "
            "platform using AWS, Kafka, Python, and IoT data. "
            "The system processed events from vehicles and warehouses "
            "to identify disruptions earlier and improve operational "
            "visibility."
        ),

        source_url=None,
    ),
]


with Session(engine) as session:
    session.add_all(engagements)
    session.commit()

    print(f"Created {len(engagements)} engagements.")

    for engagement in engagements:
        print(
            f"- {engagement.client_name} "
            f"({engagement.industry}) "
            f"{engagement.id}"
        )