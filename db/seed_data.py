"""Seed script for ChromaDB collections.

Run this script to populate the vector database with triage protocols,
routing rules, and preliminary orders.

Usage:
    python -m db.seed_data
"""

from db.vector_store import VectorStore


# =============================================================================
# Triage Protocols (Manchester Triage criteria)
# =============================================================================

TRIAGE_PROTOCOLS = [
    # RED - Emergency
    "RED: Chest pain with diaphoresis (sweating), radiating to arm or jaw, shortness of breath - possible Acute Coronary Syndrome (ACS). Immediate cardiac evaluation required.",
    "RED: Severe respiratory distress, SpO2 < 92%, cyanosis, use of accessory muscles - respiratory emergency. Immediate intervention required.",
    "RED: Uncontrolled hemorrhage, signs of shock (tachycardia, hypotension, pallor) - hemorrhagic emergency. Immediate blood product preparation.",
    "RED: Altered consciousness, GCS < 12, sudden onset confusion - neurological emergency. Immediate CT and neuro evaluation.",
    "RED: Severe allergic reaction, anaphylaxis, airway swelling, hypotension - anaphylactic emergency. Immediate epinephrine.",
    "RED: Severe abdominal pain with rigid abdomen, signs of peritonitis - surgical emergency. Immediate surgical consultation.",
    "RED: Seizure activity, status epilepticus - neurological emergency. Immediate anticonvulsant therapy.",
    "RED: Severe trauma, multiple injuries, mechanism suggests high energy transfer - trauma activation.",

    # YELLOW - Urgent
    "YELLOW: Moderate to severe abdominal pain (7-8/10) with fever, localized tenderness - possible appendicitis or cholecystitis. Urgent surgical evaluation.",
    "YELLOW: Chest pain without classic cardiac features, stable vitals - requires ECG and troponin workup within 30 minutes.",
    "YELLOW: Moderate respiratory symptoms, SpO2 92-95%, mild distress - urgent respiratory assessment.",
    "YELLOW: Possible fracture, deformity, moderate pain, neurovascularly intact - urgent orthopedic evaluation.",
    "YELLOW: High fever (>39°C/102°F) with focal symptoms - possible serious infection. Urgent evaluation.",
    "YELLOW: Severe headache, sudden onset, worst headache of life - possible SAH. Urgent CT required.",
    "YELLOW: Moderate allergic reaction without airway compromise - urgent monitoring and treatment.",
    "YELLOW: Abdominal pain in pregnancy - urgent OB evaluation required.",

    # GREEN - Standard
    "GREEN: Minor musculoskeletal injury, ambulatory, mild pain (1-4/10) - standard evaluation.",
    "GREEN: Low-grade fever (<38.5°C/101°F) with mild symptoms - standard evaluation.",
    "GREEN: Minor laceration, bleeding controlled, no neurovascular compromise - standard wound care.",
    "GREEN: Mild respiratory symptoms, SpO2 > 95%, no distress - standard evaluation.",
    "GREEN: Chronic pain exacerbation, stable, no new features - standard evaluation.",
    "GREEN: Minor urinary symptoms, no fever, no flank pain - standard evaluation.",
    "GREEN: Mild gastrointestinal symptoms, tolerating fluids - standard evaluation.",

    # BLUE - Low Priority
    "BLUE: Minor cuts or abrasions, no active bleeding, superficial - low priority wound care.",
    "BLUE: Common cold symptoms, mild congestion, no fever - low priority.",
    "BLUE: Medication refill request, stable chronic condition - low priority.",
    "BLUE: Minor rash, no systemic symptoms - low priority dermatology.",
    "BLUE: Chronic stable condition, routine follow-up concerns - low priority.",
    "BLUE: Minor insect bite, no allergic symptoms - low priority.",
]


# =============================================================================
# Routing Rules (Symptom to Department mappings)
# =============================================================================

ROUTING_RULES = [
    # Cardiology
    "Chest pain with cardiac features (radiation, diaphoresis, dyspnea) → Cardiology",
    "Arrhythmia, palpitations with hemodynamic instability → Cardiology",
    "Known cardiac history with new symptoms → Cardiology",
    "Syncope with cardiac risk factors → Cardiology",

    # Orthopedics
    "Fractures, suspected fractures, bone deformity → Orthopedics",
    "Dislocations, joint injuries → Orthopedics",
    "Severe musculoskeletal trauma → Orthopedics",
    "Back pain with neurological symptoms → Orthopedics/Neurosurgery",

    # General Surgery
    "Acute abdominal pain with surgical indicators (rigidity, guarding) → General Surgery",
    "Appendicitis symptoms (RLQ pain, fever, migration) → General Surgery",
    "Cholecystitis symptoms (RUQ pain, murphy sign) → General Surgery",
    "Bowel obstruction symptoms → General Surgery",
    "Hernia with incarceration signs → General Surgery",

    # Neurology
    "Stroke symptoms (FAST: Face, Arm, Speech, Time) → Neurology/Stroke Team",
    "Seizures, status epilepticus → Neurology",
    "Severe headache, worst of life → Neurology",
    "Altered mental status, neurological deficits → Neurology",

    # Pediatrics
    "Pediatric patient (age < 18 years) → Pediatrics",
    "Pediatric fever, respiratory symptoms → Pediatrics",
    "Pediatric injury → Pediatrics/Pediatric Surgery",

    # Obstetrics
    "Pregnancy-related symptoms → Obstetrics",
    "Abdominal pain in pregnant patient → Obstetrics",
    "Vaginal bleeding in pregnancy → Obstetrics",

    # General Practice / Internal Medicine
    "General illness, viral symptoms → General Practice",
    "Fever without focal source → General Practice/Internal Medicine",
    "Urinary tract symptoms → General Practice/Urology",
    "Mild respiratory infection → General Practice",
    "Unspecified complaints, needs evaluation → General Practice",

    # Emergency Medicine (critical)
    "Unstable patient, multiple system involvement → Emergency Medicine",
    "Trauma activation criteria met → Emergency Medicine/Trauma",
    "Resuscitation required → Emergency Medicine",
]


# =============================================================================
# Preliminary Orders (Standard orders by condition)
# =============================================================================

PRELIMINARY_ORDERS = [
    # Cardiac
    "Cardiac chest pain: 12-lead ECG within 10 minutes, Troponin I and T, CBC, BMP, continuous cardiac monitoring, IV access, aspirin 325mg (if no contraindication)",
    "Arrhythmia: 12-lead ECG, continuous monitoring, electrolytes (K, Mg), consider adenosine or cardioversion based on rhythm",
    "Syncope: ECG, orthostatic vitals, CBC, BMP, glucose, consider telemetry",

    # Respiratory
    "Respiratory distress: Pulse oximetry continuous, supplemental O2 to maintain SpO2 > 94%, chest X-ray, ABG if SpO2 < 92%, respiratory therapy consult",
    "Asthma exacerbation: Peak flow, albuterol nebulizer, ipratropium, systemic steroids if severe",
    "Pneumonia suspected: Chest X-ray, CBC, BMP, blood cultures if febrile, procalcitonin",

    # Abdominal
    "Abdominal pain: CBC, CMP, lipase, urinalysis, pregnancy test (females of childbearing age), consider CT abdomen/pelvis",
    "Appendicitis suspected: CBC, CRP, urinalysis, CT abdomen with contrast, surgical consult, NPO",
    "Cholecystitis suspected: RUQ ultrasound, CBC, LFTs, lipase, surgical consult, NPO",
    "GI bleeding: Type and screen, CBC, BMP, coagulation studies, 2 large bore IVs, GI consult",

    # Neurological
    "Stroke symptoms: Stat CT head without contrast, glucose, coagulation studies, stroke team activation, consider tPA if within window",
    "Seizure: Glucose, electrolytes, anticonvulsant levels if applicable, consider CT head, EEG if status epilepticus",
    "Severe headache: CT head without contrast, consider lumbar puncture if CT negative and SAH suspected",

    # Trauma/Orthopedic
    "Trauma: X-ray affected areas, tetanus prophylaxis if indicated, wound care supplies, pain management",
    "Fracture suspected: X-ray of affected area, splinting, ice, elevation, pain management, neurovascular checks",
    "Laceration: Wound irrigation supplies, local anesthetic, suture kit, tetanus status check",

    # Allergic
    "Allergic reaction: Diphenhydramine, famotidine, consider steroids, continuous monitoring",
    "Anaphylaxis: Epinephrine IM, IV fluids wide open, airway equipment at bedside, continuous monitoring",

    # Infection
    "Sepsis suspected: Blood cultures x2, lactate, CBC, CMP, urinalysis, chest X-ray, IV fluids 30ml/kg, broad-spectrum antibiotics within 1 hour",
    "UTI: Urinalysis, urine culture, consider CBC if systemic symptoms",

    # General
    "Fever workup: CBC, CMP, urinalysis, blood cultures if high risk, chest X-ray if respiratory symptoms",
    "Pain management: Assess pain scale, consider acetaminophen, NSAIDs, or opioids based on severity and contraindications",
]


def seed_database(clear_existing: bool = True) -> dict:
    """Seed the ChromaDB collections with protocol data.

    Args:
        clear_existing: Whether to clear existing data before seeding

    Returns:
        Dictionary with counts of seeded documents
    """
    print("Initializing vector store...")
    store = VectorStore()

    if clear_existing:
        print("Clearing existing data...")
        store.clear_all()

    # Seed triage protocols
    print("Seeding triage protocols...")
    for i, protocol in enumerate(TRIAGE_PROTOCOLS):
        store.add_triage_protocol(protocol, f"protocol_{i}")

    # Seed routing rules
    print("Seeding routing rules...")
    for i, rule in enumerate(ROUTING_RULES):
        store.add_routing_rule(rule, f"rule_{i}")

    # Seed preliminary orders
    print("Seeding preliminary orders...")
    for i, order in enumerate(PRELIMINARY_ORDERS):
        store.add_preliminary_order(order, f"order_{i}")

    stats = store.get_stats()
    print(f"\nSeeding complete!")
    print(f"  - Triage protocols: {stats['triage_protocols']}")
    print(f"  - Routing rules: {stats['routing_rules']}")
    print(f"  - Preliminary orders: {stats['preliminary_orders']}")

    return stats


if __name__ == "__main__":
    seed_database()
