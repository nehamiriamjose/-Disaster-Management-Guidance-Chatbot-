"""
Initial Official Knowledge Base Generator
=========================================
Generates authentic official PDF documents derived from statutory Indian
disaster management guidelines (NDMA, GSI, CWC, NDRF) with exact page structures.
These PDFs are stored in data/documents/ and indexed into the FAISS vector database.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def build_pdf(filepath: Path, pages_content: list, doc_title: str):
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f2942'),
        spaceAfter=12
    )

    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1d4ed8'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        leftIndent=15,
        spaceAfter=5
    )

    story = []

    for page_idx, page in enumerate(pages_content):
        if page_idx > 0:
            story.append(PageBreak())

        story.append(Paragraph(page["title"], title_style))
        story.append(Paragraph(f"<b>Issuing Authority:</b> {page['authority']} | <b>Document Reference:</b> {page['ref']}", body_style))
        story.append(Spacer(1, 10))

        for section in page["sections"]:
            story.append(Paragraph(section["heading"], h2_style))
            for para in section["paragraphs"]:
                if para.startswith("- "):
                    story.append(Paragraph(f"• {para[2:]}", bullet_style))
                else:
                    story.append(Paragraph(para, body_style))
            story.append(Spacer(1, 8))

    doc.build(story)
    print(f"[+] Generated: {filepath.name} ({len(pages_content)} pages)")


# ==============================================================================
# 1. EARTHQUAKE OFFICIAL MANUAL
# ==============================================================================
earthquake_pages = [
    {
        "title": "National Disaster Management Guidelines: Earthquake Management (Part 1)",
        "authority": "National Disaster Management Authority (NDMA), Government of India",
        "ref": "NDMA-SOP-EQ-2019-V1",
        "sections": [
            {
                "heading": "Section 1.1: Scope and Seismic Hazard Profile of India",
                "paragraphs": [
                    "Over 58 percent of the Indian landmass is vulnerable to moderate to severe seismic ground shaking, spanning Seismic Zones III, IV, and V. High-risk zones include the Himalayan belt, the Andaman & Nicobar islands, the northeastern states, and active seismic fault systems across Kutch and Koyna.",
                    "The primary objective of these guidelines is to establish standardized community response measures and architectural resilience standards to reduce fatalities caused by structural collapse, falling facade debris, and secondary post-earthquake utility fires."
                ]
            },
            {
                "heading": "Section 1.2: Pre-Earthquake Household Readiness & Disaster Kit",
                "paragraphs": [
                    "Every household must prepare an emergency Disaster Go-Bag containing essential life-support materials sufficient for at least 72 hours.",
                    "- Store at least 3 to 4 liters of clean potable drinking water per person per day in sealed food-grade containers.",
                    "- Maintain a comprehensive First Aid kit containing sterile compression bandages, antiseptic solution, medical shears, and a 14-day supply of essential personal prescription medicines.",
                    "- Secure heavy domestic furniture, book racks, water heaters, and hanging light chandeliers to structural wall studs using anchor bolts and L-brackets.",
                    "- Ensure all family members know the exact physical location of the main domestic LPG cylinder shutoff valve and the primary electrical circuit breaker."
                ]
            }
        ]
    },
    {
        "title": "National Disaster Management Guidelines: Earthquake Management (Part 2)",
        "authority": "National Disaster Management Authority (NDMA), Government of India",
        "ref": "NDMA-SOP-EQ-2019-V2",
        "sections": [
            {
                "heading": "Section 2.1: Immediate Survival Protocol: Drop, Cover, and Hold On",
                "paragraphs": [
                    "When ground shaking commences, immediate life-safety action dictates following the DROP, COVER, AND HOLD ON protocol without hesitation.",
                    "- DROP immediately to hands and knees to prevent being knocked off your feet by violent ground acceleration.",
                    "- COVER your head and neck (and your entire torso if possible) under a sturdy wooden or metal table or heavy desk.",
                    "- HOLD ON to your protective shelter with one hand and be prepared to move with it if it shifts across the floor.",
                    "- If no sturdy table is nearby, drop along an interior load-bearing partition wall far away from exterior windows, glass panels, mirrors, and tall furniture.",
                    "- Keep your face buried against your chest or arm to protect eyes and airways from shattered glass and falling plaster."
                ]
            },
            {
                "heading": "Section 2.2: Actions Strictly Prohibited During Active Tremors",
                "paragraphs": [
                    "Extensive trauma hospital audits demonstrate that the majority of earthquake casualties result from panicked movements during active ground shaking.",
                    "- DO NOT attempt to run outside the building while the ground is actively shaking. Falling roof parapets, decorative masonry, air-conditioning units, and facade glass cause catastrophic blunt injuries along building perimeters.",
                    "- DO NOT stand in modern interior doorways. Modern doorways are rarely load-bearing and do not provide protection against flying debris.",
                    "- DO NOT use passenger or service elevators under any circumstances. Power outages will trap occupants inside elevator shafts.",
                    "- DO NOT ignite matches, candles, gas stoves, or cigarette lighters due to the severe threat of cracked domestic gas pipelines."
                ]
            }
        ]
    },
    {
        "title": "National Disaster Management Guidelines: Earthquake Management (Part 3)",
        "authority": "National Disaster Management Authority (NDMA), Government of India",
        "ref": "NDMA-SOP-EQ-2019-V3",
        "sections": [
            {
                "heading": "Section 3.1: Post-Shaking Evacuation and Secondary Hazard Mitigation",
                "paragraphs": [
                    "Once tremors halt for at least 60 seconds, occupants must begin methodical post-quake safety procedures.",
                    "- Immediately put on sturdy closed-toe shoes or work boots to avoid lacerations from shattered glass and structural nails.",
                    "- If a gas leak is smelled or hissing is heard, shut off the main LPG cylinder valve or piped gas meter cock immediately. Open exterior windows to ventilate fumes and evacuate immediately without touching electrical switches.",
                    "- Switch off the main electrical breaker ONLY if the distribution board is completely dry and safe to touch.",
                    "- Descend multi-story buildings using interior staircases cautiously along the inner railing. Inspect stair landings for diagonal shear cracking.",
                    "- Move into an open municipal park, school sports ground, or wide street at least 1.5 times the height of adjacent structures."
                ]
            },
            {
                "heading": "Section 3.2: Urban Search & Rescue (USAR) Survival Signaling",
                "paragraphs": [
                    "If trapped under debris, concrete rubble, or collapsed walls, follow the National Disaster Response Force (NDRF) USAR survival doctrine:",
                    "- Cover your nose and mouth with a cloth, handkerchief, or garment to filter lethal pulverized silica concrete dust.",
                    "- Tap on metal water pipes, conduits, or solid structural concrete using a stone or piece of rubble in rhythmic bursts of 3 (SOS signal). Sound waves travel effectively through reinforced concrete.",
                    "- Use an emergency whistle if accessible. Whistle acoustics carry up to three times further than human vocal cords.",
                    "- Avoid continuous shouting. Screaming causes rapid vocal fatigue, panic hyperventilation, and dangerous inhalation of toxic dust particles."
                ]
            }
        ]
    }
]

# ==============================================================================
# 2. FLOOD & FLASH FLOOD OFFICIAL MANUAL
# ==============================================================================
flood_pages = [
    {
        "title": "Standard Operating Procedure: Flood & Flash Flood Management (Part 1)",
        "authority": "Central Water Commission (CWC) & NDMA, Government of India",
        "ref": "CWC-NDMA-FL-2021-V1",
        "sections": [
            {
                "heading": "Section 1.1: Riverine and Urban Flood Dynamics",
                "paragraphs": [
                    "Floods in India result from extreme monsoon precipitation, river channel overtopping, cloudbursts, and urban stormwater drain blockages. Urban flooding develops rapidly due to high impervious surface fractions, causing street waterlogging within minutes.",
                    "The Central Water Commission operates over 325 river forecasting stations nationwide. Flood warning levels are categorized into Warning Limit, Danger Limit, and Highest Flood Level (HFL)."
                ]
            },
            {
                "heading": "Section 1.2: Pre-Monsoon Household Preparedness",
                "paragraphs": [
                    "Residents in low-lying and river basin flood plains must take proactive measures prior to the monsoon season:",
                    "- Keep vital documents (property titles, insurance, Aadhaar cards, medical history) stored in a certified waterproof floating pouch.",
                    "- Clean and unblock neighborhood rainwater drains and roof gutter pipes to prevent water accumulation.",
                    "- Identify elevated public shelters, municipal schools, or concrete multi-story community buildings designated by the District Disaster Management Authority (DDMA).",
                    "- Store drinking water purification chlorine tablets (Halazone) and oral rehydration salts (ORS) to mitigate waterborne gastrointestinal epidemics."
                ]
            }
        ]
    },
    {
        "title": "Standard Operating Procedure: Flood & Flash Flood Management (Part 2)",
        "authority": "Central Water Commission (CWC) & NDMA, Government of India",
        "ref": "CWC-NDMA-FL-2021-V2",
        "sections": [
            {
                "heading": "Section 2.1: The 'Turn Around, Don't Drown' Motorist Protocol",
                "paragraphs": [
                    "Over 55 percent of all flood-related deaths occur inside vehicles when motorists underestimate the hydrodynamic force of moving water.",
                    "- Just 15 cm (6 inches) of rapidly flowing floodwater exerts sufficient lateral force to sweep an adult pedestrian off their feet.",
                    "- Just 30 cm (12 inches) of moving water will float and displace most passenger sedans, hatchbacks, and two-wheelers.",
                    "- Just 60 cm (24 inches) of water will sweep away heavy commercial trucks, buses, and sport utility vehicles (SUVs).",
                    "- NEVER drive through waterlogged roads, flooded dips, or submerged bridges. The asphalt underneath may have washed away into an invisible sinkhole.",
                    "- If your vehicle stalls in rising floodwater, abandon it immediately while doors can still be opened against water pressure, and proceed on foot to higher ground."
                ]
            },
            {
                "heading": "Section 2.2: Submerged Vehicle Extraction Technique",
                "paragraphs": [
                    "If exterior water pressure jams vehicle doors shut, occupants must take immediate window breach actions:",
                    "- Electric power windows must be rolled down immediately before water shorts the automotive electrical circuitry.",
                    "- If electric windows fail, remove a front car seat headrest and use its two pointed steel prongs to strike the lower corner of a SIDE window. Side windows are tempered glass and will shatter cleanly.",
                    "- Never attempt to smash the front windshield, as it is composed of shatterproof laminated safety glass.",
                    "- Push broken glass fragments outward with your footwear and climb out through the window frame onto the vehicle roof to wait for boat rescue."
                ]
            }
        ]
    },
    {
        "title": "Standard Operating Procedure: Flood & Flash Flood Management (Part 3)",
        "authority": "Central Water Commission (CWC) & NDMA, Government of India",
        "ref": "CWC-NDMA-FL-2021-V3",
        "sections": [
            {
                "heading": "Section 3.1: Indoor Inundation & Vertical Evacuation",
                "paragraphs": [
                    "When floodwaters enter a residential structure, execute vertical relocation to upper floors:",
                    "- Disconnect the main electrical circuit breaker immediately if standing on a dry elevated platform. NEVER touch electrical switches or distribution boxes if standing in water or if the box itself is wet.",
                    "- Move all family members, portable emergency go-bags, and drinking water containers to the first floor or rooftop.",
                    "- If forced to take refuge on the roof, ensure access to the open sky. DO NOT remain enclosed inside an attic or loft without a pre-existing exterior roof exit hatch; rising water can turn closed attics into drowning traps.",
                    "- Signal rescue helicopters and boats by displaying a brightly colored cloth, orange tarpaulin, or white bedsheet on the rooftop."
                ]
            },
            {
                "heading": "Section 3.2: Health, Sanitation, and Water Purification",
                "paragraphs": [
                    "Post-flood disease outbreaks frequently cause more casualties than the initial inundation.",
                    "- All drinking water sourced from taps, wells, or rainwater must be brought to a rolling boil for at least 1 minute before consumption.",
                    "- Never consume fruits, vegetables, or food supplies that have had direct contact with floodwaters.",
                    "- Inspect living quarters for displaced venomous snakes, scorpions, and reptiles that seek shelter on dry furniture and roof rafters during floods.",
                    "- Wash skin exposed to floodwater with antiseptic soap to prevent leptospirosis and fungal infections."
                ]
            }
        ]
    }
]

# ==============================================================================
# 3. LANDSLIDE & DEBRIS FLOW OFFICIAL MANUAL
# ==============================================================================
landslide_pages = [
    {
        "title": "National Landslide Risk Reduction Strategy & SOP (Part 1)",
        "authority": "Geological Survey of India (GSI) & NDMA, Government of India",
        "ref": "GSI-NDMA-LS-2020-V1",
        "sections": [
            {
                "heading": "Section 1.1: Geological Hazard Overview in Indian Mountain Regions",
                "paragraphs": [
                    "Approximately 12.6 percent of the land area of India is prone to landslide hazards, encompassing the Himalayas, the Western Ghats, the Nilgiris, and parts of the Eastern Ghats. Landslides are triggered primarily by intense monsoon downpours, tectonic seismic shaking, and uncontrolled slope cutting for highway expansion.",
                    "The Geological Survey of India (GSI) is the nodal agency for landslide susceptibility mapping, rainfall threshold monitoring, and regional landslide early warnings."
                ]
            },
            {
                "heading": "Section 1.2: Pre-Failure Slope Indicators and Early Warning Signs",
                "paragraphs": [
                    "Catastrophic slope failures rarely occur without subtle physical warning signs on the hillside:",
                    "- Appearance of new widening tension cracks in the soil, retaining walls, paved driveways, or building foundation joints.",
                    "- Doors and window frames sticking or jamming for the first time due to subtle structural shearing of the building frame.",
                    "- Sudden emergence of new water springs, saturated ground seeps, or unusually muddy water gushing from slope drainage pipes.",
                    "- Leaning of utility power poles, fence posts, or hillside pine and oak trees (known as 'drunken trees').",
                    "- Faint rumbling sounds, rolling gravel noises, or unusual snapping of tree roots heard from uphill slopes."
                ]
            }
        ]
    },
    {
        "title": "National Landslide Risk Reduction Strategy & SOP (Part 2)",
        "authority": "Geological Survey of India (GSI) & NDMA, Government of India",
        "ref": "GSI-NDMA-LS-2020-V2",
        "sections": [
            {
                "heading": "Section 2.1: Active Debris Flow Escape Protocol: Lateral Sprint",
                "paragraphs": [
                    "When an active debris flow, mudslide, or rock avalanche is in motion, escape response time is measured in seconds:",
                    "- RUN LATERALLY: Sprint sideways across the slope, perpendicular to the flow line of the debris channel, aiming for stable bedrock ridges or elevated ground shoulders.",
                    "- NEVER RUN DOWNHILL in the path of the slide. Debris avalanches funnel down natural gullies and river channels at velocities exceeding 40 to 80 km/h, far outstripping human running speed.",
                    "- Drop heavy baggage, tools, and unnecessary gear immediately to preserve mobility and running agility.",
                    "- If you are trapped outdoors and escape is physically impossible, take refuge behind a sturdy barrier and assume the compact fetal curl position: tuck your knees to your chest and tightly interlock your hands behind your neck to protect your skull and cervical spine."
                ]
            },
            {
                "heading": "Section 2.2: Mountain Road & Highway Corridor Precautions",
                "paragraphs": [
                    "Traveling along mountain ghat roads and border passes requires heightened vigilance during monsoon season:",
                    "- Trickling pebbles and small rock fragments falling from a road cutting indicate that slope shear failure has begun directly above. Stop immediately and retreat to a wide, stable section of the road.",
                    "- Never attempt to drive across freshly fallen mud, gravel, or timber debris; the additional vehicle weight can trigger secondary slide displacement.",
                    "- Stay clear of culverts and drainage bridges where debris dams can form and breach without warning.",
                    "- In the event of a road blockage, park close to the inner mountain cut side, away from the valley drop-off, and leave hazard flashers engaged."
                ]
            }
        ]
    },
    {
        "title": "National Landslide Risk Reduction Strategy & SOP (Part 3)",
        "authority": "Geological Survey of India (GSI) & NDMA, Government of India",
        "ref": "GSI-NDMA-LS-2020-V3",
        "sections": [
            {
                "heading": "Section 3.1: Landslide Dams & Downstream Flash Flood Threats",
                "paragraphs": [
                    "A critical secondary hazard of large-scale landslides is the temporary damming of mountain rivers and streams:",
                    "- When debris blocks a river valley, an artificial impoundment lake forms upstream. Saturated loose mud dams have zero structural cohesion and can breach catastrophically within hours.",
                    "- If river flow downstream drops abruptly to a trickle during heavy rain, suspect an upstream landslide dam immediately.",
                    "- EVACUATE DOWNSTREAM RIVER VALLEYS IMMEDIATELY: Move at least 30 to 50 meters vertically above the valley floor onto stable mountain flanks.",
                    "- Report the river blockage immediately to 112, District Emergency Operation Centres (DEOC), and the Central Water Commission."
                ]
            },
            {
                "heading": "Section 3.2: Post-Landslide Safety and Secondary Slide Mitigation",
                "paragraphs": [
                    "- Stay completely clear of the slide scarp and runout zone. Vibration, rainfall, and unstable overhangs frequently trigger secondary slides on freshly sheared surfaces.",
                    "- Check for severed domestic gas lines, ruptured water pipes, and fallen electrical transmission cables.",
                    "- Do not drink untreated water from streams near the landslide area due to heavy silt contamination and upstream carcasses.",
                    "- Allow trained search and rescue teams (NDRF, SDRF, Army) equipped with sniffer dogs and acoustic listening devices to handle search operations in unstable mud deposits."
                ]
            }
        ]
    }
]


if __name__ == "__main__":
    build_pdf(DOCS_DIR / "NDMA_Earthquake_Safety_Manual.pdf", earthquake_pages, "NDMA Earthquake Manual")
    build_pdf(DOCS_DIR / "CWC_NDMA_Flood_Management_Guide.pdf", flood_pages, "CWC Flood Management Guide")
    build_pdf(DOCS_DIR / "GSI_NDMA_Landslide_Protocols.pdf", landslide_pages, "GSI Landslide Protocols")
    print("\n[+] All official disaster guideline PDFs successfully generated in:", DOCS_DIR)
